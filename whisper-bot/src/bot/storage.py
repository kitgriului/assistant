"""
In-memory storage for bot data.
In production, consider using Redis or a database.
"""

from typing import Dict, Optional


class TranscriptionStorage:
    """Simple in-memory storage for transcriptions."""
    
    def __init__(self):
        """Initialize storage."""
        self._storage: Dict[int, str] = {}
    
    def save(self, chat_id: int, text: str) -> None:
        """
        Save transcription for a chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Transcribed text
        """
        self._storage[chat_id] = text
    
    def get(self, chat_id: int) -> Optional[str]:
        """
        Get transcription for a chat.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Transcribed text or None if not found
        """
        return self._storage.get(chat_id)
    
    def delete(self, chat_id: int) -> None:
        """
        Delete transcription for a chat.
        
        Args:
            chat_id: Telegram chat ID
        """
        self._storage.pop(chat_id, None)
    
    def clear(self) -> None:
        """Clear all transcriptions."""
        self._storage.clear()
    
    def __len__(self) -> int:
        """Get number of stored transcriptions."""
        return len(self._storage)
