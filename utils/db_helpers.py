"""
Database utilities: connection pooling, caching, query optimization
"""
import asyncio
from functools import wraps
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database.session import get_session
from database.models import PatrolEvent, PatrolCheckpoint, CheckpointPhoto

logger = logging.getLogger(__name__)

# ============================================================================
# SIMPLE IN-MEMORY CACHE
# ============================================================================

class SimpleCache:
    """Простой in-memory кэш с TTL"""
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str, ttl_seconds: int = 30) -> Optional[Any]:
        """Получить значение из кэша"""
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                age = (datetime.now() - timestamp).total_seconds()
                if age < ttl_seconds:
                    logger.debug(f"Cache HIT: {key} (age={age:.1f}s)")
                    return value
                else:
                    logger.debug(f"Cache EXPIRED: {key} (age={age:.1f}s)")
                    del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any):
        """Сохранить значение в кэш"""
        async with self._lock:
            self._cache[key] = (value, datetime.now())
            logger.debug(f"Cache SET: {key}")
    
    async def delete(self, key: str):
        """Удалить значение из кэша"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE: {key}")
    
    async def clear(self):
        """Очистить весь кэш"""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

# Global cache instance
_cache = SimpleCache()

# ============================================================================
# PATROL QUERIES WITH CACHING
# ============================================================================

async def get_active_patrol(user_id: int, use_cache: bool = True) -> Optional[PatrolEvent]:
    """
    Получить активный патруль пользователя с кэшированием
    
    Args:
        user_id: ID пользователя в БД
        use_cache: Использовать кэш (по умолчанию True)
    
    Returns:
        PatrolEvent или None
    """
    cache_key = f"active_patrol:{user_id}"
    
    if use_cache:
        cached = await _cache.get(cache_key, ttl_seconds=10)
        if cached is not None:
            return cached
    
    async with get_session() as session:
        result = await session.execute(
            select(PatrolEvent)
            .where(
                PatrolEvent.guard_id == user_id,
                PatrolEvent.status == 'in_progress'
            )
            .options(
                selectinload(PatrolEvent.checkpoints).selectinload(PatrolCheckpoint.photos)
            )
        )
        patrol = result.scalar_one_or_none()
        
        if use_cache and patrol:
            await _cache.set(cache_key, patrol)
        
        return patrol

async def invalidate_patrol_cache(user_id: int):
    """Инвалидировать кэш патруля при изменениях"""
    await _cache.delete(f"active_patrol:{user_id}")

async def get_checkpoint_photo_count(checkpoint_id: int) -> int:
    """
    Получить количество фотографий точки патруля (оптимизированный запрос)
    
    Args:
        checkpoint_id: ID точки патруля
    
    Returns:
        Количество фотографий
    """
    cache_key = f"photo_count:{checkpoint_id}"
    
    cached = await _cache.get(cache_key, ttl_seconds=5)
    if cached is not None:
        return cached
    
    async with get_session() as session:
        result = await session.execute(
            select(func.count(CheckpointPhoto.id))
            .where(CheckpointPhoto.checkpoint_id == checkpoint_id)
        )
        count = result.scalar() or 0
        
        await _cache.set(cache_key, count)
        return count

async def invalidate_photo_count_cache(checkpoint_id: int):
    """Инвалидировать кэш счетчика фотографий"""
    await _cache.delete(f"photo_count:{checkpoint_id}")

async def get_patrol_by_id(
    patrol_id: int,
    user_id: Optional[int] = None,
    require_guard_match: bool = False
) -> Optional[PatrolEvent]:
    """
    Получить патруль по ID с полной предзагрузкой связей
    
    Args:
        patrol_id: ID патруля
        user_id: ID пользователя (для проверки доступа)
        require_guard_match: Требовать совпадения guard_id с user_id
    
    Returns:
        PatrolEvent или None
    """
    cache_key = f"patrol_details:{patrol_id}"
    
    cached = await _cache.get(cache_key, ttl_seconds=30)
    if cached is not None:
        # Проверяем доступ если требуется
        if require_guard_match and user_id and cached.guard_id != user_id:
            return None
        return cached
    
    async with get_session() as session:
        query = select(PatrolEvent).where(PatrolEvent.id == patrol_id)
        
        if require_guard_match and user_id:
            query = query.where(PatrolEvent.guard_id == user_id)
        
        result = await session.execute(
            query.options(
                selectinload(PatrolEvent.checkpoints).selectinload(PatrolCheckpoint.photos),
                selectinload(PatrolEvent.guard),
                selectinload(PatrolEvent.questions)
            )
        )
        patrol = result.scalar_one_or_none()
        
        if patrol:
            await _cache.set(cache_key, patrol)
        
        return patrol

async def get_patrol_archive(
    user_id: int,
    limit: int = 10,
    offset: int = 0
) -> List[PatrolEvent]:
    """
    Получить архив патрулей с пагинацией
    
    Args:
        user_id: ID пользователя
        limit: Лимит записей
        offset: Смещение
    
    Returns:
        Список патрулей
    """
    cache_key = f"patrol_archive:{user_id}:{limit}:{offset}"
    
    cached = await _cache.get(cache_key, ttl_seconds=60)
    if cached is not None:
        return cached
    
    async with get_session() as session:
        result = await session.execute(
            select(PatrolEvent)
            .where(
                PatrolEvent.guard_id == user_id,
                PatrolEvent.status == 'completed'
            )
            .options(
                selectinload(PatrolEvent.checkpoints)
            )
            .order_by(PatrolEvent.completed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        patrols = result.scalars().all()
        
        await _cache.set(cache_key, list(patrols))
        return list(patrols)

# ============================================================================
# BATCH OPERATIONS
# ============================================================================

async def batch_load_checkpoint_photos(checkpoint_ids: List[int]) -> Dict[int, int]:
    """
    Пакетная загрузка количества фотографий для нескольких точек
    
    Args:
        checkpoint_ids: Список ID точек патруля
    
    Returns:
        Словарь {checkpoint_id: photo_count}
    """
    if not checkpoint_ids:
        return {}
    
    async with get_session() as session:
        result = await session.execute(
            select(
                CheckpointPhoto.checkpoint_id,
                func.count(CheckpointPhoto.id).label('count')
            )
            .where(CheckpointPhoto.checkpoint_id.in_(checkpoint_ids))
            .group_by(CheckpointPhoto.checkpoint_id)
        )
        
        counts = {row.checkpoint_id: row.count for row in result}
        
        # Cache each result
        for checkpoint_id, count in counts.items():
            await _cache.set(f"photo_count:{checkpoint_id}", count)
        
        # Fill missing with 0
        for checkpoint_id in checkpoint_ids:
            if checkpoint_id not in counts:
                counts[checkpoint_id] = 0
        
        return counts

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

async def clear_all_cache():
    """Очистить весь кэш (use after major DB changes)"""
    await _cache.clear()

async def warm_cache_for_user(user_id: int):
    """Предзагрузить кэш для пользователя (call on /start)"""
    logger.info(f"Warming cache for user {user_id}")
    await get_active_patrol(user_id, use_cache=False)
