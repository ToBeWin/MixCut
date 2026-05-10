from __future__ import annotations

import asyncio
import pytest

from backend.harness.retry import RetryPolicy, retry_async
from backend.harness.circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError
from backend.harness.loop import LoopPolicy, MaxIterationsExceeded, run_agent_loop, LoopMode
from backend.harness.timeout import TimeoutPolicy, NodeTimeoutError, run_with_timeout
from backend.harness.cost_tracker import CostRecord, CostTracker, current_node
from backend.harness.context_trimmer import trim_agent_state, MAX_NODE_OUTPUTS_ENTRIES, MAX_CORRECTION_HISTORY
from backend.schemas.agent_state import AgentState
from backend.schemas.correction import CorrectionIntent
from backend.schemas.user_goal import UserGoal


class TestRetryPolicy:
    def test_delay_increases_exponentially(self):
        policy = RetryPolicy(base_delay_seconds=1.0, multiplier=2.0, max_delay_seconds=60.0, jitter_ratio=0.0)
        assert policy.delay_for_attempt(0) == 1.0
        assert policy.delay_for_attempt(1) == 2.0
        assert policy.delay_for_attempt(2) == 4.0
        assert policy.delay_for_attempt(3) == 8.0

    def test_delay_capped_at_max(self):
        policy = RetryPolicy(base_delay_seconds=1.0, multiplier=2.0, max_delay_seconds=10.0, jitter_ratio=0.0)
        assert policy.delay_for_attempt(10) == 10.0

    def test_jitter_applied(self):
        policy = RetryPolicy(base_delay_seconds=10.0, multiplier=1.0, max_delay_seconds=100.0, jitter_ratio=0.2)
        for _ in range(100):
            delay = policy.delay_for_attempt(0)
            assert 8.0 <= delay <= 12.0


class TestRetryAsync:
    @pytest.mark.asyncio
    async def test_succeeds_immediately(self):
        call_count = 0

        @retry_async(policy=RetryPolicy(attempts=3))
        async def succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeeds()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure_then_succeeds(self):
        call_count = 0

        @retry_async(policy=RetryPolicy(attempts=3, base_delay_seconds=0.01, jitter_ratio=0.0))
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return "ok"

        result = await fail_then_succeed()
        assert result == "ok"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        @retry_async(policy=RetryPolicy(attempts=2, base_delay_seconds=0.01, jitter_ratio=0.0), retry_on=(ValueError,))
        async def always_fail():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            await always_fail()

    @pytest.mark.asyncio
    async def test_does_not_retry_non_retryable_errors(self):
        call_count = 0

        @retry_async(policy=RetryPolicy(attempts=3, base_delay_seconds=0.01), retry_on=(ValueError,))
        async def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            await raise_type_error()
        assert call_count == 1


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    @pytest.mark.asyncio
    async def test_raises_on_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=1)
        cb.record_failure()
        with pytest.raises(CircuitOpenError):
            await cb.call(lambda: asyncio.sleep(0))

    @pytest.mark.asyncio
    async def test_success_resets_breaker(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2
        await cb.call(lambda: asyncio.sleep(0))
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self):
        import time

        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout_seconds=0.01)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        assert cb.allow_request() is True
        assert cb.state == CircuitState.HALF_OPEN


class TestAgentLoop:
    @pytest.mark.asyncio
    async def test_single_mode_succeeds_immediately(self):
        result = await run_agent_loop(
            lambda i: asyncio.sleep(0, result="done"),
            policy=LoopPolicy(max_iterations=3, mode=LoopMode.SINGLE),
        )
        assert result == "done"

    @pytest.mark.asyncio
    async def test_retry_on_invalid_mode_retries(self):
        calls = 0

        async def step(i):
            nonlocal calls
            calls += 1
            if i < 2:
                return "invalid"
            return "valid"

        result = await run_agent_loop(
            step,
            policy=LoopPolicy(
                max_iterations=5,
                mode=LoopMode.RETRY_ON_INVALID,
                stop_conditions=[lambda x: x == "valid"],
            ),
        )
        assert result == "valid"
        assert calls == 3

    @pytest.mark.asyncio
    async def test_raises_max_iterations(self):
        async def forever(i):
            return "never_valid"

        with pytest.raises(MaxIterationsExceeded):
            await run_agent_loop(
                forever,
                policy=LoopPolicy(
                    max_iterations=3,
                    mode=LoopMode.RETRY_ON_INVALID,
                    stop_conditions=[lambda x: x == "valid"],
                ),
            )


class TestTimeout:
    @pytest.mark.asyncio
    async def test_completes_within_timeout(self):
        result = await run_with_timeout(asyncio.sleep(0, result="ok"), TimeoutPolicy(seconds=5.0, node_name="test"))
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        async def slow():
            await asyncio.sleep(10)
            return "late"

        with pytest.raises(NodeTimeoutError, match="test"):
            await run_with_timeout(slow(), TimeoutPolicy(seconds=0.05, node_name="test"))


class TestCostTracker:
    def setup_method(self):
        self.tracker = CostTracker()

    def test_record_and_summary(self):
        self.tracker.record(CostRecord(
            node="plan", task="planning", provider="anthropic", model="claude-sonnet-4-20250514",
            input_tokens=100, output_tokens=50, duration_ms=500.0,
        ))
        self.tracker.record(CostRecord(
            node="plan", task="planning", provider="anthropic", model="claude-sonnet-4-20250514",
            input_tokens=200, output_tokens=80, duration_ms=600.0,
        ))
        self.tracker.record(CostRecord(
            node="execute", task="execution", provider="openai", model="gpt-4o",
            input_tokens=300, output_tokens=120, duration_ms=800.0,
        ))

        assert self.tracker.total_tokens() == 850  # 100+50+200+80+300+120
        assert len(self.tracker.records) == 3

        by_node = self.tracker.summary_by_node()
        assert "plan" in by_node
        assert "execute" in by_node
        assert by_node["plan"]["input_tokens"] == 300
        assert by_node["plan"]["output_tokens"] == 130
        assert by_node["plan"]["calls"] == 2

        by_provider = self.tracker.summary_by_provider()
        assert "anthropic" in by_provider
        assert "openai" in by_provider
        assert by_provider["anthropic"]["calls"] == 2

    def test_to_dict(self):
        self.tracker.record(CostRecord(
            node="plan", task="planning", provider="anthropic", model="claude-sonnet-4-20250514",
            input_tokens=100, output_tokens=50, duration_ms=500.0,
        ))
        d = self.tracker.to_dict()
        assert "total_tokens" in d
        assert "total_calls" in d
        assert "by_node" in d
        assert "by_provider" in d
        assert d["total_tokens"] == 150
        assert d["total_calls"] == 1
        assert d["by_node"]["plan"]["calls"] == 1

    def test_current_node_contextvar(self):
        assert current_node.get("unknown") == "unknown"
        current_node.set("plan")
        assert current_node.get() == "plan"


class TestContextTrimmer:
    def _make_state(self, n_outputs: int = 0, n_corrections: int = 0) -> AgentState:
        state = AgentState(
            project_id="p1",
            job_id="j1",
            assets=[],
            user_goal=UserGoal(prompt="test"),
            clip_metadata={},
            edit_script=None,
            correction_history=[
                CorrectionIntent(id=f"c{i}", project_id="p1", job_id="j1", raw_text=f"fix {i}", affected_nodes=["plan"])
                for i in range(n_corrections)
            ],
            current_output_path=None,
            subtitle_path=None,
            node_outputs={f"node_{i}": {"result": i} for i in range(n_outputs)},
            node_errors={},
            iteration_count={},
            pending_human_input=False,
            final_output_path=None,
        )
        return state

    def test_trims_large_node_outputs(self):
        state = self._make_state(n_outputs=30)
        trimmed = trim_agent_state(state)
        assert len(trimmed.node_outputs) <= MAX_NODE_OUTPUTS_ENTRIES

    def test_trims_correction_history(self):
        state = self._make_state(n_corrections=20)
        trimmed = trim_agent_state(state)
        assert len(trimmed.correction_history) <= MAX_CORRECTION_HISTORY

    def test_prunes_empty_error_lists(self):
        state = self._make_state()
        state.node_errors = {"a": [], "b": ["error"], "c": []}
        trimmed = trim_agent_state(state)
        assert "a" not in trimmed.node_errors
        assert "b" in trimmed.node_errors
        assert "c" not in trimmed.node_errors

    def test_noop_when_within_limits(self):
        state = self._make_state(n_outputs=5, n_corrections=3)
        trimmed = trim_agent_state(state)
        assert len(trimmed.node_outputs) == 5
        assert len(trimmed.correction_history) == 3