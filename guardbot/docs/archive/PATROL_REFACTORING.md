# Рефакторинг модуля Patrol

## Дата: 7 ноября 2025

## Проблема
При попытке добавить точку в обходе возникала ошибка:
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
```

Ошибка происходила на строке 152 в `handlers/patrol.py` при доступе к `patrol.checkpoints`.

## Причина
SQLAlchemy в асинхронном режиме не может выполнять "ленивую загрузку" (lazy loading) связанных объектов. При обращении к `patrol.checkpoints` без предварительной загрузки, SQLAlchemy пытается выполнить синхронный запрос, что вызывает ошибку MissingGreenlet.

## Решение

### 1. Исправление lazy loading

Добавлен `selectinload` для явной загрузки связанных объектов во всех запросах:

**Было:**
```python
result = await session.execute(
    select(PatrolEvent)
    .where(PatrolEvent.guard_id == user.id)
)
patrol = result.scalar_one_or_none()
points_count = len(patrol.checkpoints)  # ❌ Ошибка здесь
```

**Стало:**
```python
result = await session.execute(
    select(PatrolEvent)
    .where(PatrolEvent.guard_id == user.id)
    .options(selectinload(PatrolEvent.checkpoints))
)
patrol = result.scalar_one_or_none()
points_count = len(patrol.checkpoints)  # ✅ Работает
```

### 2. Оптимизация запросов

В функции `patrol_add_point` заменил загрузку всех checkpoints на прямой SQL COUNT:

**Было:**
```python
result = await session.execute(
    select(PatrolEvent)
    .options(selectinload(PatrolEvent.checkpoints))
    .where(...)
)
patrol = result.scalar_one_or_none()
checkpoint_number = len(patrol.checkpoints) + 1
```

**Стало:**
```python
result = await session.execute(
    select(PatrolEvent)
    .where(...)
)
patrol = result.scalar_one_or_none()

count_result = await session.execute(
    select(func.count(PatrolCheckpoint.id))
    .where(PatrolCheckpoint.patrol_event_id == patrol.id)
)
checkpoint_count = count_result.scalar() or 0
checkpoint_number = checkpoint_count + 1
```

**Преимущества:**
- Не загружаем все объекты checkpoints, только считаем их количество
- Быстрее выполняется для обходов с большим количеством точек
- Меньше нагрузка на память

### 3. Обработка ошибок

Добавлен try-except блок в критичную функцию `patrol_add_point`:

```python
@router.callback_query(F.data == "patrol_add_point")
async def patrol_add_point(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Вся логика функции
        ...
    except Exception as e:
        logger.error(f"Error adding patrol point: {e}")
        await callback.answer(
            "❌ Ошибка при добавлении точки. Попробуйте снова.", 
            show_alert=True
        )
```

### 4. Проверенные функции

Все функции с доступом к связанным объектам проверены и исправлены:

1. ✅ `patrol_main_menu` - добавлен `selectinload(PatrolEvent.checkpoints)`
2. ✅ `patrol_add_point` - оптимизирован с COUNT + обработка ошибок
3. ✅ `patrol_show_points` - добавлен `selectinload` для checkpoints и photos
4. ✅ `patrol_finish` - добавлен `selectinload(PatrolEvent.checkpoints)`
5. ✅ `patrol_archive` - добавлен `selectinload` для checkpoints и guard
6. ✅ `view_patrol_command` - добавлен `selectinload` для всех связей
7. ✅ `handle_question_text` - добавлен `selectinload(PatrolEvent.guard)`

## Изменённые файлы

- `handlers/patrol.py` - основной рефакторинг
- `states/guard.py` - добавлены FSM состояния (уже было сделано ранее)

## Тестирование

Бот успешно запущен. Требуется протестировать:

1. ✅ Создание обхода: `/patrol` → "🚶 Начать обход"
2. 🔄 Добавление точки с фото и геолокацией
3. 🔄 Завершение обхода
4. 🔄 Просмотр архива обходов
5. 🔄 Q&A система (админ задает вопрос, охранник отвечает)

## Следующие шаги

1. Провести полное тестирование всех функций модуля
2. Добавить аналогичную обработку ошибок в остальные функции
3. Рассмотреть возможность добавления индексов в БД для оптимизации COUNT запросов
4. Обновить документацию для пользователей

## Технические детали

**SQLAlchemy версия:** 2.0.44
**Aiogram версия:** 3.22.0
**aiosqlite версия:** 0.21.0

**Важно:** В асинхронном SQLAlchemy всегда используйте:
- `selectinload()` для отношений one-to-many и many-to-many
- `joinedload()` для отношений many-to-one
- Или настройте `lazy="selectin"` в определении отношения в models.py
