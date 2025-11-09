# 🔧 План рефакторинга GuardBot

**Дата анализа:** 01.11.2025  
**Версия:** 0.9.0 Beta  
**Бэкап:** backup_20251101_202307

---

## 🔍 АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ

### ❌ Выявленные проблемы

#### 1. **КРИТИЧНО: Дублирование кода получения пользователя**
**Локация:** `handlers/applicant.py` (5 мест)

**Проблема:**
```python
# Повторяется 5+ раз в одном файле
from handlers.menu import show_main_menu
user_telegram_id = message.from_user.id

async with get_session() as session:
    result = await session.execute(
        select(User).where(User.telegram_id == user_telegram_id)
    )
    user = result.scalar_one_or_none()
    role = user.role if user else "guest"
    name = user.name if user else "Гость"

await show_main_menu(message, role, name)
```

**Последствия:**
- 50+ строк дублированного кода
- Риск рассинхронизации при изменениях
- Сложность поддержки

---

#### 2. **Путаница в навигации меню**
**Локация:** `handlers/auth_phone.py` строки 179-250

**Проблема:**
- В `/start` команде дублируется логика показа меню
- Разные подходы к созданию клавиатур (inline vs код в auth_phone.py)
- Не используется `show_main_menu()` из menu.py

**Код в auth_phone.py:**
```python
if user.role == "admin":
    # Дублирует логику из menu.py
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Заявки на утверждение", callback_data="menu_pending")],
        # ... еще 5 кнопок
    ])
elif user.role == "guard":
    # Еще одна копия логики
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Заявки на утверждение", callback_data="menu_pending")]
    ])
```

**Последствия:**
- Кнопки "скачут" - старое и новое меню конфликтуют
- При изменении меню надо править 2 места
- Нет единого источника правды

---

#### 3. **Циклические импорты**
**Локация:** По всему проекту

**Проблема:**
```python
# В applicant.py, guard.py и др.
from handlers.menu import show_main_menu  # Импорт внутри функций
```

**Последствия:**
- Импорты внутри функций (анти-паттерн)
- Сложность анализа зависимостей
- Потенциальные ошибки при рефакторинге

---

#### 4. **Отсутствие утилит для частых операций**
**Отсутствует:**
- Хелпер для получения пользователя по telegram_id
- Хелпер для возврата в меню с очисткой состояния
- Декораторы проверки ролей
- Унифицированные обработчики ошибок

---

#### 5. **Избыточные файлы в корне проекта**
**Найдено 15+ служебных скриптов:**
```
create_admin.py
make_admin.py
set_admin.py
init_users.py
setup_users.py
add_users_direct.py
quick_reset.py
reset_bot.py
test_*.py
check_*.py
debug_*.py
fix_webhook.py
migrate_db.py
```

**Последствия:**
- Захламленность корня
- Сложность навигации
- Неясно, что активно используется

---

## ✅ ЧТО РАБОТАЕТ ХОРОШО

1. **Архитектура обработчиков** - четкое разделение по ролям
2. **FSM система** - хорошо структурированные состояния
3. **База данных** - правильная модель с relationships
4. **QR-коды с deep links** - надежная реализация
5. **Уведомления** - полноценная система оповещений
6. **Новая структура меню** - подменю "Управление заявками" правильное решение

---

## 🎯 ПЛАН РЕФАКТОРИНГА

### Фаза 1: Создание утилит (Приоритет: ВЫСОКИЙ)

#### 1.1. Создать `utils/user_helpers.py`
```python
async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    """Получить пользователя по telegram_id"""
    
async def get_user_info(telegram_id: int) -> tuple[str, str]:
    """Вернуть (role, name) для пользователя"""
    
async def return_to_menu(message_or_callback, state: FSMContext):
    """Очистить состояние и вернуться в главное меню"""
```

#### 1.2. Создать `utils/decorators.py`
```python
def require_role(*roles):
    """Декоратор для проверки роли"""
    
def with_error_handler(func):
    """Обёртка с обработкой ошибок"""
```

---

### Фаза 2: Рефакторинг handlers/auth_phone.py (Приоритет: КРИТИЧНЫЙ)

**Цель:** Убрать дублирование меню

**Действия:**
1. Удалить дублированную логику меню из `cmd_start()`
2. Использовать `show_main_menu()` из menu.py
3. Сохранить только логику deep links

**До:**
```python
if user.role == "admin":
    keyboard = InlineKeyboardMarkup(...)  # 20 строк
```

**После:**
```python
from handlers.menu import show_main_menu
await show_main_menu(message, user.role, user.name)
```

---

### Фаза 3: Рефакторинг handlers/applicant.py (Приоритет: ВЫСОКИЙ)

**Цель:** Убрать дублирование кода возврата в меню

**Действия:**
1. Заменить все блоки `/cancel` на вызов `return_to_menu()`
2. Использовать хелпер `get_user_info()`

**До (5 повторений):**
```python
if message.text and message.text.lower() in ['/cancel', 'отмена']:
    await state.clear()
    from handlers.menu import show_main_menu
    user_telegram_id = message.from_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )
        user = result.scalar_one_or_none()
        role = user.role if user else "guest"
        name = user.name if user else "Гость"
    
    await show_main_menu(message, role, name)
    return
```

**После:**
```python
if message.text and message.text.lower() in ['/cancel', 'отмена']:
    await return_to_menu(message, state)
    return
```

**Экономия:** ~40 строк → 2 строки (×5 мест = 190 строк сокращения)

---

### Фаза 4: Организация служебных скриптов (Приоритет: СРЕДНИЙ)

**Действия:**
1. Создать директорию `scripts/`
2. Разделить на подпапки:
   - `scripts/admin/` - управление админами
   - `scripts/db/` - работа с БД
   - `scripts/tests/` - тестовые скрипты
   - `scripts/debug/` - отладочные утилиты
3. Создать `scripts/README.md` с описанием

**Перемещение:**
```
create_admin.py → scripts/admin/create_admin.py
quick_reset.py → scripts/db/reset_database.py
test_*.py → scripts/tests/
check_*.py → scripts/debug/
```

---

### Фаза 5: Улучшение обработки ошибок (Приоритет: СРЕДНИЙ)

**Действия:**
1. Создать `utils/errors.py` с кастомными исключениями
2. Добавить централизованный error handler в `bot/main.py`
3. Логирование в файл с ротацией

---

### Фаза 6: Документация (Приоритет: НИЗКИЙ)

**Действия:**
1. Обновить TECHNICAL.md с новыми утилитами
2. Создать ARCHITECTURE.md с диаграммами
3. Добавить docstrings к новым функциям

---

## 📊 МЕТРИКИ УЛУЧШЕНИЯ

### До рефакторинга:
- **Строк кода:** ~2500
- **Дублирование:** ~15% (370 строк)
- **Цикличность импортов:** 8 мест
- **Файлов в корне:** 40+

### После рефакторинга:
- **Строк кода:** ~2150 (-14%)
- **Дублирование:** <3%
- **Цикличность импортов:** 0
- **Файлов в корне:** ~15 (только основные)

---

## ⚡ ПОРЯДОК ВЫПОЛНЕНИЯ

### Сегодня (День 1):
1. ✅ Создать бэкап
2. ⬜ Создать `utils/user_helpers.py`
3. ⬜ Рефакторинг `handlers/auth_phone.py`
4. ⬜ Тестирование меню
5. ⬜ Запуск бота - проверка стабильности

### День 2:
6. ⬜ Создать `utils/decorators.py`
7. ⬜ Рефакторинг `handlers/applicant.py`
8. ⬜ Полное тестирование флоу подачи заявки

### День 3:
9. ⬜ Организация `scripts/`
10. ⬜ Улучшение error handling
11. ⬜ Обновление документации

---

## 🚨 РИСКИ И МИТИГАЦИЯ

### Риск 1: Поломка существующего функционала
**Митигация:**
- ✅ Бэкап создан
- Тестирование после каждого изменения
- Коммиты после каждой фазы

### Риск 2: Несовместимость с существующими данными
**Митигация:**
- Не меняем структуру БД
- Только рефакторинг кода, не данных

### Риск 3: Конфликты при запущенном боте
**Митигация:**
- Останавливать бот перед изменениями
- Проверять отсутствие процессов `python.exe`

---

## 📝 КОНТРОЛЬНЫЙ ЧЕКЛИСТ

### После каждой фазы:
- [ ] Код работает без ошибок
- [ ] Бот запускается
- [ ] Меню отображается корректно
- [ ] Навигация работает
- [ ] Создание заявки работает
- [ ] Утверждение заявки работает
- [ ] Все тесты проходят

---

## 🎓 ВЫВОДЫ

Основная проблема - **дублирование логики меню** в двух местах:
1. `handlers/menu.py` (новая правильная версия)
2. `handlers/auth_phone.py` (старая версия в `/start`)

Это причина "прыгающих" кнопок - бот показывает то одно меню, то другое.

**Решение:** Убрать дублирование, использовать единый источник правды (`show_main_menu()`).

---

**Время выполнения:** 6-8 часов разработки  
**Сложность:** Средняя  
**Приоритет:** КРИТИЧНО (блокирует нормальное использование)
