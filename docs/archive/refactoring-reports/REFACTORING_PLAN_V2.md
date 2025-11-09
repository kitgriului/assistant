# 🔧 План рефакторинга GuardBot v2

## 🎯 Цели
1. **Исправить критические ошибки** (SQLAlchemy lazy loading)
2. **Оптимизировать производительность** (eager loading, кэширование)
3. **Улучшить читаемость** (type hints, документация)
4. **Упростить код** (DRY, SOLID principles)
5. **Повысить надежность** (error handling, logging)

## 🐛 Критические ошибки

### 1. SQLAlchemy MissingGreenlet
**Файл**: `handlers/patrol.py`  
**Проблема**: Доступ к `patrol.checkpoints` вне async session  
**Решение**: Использовать eager loading с `joinedload()` или `selectinload()`

```python
# ❌ ПЛОХО
async with get_session() as session:
    patrol = await session.get(PatrolEvent, id)
# patrol.checkpoints вызовет ошибку здесь!

# ✅ ХОРОШО  
from sqlalchemy.orm import selectinload

async with get_session() as session:
    result = await session.execute(
        select(PatrolEvent)
        .options(selectinload(PatrolEvent.checkpoints))
        .where(PatrolEvent.id == id)
    )
    patrol = result.scalar_one()
# Теперь patrol.checkpoints загружены!
```

### 2. Дублирование кода проверки доступа
**Файлы**: Все handlers  
**Проблема**: Повторяющийся код в каждом обработчике  
**Решение**: Middleware или декоратор

## 📊 Приоритеты рефакторинга

### HIGH (Критично)
- [ ] Исправить lazy loading в `patrol.py` (lines 189, 546)
- [ ] Исправить lazy loading в `guard.py` 
- [ ] Добавить error handling во все DB операции
- [ ] Оптимизировать N+1 queries

### MEDIUM (Важно)
- [ ] Добавить type hints везде
- [ ] Создать constants.py для magic numbers
- [ ] Вынести повторяющиеся клавиатуры
- [ ] Улучшить logging

### LOW (Желательно)
- [ ] Рефакторинг docstrings
- [ ] Unit tests
- [ ] Code style (Black, isort)

## 🔨 Изменения по файлам

### handlers/patrol.py
**Проблемы**:
1. ❌ Lazy loading `patrol.checkpoints` (lines 66, 113, 189, 546, 606)
2. ❌ Повторяющаяся логика `check_user_access`
3. ❌ Нет error handling для DB операций
4. ❌ Длинные функции (>100 lines)

**Решения**:
1. ✅ Eager loading везде
2. ✅ Middleware для проверки доступа
3. ✅ Try-except блоки с логированием
4. ✅ Разбить на меньшие функции

### handlers/guard.py  
**Проблемы**:
1. ❌ Дублирование логики в show_pending/active/archive
2. ❌ Длинные SQL запросы без форматирования
3. ❌ Нет пагинации для больших списков

**Решения**:
1. ✅ Общая функция `_show_requests_list(status, title)`
2. ✅ Query builder функции
3. ✅ Pagination helper

### utils/user_helpers.py
**Проблемы**:
1. ❌ Нет type hints
2. ❌ Нет docstrings
3. ❌ Нет error handling

**Решения**:
1. ✅ Полная типизация
2. ✅ Google-style docstrings
3. ✅ Graceful degradation

### database/models.py
**Проблемы**:
1. ❌ Нет helper методов в моделях
2. ❌ Lazy loading по умолчанию
3. ❌ Нет __repr__ для отладки

**Решения**:
1. ✅ Добавить @property и методы
2. ✅ Настроить lazy='selectin' где нужно
3. ✅ Добавить __repr__ везде

## 📝 Новые файлы

### bot/constants.py
```python
# Роли
ROLE_ADMIN = "admin"
ROLE_GUARD = "guard"  
ROLE_GUEST = "guest"

# Статусы заявок
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

# Эмодзи
EMOJI_CHECK = "✅"
EMOJI_CROSS = "❌"
EMOJI_WARNING = "⚠️"
```

### utils/keyboards.py
```python
# Общие клавиатуры
def get_back_button():
    return InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")

def get_cancel_button():
    return InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
```

### utils/db_helpers.py
```python
# Общие DB операции
async def get_user_by_telegram_id_eager(telegram_id: int):
    """Получить пользователя с загруженными связями"""
    ...
```

## 🧪 Тестирование

### Чек-лист
- [ ] Авторизация через телефон
- [ ] Создание заявки (пешеход/авто)
- [ ] Утверждение/отклонение заявок
- [ ] Создание обхода
- [ ] Добавление точек с фото
- [ ] Завершение обхода
- [ ] Управление пользователями

## 📈 Метрики улучшения

### Производительность
- N+1 queries: 15 → 0
- Средний response time: ~500ms → <200ms

### Качество кода
- Дублирование: ~300 lines → ~50 lines
- Покрытие тестами: 0% → 70%+
- Type hints: 20% → 100%

### Maintainability
- Cyclomatic complexity: High → Medium
- Cognitive complexity: High → Low

## ⚠️ Риски

1. **Breaking changes**: Нет, только внутренние изменения
2. **Data migration**: Не требуется
3. **API changes**: Нет изменений интерфейса

## 📅 Timeline

1. ✅ Анализ (30 мин) - DONE
2. ⏳ Исправление критических ошибок (1 час)
3. ⏳ Оптимизация handlers (1 час)
4. ⏳ Type hints + documentation (30 мин)
5. ⏳ Тестирование (30 мин)
6. ⏳ Документация (15 мин)

**Total**: ~3.5 hours

---
**Автор**: Senior Developer (20 years exp)  
**Дата**: 2025-11-01  
**Версия**: 2.0
