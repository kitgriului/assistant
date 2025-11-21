"""
Media processing service for audio/video files.
Handles format conversion using ffmpeg.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional

from ..utils import get_logger

logger = get_logger(__name__)


class MediaProcessor:
    """Handles media file processing and conversion."""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize media processor.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable
        """
        self.ffmpeg_path = ffmpeg_path
    
    async def convert_to_wav(
        self,
        src: Path,
        dst: Path,
        sample_rate: int = 16000,
        channels: int = 1
    ) -> None:
        """
        Convert any audio/video file to mono WAV format.
        
        Args:
            src: Source file path
            dst: Destination WAV file path
            sample_rate: Output sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            
        Raises:
            FileNotFoundError: If ffmpeg is not installed
            RuntimeError: If conversion fails
        """
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output file
            "-i", str(src),
            "-ac", str(channels),
            "-ar", str(sample_rate),
            str(dst),
        ]
        
        logger.info(f"Converting {src.name} to WAV format")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                "ffmpeg is not installed or not found in PATH. "
                "Install with: apt install ffmpeg (Linux) or brew install ffmpeg (Mac)"
            ) from e
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            error_msg = stderr.decode(errors="ignore")
            logger.error(f"FFmpeg conversion failed: {error_msg}")
            raise RuntimeError(f"Failed to convert {src.name} to WAV format")
        
        logger.info(f"Successfully converted {src.name} to WAV")
    
    async def get_duration(self, file_path: Path) -> Optional[float]:
        """
        Get duration of media file in seconds.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Duration in seconds or None if cannot be determined
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            
            if proc.returncode == 0:
                duration_str = stdout.decode().strip()
                return float(duration_str)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Could not determine duration for {file_path.name}: {e}")
        
        return None
