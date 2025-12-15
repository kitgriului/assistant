"""
GPT service for text processing and generation.
"""

from enum import Enum
from typing import List, Dict, Any

from openai import OpenAI

from utils import get_logger

logger = get_logger(__name__)


class ProcessingType(Enum):
    """Types of text processing operations."""
    NOTE = "note"
    MEETING = "meeting"
    SUMMARY = "summary"


class GPTService:
    """Handles text processing using OpenAI GPT models."""
    
    def __init__(
        self,
        client: OpenAI,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7
    ):
        """
        Initialize GPT service.
        
        Args:
            client: OpenAI client instance
            model: GPT model to use
            temperature: Sampling temperature (0-2)
        """
        self.client = client
        self.model = model
        self.temperature = temperature
    
    async def create_note(self, text: str) -> str:
        """
        Create structured Markdown note from transcription.
        
        Args:
            text: Transcribed text
            
        Returns:
            Formatted note in Markdown
        """
        logger.info("Creating note from transcription")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты помощник, который оформляет расшифровки аудио в структурированные заметки в формате Markdown. "
                    "Твоя задача: создать чёткую, читаемую заметку с заголовками, списками и форматированием. "
                    "Убери слова-паразиты, повторы, сохрани все факты и смысл. Используй эмодзи для улучшения читаемости."
                )
            },
            {
                "role": "user",
                "content": f"Создай структурированную заметку из этого текста:\n\n{text}"
            }
        ]
        
        return await self._complete(messages, temperature=0.7)
    
    async def extract_meeting_info(self, text: str) -> str:
        """
        Extract meeting information from transcription.
        
        Args:
            text: Transcribed text
            
        Returns:
            Formatted meeting information
        """
        logger.info("Extracting meeting information")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты помощник, который извлекает информацию о встрече из текста. "
                    "Определи и структурируй: тему встречи, дату и время (если есть), участников, повестку/задачи. "
                    "Оформи результат в Markdown с чёткой структурой. Если какая-то информация отсутствует, укажи это."
                )
            },
            {
                "role": "user",
                "content": f"Извлеки информацию о встрече из этого текста:\n\n{text}"
            }
        ]
        
        return await self._complete(messages, temperature=0.5)
    
    async def create_summary(self, text: str) -> str:
        """
        Create structured summary from transcription.
        
        Args:
            text: Transcribed text
            
        Returns:
            Formatted summary
        """
        logger.info("Creating summary")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты помощник, который создаёт краткое саммари из текста в информационном стиле. "
                    "Убери все повторы, слова-паразиты и лишние слова. "
                    "Сохрани все ключевые факты, идеи и выводы. "
                    "Оформи текст чётко и лаконично, без эмодзи и специального форматирования. "
                    "Используй простые абзацы или нумерованный список для структуры."
                )
            },
            {
                "role": "user",
                "content": f"Создай краткое саммари из этого текста:\n\n{text}"
            }
        ]
        
        return await self._complete(messages, temperature=0.5)
    
    async def process_with_prompt(self, text: str, user_prompt: str) -> str:
        """
        Process text with custom user prompt.
        
        Args:
            text: Transcribed text
            user_prompt: Custom prompt from user
            
        Returns:
            Processed text
        """
        logger.info(f"Processing with custom prompt: {user_prompt[:50]}...")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты помощник, который обрабатывает расшифровку аудио согласно указаниям пользователя. "
                    "Выполни запрос пользователя точно и качественно."
                )
            },
            {
                "role": "user",
                "content": f"Текст для обработки:\n\n{text}\n\n---\n\nЗадание: {user_prompt}"
            }
        ]
        
        return await self._complete(messages, temperature=0.7)
    
    async def _complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None = None
    ) -> str:
        """
        Internal method to call GPT completion API.
        
        Args:
            messages: List of message dicts
            temperature: Override default temperature
            
        Returns:
            Generated text
            
        Raises:
            RuntimeError: If API call fails
        """
        temp = temperature if temperature is not None else self.temperature
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp
            )
            
            result = response.choices[0].message.content or ""
            
            if not result:
                logger.warning("GPT returned empty response")
                return "Не удалось обработать текст"
            
            logger.debug(f"GPT response: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"GPT completion failed: {e}")
            raise RuntimeError(f"Failed to process text with GPT: {e}") from e
