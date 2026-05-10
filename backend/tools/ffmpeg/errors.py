"""FFmpeg exception types."""


class FFmpegError(RuntimeError):
    """Raised when an FFmpeg command fails."""


class FFprobeError(RuntimeError):
    """Raised when ffprobe fails."""

