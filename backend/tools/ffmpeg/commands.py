from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FFmpegCommand:
    args: list[str] = field(default_factory=list)

    def as_subprocess_args(self) -> list[str]:
        return ["ffmpeg", "-y", *self.args]


def trim(input_path: str, output_path: str, start: float, end: float) -> FFmpegCommand:
    return FFmpegCommand(["-ss", str(start), "-to", str(end), "-i", input_path, "-c", "copy", output_path])


def concat(inputs_file: str, output_path: str) -> FFmpegCommand:
    return FFmpegCommand(["-f", "concat", "-safe", "0", "-i", inputs_file, "-c", "copy", output_path])


def resize(input_path: str, output_path: str, width: int, height: int) -> FFmpegCommand:
    vf = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    return FFmpegCommand(["-i", input_path, "-vf", vf, output_path])


def speed(input_path: str, output_path: str, speed: float, has_audio: bool = True) -> FFmpegCommand:
    video_filter = f"[0:v]setpts={1/speed}*PTS[v]"
    if has_audio:
        atempo_filters = []
        remaining = speed
        while remaining < 0.5 or remaining > 2.0:
            if remaining < 0.5:
                atempo_filters.append("atempo=0.5")
                remaining = remaining / 0.5
            else:
                atempo_filters.append("atempo=2.0")
                remaining = remaining / 2.0
        atempo_filters.append(f"atempo={remaining}")
        atempo_str = ",".join(atempo_filters)
        return FFmpegCommand([
            "-i", input_path,
            "-filter_complex", f"{video_filter};[0:a]{atempo_str}[a]",
            "-map", "[v]", "-map", "[a]", output_path,
        ])
    return FFmpegCommand(["-i", input_path, "-vf", f"setpts={1/speed}*PTS", "-an", output_path])


def fade_transition(input1: str, input2: str, output_path: str, duration: float, offset: float, transition: str = "fade") -> FFmpegCommand:
    xfade_filter = f"[0:v][1:v]xfade=transition={transition}:duration={duration}:offset={offset}[v]"
    return FFmpegCommand([
        "-i", input1, "-i", input2,
        "-filter_complex", xfade_filter,
        "-map", "[v]", output_path,
    ])


def text_overlay(
    input_path: str,
    output_path: str,
    text: str,
    fontsize: int = 24,
    fontcolor: str = "white",
    box: int = 1,
    boxcolor: str = "black@0.5",
    x: int = 10,
    y: int = 10,
    fontfile: str | None = None,
) -> FFmpegCommand:
    escaped_text = text.replace("'", "'\\''").replace(":", "\\:")
    drawtext = (
        f"drawtext=text='{escaped_text}':fontsize={fontsize}:fontcolor={fontcolor}"
        f":box={box}:boxcolor={boxcolor}:x={x}:y={y}"
    )
    if fontfile:
        drawtext += f":fontfile={fontfile}"
    return FFmpegCommand(["-i", input_path, "-vf", drawtext, output_path])


def burn_subtitle(input_path: str, subtitle_path: str, output_path: str) -> FFmpegCommand:
    return FFmpegCommand(["-i", input_path, "-vf", f"subtitles={subtitle_path}", output_path])


def audio_mix(
    video_path: str,
    audio_path: str,
    output_path: str,
    video_volume: float = 1.0,
    audio_volume: float = 1.0,
) -> FFmpegCommand:
    filter_parts = [
        f"[0:a]volume={video_volume}[a0]",
        f"[1:a]volume={audio_volume}[a1]",
        "[a0][a1]amix=inputs=2:duration=first[aout]",
    ]
    complex_filter = ";".join(filter_parts)
    return FFmpegCommand([
        "-i", video_path, "-i", audio_path,
        "-filter_complex", complex_filter,
        "-map", "0:v", "-map", "[aout]",
        output_path,
    ])


def audio_normalize(input_path: str, output_path: str) -> FFmpegCommand:
    return FFmpegCommand([
        "-i", input_path,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "copy", output_path,
    ])


def poster_thumbnail(input_path: str, output_path: str, timestamp: float = 0.0, width: int = 320) -> FFmpegCommand:
    return FFmpegCommand([
        "-ss", str(timestamp), "-i", input_path,
        "-vframes", "1", "-vf", f"scale={width}:-1",
        output_path,
    ])


PLATFORM_PRESETS: dict[str, dict] = {
    "douyin": {"width": 1080, "height": 1920, "bitrate": "4M", "aspect": "9:16"},
    "xiaohongshu": {"width": 1080, "height": 1440, "bitrate": "3M", "aspect": "3:4"},
    "taobao": {"width": 1080, "height": 1080, "bitrate": "3M", "aspect": "1:1"},
    "bilibili": {"width": 1920, "height": 1080, "bitrate": "6M", "aspect": "16:9"},
}


def final_render(input_path: str, output_path: str, platform: str = "douyin", bitrate: str | None = None) -> FFmpegCommand:
    preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["douyin"])
    target_bitrate = bitrate or preset["bitrate"]
    return FFmpegCommand([
        "-i", input_path,
        "-c:v", "libx264", "-preset", "medium", "-b:v", target_bitrate,
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ])