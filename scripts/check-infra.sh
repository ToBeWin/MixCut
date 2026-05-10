#!/usr/bin/env sh
set -eu

check_http() {
  name="$1"
  url="$2"
  code="$(curl -fsS -o /dev/null -w "%{http_code}" "$url" || true)"
  if [ "$code" = "200" ] || [ "$code" = "302" ]; then
    printf "ok   %s %s\n" "$name" "$url"
  else
    printf "fail %s %s returned %s\n" "$name" "$url" "${code:-no response}" >&2
    return 1
  fi
}

check_tcp() {
  name="$1"
  host="$2"
  port="$3"
  if nc -z "$host" "$port" >/dev/null 2>&1; then
    printf "ok   %s %s:%s\n" "$name" "$host" "$port"
  else
    printf "fail %s %s:%s not reachable\n" "$name" "$host" "$port" >&2
    return 1
  fi
}

check_tcp "postgres" "127.0.0.1" "5432"
check_tcp "redis" "127.0.0.1" "6379"
check_http "minio" "http://127.0.0.1:9000/minio/health/live"
check_http "jaeger" "http://127.0.0.1:16686/"
check_http "prometheus" "http://127.0.0.1:9090/-/healthy"
check_http "grafana" "http://127.0.0.1:3001/api/health"
