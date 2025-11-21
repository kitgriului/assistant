"""
Whisper transcription service using OpenAI API.
"""

from pathlib import Path
from typing import Optional

from openai import OpenAI

from ..utils import get_logger

logger = get_logger(__name__)


class WhisperService:
    """Handles audio transcription using OpenAI Whisper API."""
    
    def __init__(self, client: OpenAI, model: str = "whisper-1"):
        """
        Initialize Whisper service.
        
        Args:
            client: OpenAI client instance
            model: Whisper model to use (default: whisper-1)
        """
        self.client = client
        self.model = model
    
    async def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., "ru", "en") - auto-detect if None
            prompt: Optional prompt to guide transcription
            
        Returns:
            Transcribed text
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Transcribing {audio_path.name} using Whisper API")
        
        try:
            with open(audio_path, "rb") as f:
                kwargs = {"model": self.model, "file": f}
                
                if language:
                    kwargs["language"] = language
                if prompt:
                    kwargs["prompt"] = prompt
                
                response = self.client.audio.transcriptions.create(**kwargs)
            
            # Extract text from response
            text = getattr(response, "text", None)
            if not text:
                text = str(response)
            
            text = text.strip()
            logger.info(f"Transcription completed: {len(text)} characters")
            logger.debug(f"Transcribed text: {text[:100]}...")
            
            return text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}") from e
    
    async def translate(self, audio_path: Path) -> str:
        """
        Translate audio to English.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Translated text in English
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Translating {audio_path.name} to English")
        
        try:
            with open(audio_path, "rb") as f:
                response = self.client.audio.translations.create(
                    model=self.model,
                    file=f
                )
            
            text = getattr(response, "text", str(response)).strip()
            logger.info(f"Translation completed: {len(text)} characters")
            
            return text
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise RuntimeError(f"Failed to translate audio: {e}") from e
