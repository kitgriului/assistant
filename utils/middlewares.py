"""
Middleware для защиты от конфликтов и оптимизации
"""
import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime, timedelta

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)

# ============================================================================
# CALLBACK DEDUPLICATION MIDDLEWARE
# ============================================================================

class CallbackDeduplicationMiddleware(BaseMiddleware):
    """
    Защита от множественных нажатий одной кнопки
    Отслеживает callback_data + message_id и блокирует дубли
    """
    
    def __init__(self, ttl_seconds: int = 3):
        super().__init__()
        self.ttl_seconds = ttl_seconds
        self._processed: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Применяется только к callback_query
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)
        
        callback: CallbackQuery = event
        
        # Создаём уникальный ключ
        key = f"{callback.from_user.id}:{callback.message.message_id}:{callback.data}"
        
        async with self._lock:
            now = datetime.now()
            
            # Очищаем старые записи
            expired_keys = [
                k for k, v in self._processed.items()
                if (now - v).total_seconds() > self.ttl_seconds
            ]
            for k in expired_keys:
                del self._processed[k]
            
            # Проверяем дубликат
            if key in self._processed:
                age = (now - self._processed[key]).total_seconds()
                logger.warning(
                    f"DUPLICATE callback detected: {callback.data} "
                    f"(age={age:.2f}s, user={callback.from_user.id})"
                )
                await callback.answer(
                    "⚠️ Подождите, обрабатываю предыдущее действие...",
                    show_alert=False
                )
                return
            
            # Записываем новый
            self._processed[key] = now
        
        try:
            # Всегда отвечаем на callback чтобы убрать "часики"
            await callback.answer()
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error in callback handler: {e}")
            # Удаляем из обработанных чтобы можно было повторить
            async with self._lock:
                self._processed.pop(key, None)
            raise

# ============================================================================
# USER ACTION LOCK MIDDLEWARE
# ============================================================================

class UserActionLockMiddleware(BaseMiddleware):
    """
    Блокирует одновременную обработку нескольких действий одного пользователя
    Предотвращает race conditions в FSM state и DB
    """
    
    def __init__(self):
        super().__init__()
        self._locks: Dict[int, asyncio.Lock] = {}
        self._lock = asyncio.Lock()
    
    async def _get_user_lock(self, user_id: int) -> asyncio.Lock:
        """Получить или создать lock для пользователя"""
        async with self._lock:
            if user_id not in self._locks:
                self._locks[user_id] = asyncio.Lock()
            return self._locks[user_id]
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        else:
            return await handler(event, data)
        
        # НЕ блокируем фото - они могут приходить подряд быстро
        if isinstance(event, Message) and event.photo:
            return await handler(event, data)
        
        # Получаем lock пользователя
        user_lock = await self._get_user_lock(user_id)
        
        # Пытаемся захватить lock
        if user_lock.locked():
            logger.warning(f"User {user_id} action blocked - previous action still processing")
            if isinstance(event, CallbackQuery):
                await event.answer("⏳ Подождите, предыдущее действие ещё обрабатывается")
            elif isinstance(event, Message):
                await event.answer("⏳ Подождите секунду...")
            return
        
        async with user_lock:
            return await handler(event, data)

# ============================================================================
# RATE LIMITING MIDDLEWARE
# ============================================================================

class RateLimitMiddleware(BaseMiddleware):
    """
    Ограничение количества действий в секунду
    Защита от флуда и злоупотреблений
    """
    
    def __init__(self, max_actions: int = 5, window_seconds: int = 1):
        super().__init__()
        self.max_actions = max_actions
        self.window_seconds = window_seconds
        self._actions: Dict[int, list[datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        else:
            return await handler(event, data)
        
        async with self._lock:
            now = datetime.now()
            
            # Инициализируем список если нет
            if user_id not in self._actions:
                self._actions[user_id] = []
            
            # Удаляем старые записи
            cutoff = now - timedelta(seconds=self.window_seconds)
            self._actions[user_id] = [
                t for t in self._actions[user_id]
                if t > cutoff
            ]
            
            # Проверяем лимит
            if len(self._actions[user_id]) >= self.max_actions:
                logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{len(self._actions[user_id])} actions in {self.window_seconds}s"
                )
                if isinstance(event, CallbackQuery):
                    await event.answer(
                        "⚠️ Слишком много действий. Подождите немного.",
                        show_alert=True
                    )
                elif isinstance(event, Message):
                    await event.answer("⚠️ Вы отправляете сообщения слишком быстро. Подождите.")
                return
            
            # Записываем новое действие
            self._actions[user_id].append(now)
        
        return await handler(event, data)

# ============================================================================
# ERROR HANDLER MIDDLEWARE
# ============================================================================

class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Перехват и логирование всех ошибок
    Отправка дружественных сообщений пользователю
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Unhandled error in handler: {e}")
            
            # Отправляем сообщение пользователю
            error_message = (
                "❌ Произошла ошибка при обработке вашего запроса.\n"
                "Попробуйте ещё раз или обратитесь к администратору."
            )
            
            try:
                if isinstance(event, CallbackQuery):
                    await event.answer(error_message, show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(error_message)
            except:
                pass  # Не можем отправить - ничего не делаем
            
            # Не пробрасываем ошибку дальше чтобы бот не падал
            return None

# ============================================================================
# LOGGING MIDDLEWARE
# ============================================================================

class RequestLoggingMiddleware(BaseMiddleware):
    """
    Логирование всех входящих запросов
    Полезно для отладки и мониторинга
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        start_time = datetime.now()
        
        # Логируем запрос
        if isinstance(event, Message):
            logger.info(
                f"Message from user {event.from_user.id}: "
                f"{event.text[:50] if event.text else 'non-text'}"
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                f"Callback from user {event.from_user.id}: "
                f"{event.data}"
            )
        
        # Обрабатываем
        result = await handler(event, data)
        
        # Логируем время обработки
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > 1.0:
            logger.warning(f"Slow handler: {elapsed:.2f}s")
        else:
            logger.debug(f"Handler completed in {elapsed:.2f}s")
        
        return result


# ============================================================================
# ALBUM MIDDLEWARE - для обработки альбомов (несколько фото сразу)
# ============================================================================

class AlbumMiddleware(BaseMiddleware):
    """
    Собирает фото из альбома (media_group) в один список
    Aiogram 3 присылает каждое фото отдельно, но с одинаковым media_group_id
    """
    
    def __init__(self, latency: float = 0.5):
        """
        :param latency: Задержка ожидания всех фото из альбома (секунды)
        """
        super().__init__()
        self.latency = latency
        self.album_data: Dict[str, Dict[str, Any]] = {}
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Применяется только к сообщениям с фото
        if not isinstance(message, Message) or not message.photo:
            return await handler(message, data)
        
        # Если нет media_group_id, это одиночное фото
        if not message.media_group_id:
            return await handler(message, data)
        
        # Есть media_group_id - это альбом
        media_group_id = message.media_group_id
        
        try:
            # Инициализируем данные альбома
            if media_group_id not in self.album_data:
                self.album_data[media_group_id] = {
                    "messages": [],
                    "lock": asyncio.Lock(),
                    "processed": False
                }
            
            album_info = self.album_data[media_group_id]
            
            async with album_info["lock"]:
                # Добавляем сообщение в список
                album_info["messages"].append(message)
                
                # Если уже обработан, пропускаем
                if album_info["processed"]:
                    return None
                
                # Ждём остальные фото (небольшая задержка)
                await asyncio.sleep(self.latency)
                
                # Помечаем как обработанный
                album_info["processed"] = True
                
                # Собираем все фото из альбома
                album_messages = album_info["messages"]
                
                # Передаём список фото в data
                data["album"] = album_messages
                data["is_album"] = True
                
                # Вызываем handler с первым сообщением (с данными альбома)
                result = await handler(album_messages[0], data)
                
                # Очищаем данные альбома
                del self.album_data[media_group_id]
                
                return result
        
        except Exception as e:
            logger.error(f"Album middleware error: {e}")
            # В случае ошибки обрабатываем как обычное фото
            return await handler(message, data)


# ============================================================================
# COMMAND INTERRUPT MIDDLEWARE - для прерывания FSM командами
# ============================================================================

class CommandInterruptMiddleware(BaseMiddleware):
    """
    Позволяет прервать любое FSM состояние командами /menu, /start, /help
    """
    
    INTERRUPT_COMMANDS = ["/menu", "/start", "/help"]
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Применяется только к сообщениям
        if not isinstance(message, Message):
            return await handler(message, data)
        
        # Проверяем текст сообщения
        if message.text and message.text.startswith(tuple(self.INTERRUPT_COMMANDS)):
            # Получаем FSM context
            state = data.get("state")
            if state:
                # Очищаем состояние
                await state.clear()
                logger.info(f"FSM state cleared by command: {message.text}")
        
        return await handler(message, data)
