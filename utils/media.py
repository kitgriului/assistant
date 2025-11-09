"""Utilities for handling media files (photos, documents, etc.).

Provides safe file handling for incoming Telegram media with proper
path management, validation, and error handling.
"""
import os
import logging
from typing import Optional, Union
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from aiogram.types import PhotoSize, Document

from bot.config import settings


logger = logging.getLogger(__name__)


# Base media directory
MEDIA_DIR = Path(__file__).parent.parent / "data" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


class MediaError(Exception):
    """Base exception for media handling errors."""
    pass


class FileSizeError(MediaError):
    """Raised when file exceeds size limits."""
    pass


class FileTypeError(MediaError):
    """Raised when file type is not allowed."""
    pass


async def save_photo(
    bot: Bot, 
    photo: PhotoSize, 
    prefix: str = "photo_"
) -> str:
    """Save Telegram photo to disk.
    
    Args:
        bot: Bot instance for downloading
        photo: PhotoSize object from Telegram
        prefix: Filename prefix (default: "photo_")
        
    Returns:
        Absolute path to saved file
        
    Raises:
        FileSizeError: If photo exceeds size limit
        MediaError: If download fails
        
    Example:
        photo_path = await save_photo(bot, message.photo[-1])
        # Save path to database
    """
    try:
        # Get file info
        file = await bot.get_file(photo.file_id)
        
        # Check file size
        if file.file_size and file.file_size > settings.max_photo_size_bytes:
            raise FileSizeError(
                f"Photo size ({file.file_size} bytes) exceeds limit "
                f"({settings.max_photo_size_bytes} bytes)"
            )
        
        # Generate unique filename
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"{prefix}{photo.file_id}_{timestamp}.jpg"
        file_path = MEDIA_DIR / filename
        
        # Download file
        await bot.download_file(file.file_path, destination=file_path)
        
        logger.info(f"Saved photo: {file_path} ({file.file_size} bytes)")
        return str(file_path.absolute())
        
    except FileSizeError:
        raise
    except Exception as e:
        logger.exception(f"Failed to save photo: {e}")
        raise MediaError(f"Failed to save photo: {e}") from e


async def save_document(
    bot: Bot, 
    document: Document, 
    prefix: str = "doc_",
    allowed_extensions: Optional[list[str]] = None,
) -> str:
    """Save Telegram document to disk.
    
    Args:
        bot: Bot instance for downloading
        document: Document object from Telegram
        prefix: Filename prefix (default: "doc_")
        allowed_extensions: List of allowed file extensions (e.g., ['.pdf', '.jpg'])
                           If None, all extensions allowed
        
    Returns:
        Absolute path to saved file
        
    Raises:
        FileSizeError: If document exceeds size limit
        FileTypeError: If document extension not allowed
        MediaError: If download fails
        
    Example:
        doc_path = await save_document(
            bot, 
            message.document,
            allowed_extensions=['.pdf', '.jpg']
        )
    """
    try:
        # Get file info
        file = await bot.get_file(document.file_id)
        
        # Check file size
        if file.file_size and file.file_size > settings.max_photo_size_bytes:
            raise FileSizeError(
                f"Document size ({file.file_size} bytes) exceeds limit "
                f"({settings.max_photo_size_bytes} bytes)"
            )
        
        # Get file extension
        original_name = document.file_name or "unnamed"
        extension = Path(original_name).suffix.lower()
        
        # Validate extension if restrictions set
        if allowed_extensions and extension not in allowed_extensions:
            raise FileTypeError(
                f"File type {extension} not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"{prefix}{document.file_id}_{timestamp}{extension}"
        file_path = MEDIA_DIR / filename
        
        # Download file
        await bot.download_file(file.file_path, destination=file_path)
        
        logger.info(f"Saved document: {file_path} ({file.file_size} bytes)")
        return str(file_path.absolute())
        
    except (FileSizeError, FileTypeError):
        raise
    except Exception as e:
        logger.exception(f"Failed to save document: {e}")
        raise MediaError(f"Failed to save document: {e}") from e


async def save_file(
    bot: Bot,
    file_obj: Union[PhotoSize, Document],
    prefix: str = "file_",
) -> str:
    """Save any file object (photo or document).
    
    Convenience wrapper that dispatches to appropriate handler based on type.
    
    Args:
        bot: Bot instance for downloading
        file_obj: PhotoSize or Document object
        prefix: Filename prefix
        
    Returns:
        Absolute path to saved file
        
    Raises:
        ValueError: If file_obj type is not supported
        MediaError: If save operation fails
        
    Example:
        # Works with both photos and documents
        file_path = await save_file(bot, message.photo[-1])
        file_path = await save_file(bot, message.document)
    """
    if isinstance(file_obj, PhotoSize):
        return await save_photo(bot, file_obj, prefix)
    elif isinstance(file_obj, Document):
        return await save_document(bot, file_obj, prefix)
    else:
        raise ValueError(f"Unsupported file type: {type(file_obj)}")


def get_media_path(filename: str) -> Path:
    """Get full path for media file.
    
    Args:
        filename: Media filename (not full path)
        
    Returns:
        Full path to media file
        
    Example:
        path = get_media_path("photo_123_456.jpg")
    """
    return MEDIA_DIR / filename


def cleanup_old_media(days: int = 30) -> int:
    """Delete media files older than specified days.
    
    Args:
        days: Delete files older than this many days
        
    Returns:
        Number of files deleted
        
    Example:
        deleted = cleanup_old_media(days=30)
        logger.info(f"Cleaned up {deleted} old files")
    """
    cutoff_time = datetime.utcnow().timestamp() - (days * 86400)
    deleted_count = 0
    
    try:
        for file_path in MEDIA_DIR.iterdir():
            if not file_path.is_file():
                continue
            
            # Check file modification time
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old media file: {file_path}")
        
        logger.info(f"Cleaned up {deleted_count} media files older than {days} days")
        return deleted_count
        
    except Exception as e:
        logger.exception(f"Error during media cleanup: {e}")
        return deleted_count
