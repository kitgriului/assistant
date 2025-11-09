# 🔧 Дополнение к технической документации

## FSM States (Finite State Machine)

### ApplicantStates

```python
class ApplicantStates(StatesGroup):
    pass_type = State()       # Выбор типа пропуска (пешеход/авто)
    purpose = State()         # Выбор цели визита (inline buttons)
    custom_purpose = State()  # Ввод своей цели (text input)
    datetime = State()        # Хранение выбранной даты
    photo = State()           # Загрузка фото документа
    car_number = State()      # Ввод номера авто (только для vehicle)
```

**Поток состояний:**
```
pass_type → purpose → [custom_purpose если "Другое"] → calendar → time → 
[car_number если vehicle] → photo → создание заявки
```

### AuthStates

```python
class AuthStates(StatesGroup):
    waiting_for_name = State()  # Ожидание ввода ФИО при регистрации
```

## Callback Data API

### Формат callback_data

Все callback данные имеют префиксную структуру для маршрутизации:

#### Навигация
```python
"main_menu"           # Возврат в главное меню
"menu_pending"        # Переход к заявкам
"menu_users"          # Управление пользователями
"menu_request"        # Начать подачу заявки
```

#### Тип пропуска
```python
"passtype_pedestrian"  # Выбран пешеход
"passtype_vehicle"     # Выбран автомобиль
```

#### Цель визита
```python
# Для пешехода
"purpose_meeting"      # Деловая встреча
"purpose_pickup"       # Получение груза
"purpose_delivery"     # Доставка
"purpose_custom"       # Другое (требует ввода)

# Для автомобиля
"purpose_loading"      # Погрузка/разгрузка
"purpose_delivery"     # Доставка
"purpose_business"     # Служебная поездка
"purpose_custom"       # Другое
```

#### Календарь
```python
"cal_ignore"                    # Неактивная ячейка
"cal_prev_{year}_{month}"       # Предыдущий месяц
"cal_next_{year}_{month}"       # Следующий месяц
"cal_day_{year}_{month}_{day}"  # Выбор даты
```

#### Время
```python
"time_{hour}_{minute}"  # Например: "time_09_30" для 09:30
```

#### Управление заявками
```python
"approve_{request_id}"     # Утвердить заявку
"reject_{request_id}"      # Отклонить заявку
"view_photo_{request_id}"  # Просмотр фото
```

#### Управление пользователями
```python
"set_role_{user_id}_{role}"     # Изменить роль (role: admin/guard/guest)
"toggle_block_{user_id}"        # Заблокировать/разблокировать
```

#### Общие
```python
"cancel_request"  # Отмена текущего процесса
```

## Утилиты

### QR Code Generation (`utils/qr.py`)

```python
def generate_qr_bytes(data: str) -> BytesIO:
    """
    Генерирует QR-код в BytesIO объект
    
    Args:
        data: Строка для кодирования (обычно "request:{id}:{uuid}")
    
    Returns:
        BytesIO: Изображение QR-кода в формате PNG
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
```

**Формат данных в QR:**
```
request:{request_id}:{uuid}
```
Например: `request:42:a1b2c3d4-e5f6-7890-abcd-ef1234567890`

### Media Handling (`utils/media.py`)

```python
async def save_file(bot, file_obj, prefix="") -> str:
    """
    Сохраняет файл из Telegram в локальную директорию
    
    Args:
        bot: Bot instance
        file_obj: Telegram file object (PhotoSize, Document, etc.)
        prefix: Префикс для имени файла
    
    Returns:
        str: Путь к сохраненному файлу
    """
    file = await bot.get_file(file_obj.file_id)
    file_path = file.file_path
    
    # Генерация уникального имени
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = file_path.split('.')[-1]
    filename = f"{prefix}{timestamp}.{ext}"
    
    local_path = f"data/media/{filename}"
    await bot.download_file(file_path, local_path)
    
    return local_path
```

**Структура хранения:**
```
data/
  media/
    applicant_20251101_143052.jpg
    applicant_20251101_143125.jpg
    patrol_20251101_150000.jpg
```

### Calendar Generator (`utils/calendar_kb.py`)

```python
def generate_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    """
    Генерирует inline-календарь на указанный месяц
    
    Args:
        year: Год (2025)
        month: Месяц (1-12)
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с календарем
    
    Features:
        - Блокировка прошлых дат
        - Навигация << >>
        - Отображение дней недели
        - Кнопка отмены
    """
```

**Пример сгенерированного календаря:**
```
    Ноябрь 2025      <<  >>
Пн  Вт  Ср  Чт  Пт  Сб  Вс
                1   2   3
4   5   6   7   8   9   10
11  12  13  14  15  16  17
18  19  20  21  22  23  24
25  26  27  28  29  30
         [❌ Отменить]
```

```python
def generate_time_keyboard() -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру выбора времени
    
    Диапазон: 8:00 - 20:00
    Шаг: 30 минут
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с временем
    """
```

**Пример:**
```
8:00   8:30
9:00   9:30
10:00  10:30
...
19:00  19:30
20:00
[❌ Отменить]
```

## База данных

### Инициализация

```python
# database/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None

async def init_db(db_url: str):
    """Инициализация БД и создание таблиц"""
    global _engine, _SessionLocal
    _engine = create_async_engine(db_url, echo=False)
    _SessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def get_session():
    """Контекстный менеджер для сессий БД"""
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_db first.")
    return _SessionLocal()
```

### Миграции

Для безопасного изменения структуры БД используется `migrate_db.py`:

```python
# migrate_db.py
import sqlite3

def migrate():
    conn = sqlite3.connect('guardbot.db')
    cursor = conn.cursor()
    
    # Проверка существующих колонок
    cursor.execute("PRAGMA table_info(requests)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Добавление новых колонок если их нет
    if 'pass_type' not in columns:
        cursor.execute("ALTER TABLE requests ADD COLUMN pass_type TEXT DEFAULT 'pedestrian'")
    
    if 'car_number' not in columns:
        cursor.execute("ALTER TABLE requests ADD COLUMN car_number TEXT")
    
    conn.commit()
    conn.close()
```

**Важно:** Никогда не удалять базу на проде! Только миграции!

### Индексы (TODO для продакшена)

```sql
-- Часто используемые поля
CREATE INDEX idx_telegram_id ON users(telegram_id);
CREATE INDEX idx_phone_number ON users(phone_number);
CREATE INDEX idx_request_status ON requests(status);
CREATE INDEX idx_request_created ON requests(created_at);
CREATE INDEX idx_request_applicant ON requests(applicant_id);
```

## Performance Considerations

### Database Queries

**❌ Плохо (N+1 проблема):**
```python
requests = await session.execute(select(Request))
for req in requests.scalars():
    user = await session.get(User, req.applicant_id)  # N запросов
```

**✅ Хорошо (Eager loading):**
```python
from sqlalchemy.orm import selectinload

requests = await session.execute(
    select(Request)
    .options(selectinload(Request.applicant))
    .where(Request.status == 'pending')
)
```

### Caching

**TODO:** Добавить кеширование для:
- Часто запрашиваемых пользователей
- Списка активных заявок
- Статистики

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_user_role(telegram_id: int) -> str:
    # Cache на 5 минут
    pass
```

## Логирование

### Текущая реализация

```python
import logging

logger = logging.getLogger(__name__)

# В обработчиках
logger.info(f"User {telegram_id} created request {request_id}")
logger.error(f"Failed to approve request: {e}")
```

### Рекомендации для продакшена

```python
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_data)

# Настройка
handler = logging.FileHandler('guardbot.log')
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
```

## Безопасность

### Input Validation

**Текущее состояние:**
```python
if not purpose or len(purpose) < 5:
    await message.reply("❌ Минимум 5 символов")
```

**Рекомендуется (Pydantic):**
```python
from pydantic import BaseModel, validator, constr

class RequestInput(BaseModel):
    purpose: constr(min_length=5, max_length=512)
    pass_type: Literal['pedestrian', 'vehicle']
    car_number: Optional[constr(pattern=r'^[A-ZА-Я]\d{3}[A-ZА-Я]{2}\d{2,3}$')]
    
    @validator('purpose')
    def sanitize_purpose(cls, v):
        # XSS protection
        return v.replace('<', '').replace('>', '')
```

### Rate Limiting

**TODO:** Добавить ограничение запросов

```python
from collections import defaultdict
from datetime import datetime, timedelta

request_counts = defaultdict(list)

async def rate_limit(telegram_id: int, max_requests=10, window=60):
    now = datetime.now()
    cutoff = now - timedelta(seconds=window)
    
    # Очистка старых запросов
    request_counts[telegram_id] = [
        t for t in request_counts[telegram_id] if t > cutoff
    ]
    
    if len(request_counts[telegram_id]) >= max_requests:
        return False  # Превышен лимит
    
    request_counts[telegram_id].append(now)
    return True
```

## Testing

### Unit Tests

```python
# tests/test_calendar.py
import pytest
from utils.calendar_kb import generate_calendar
import datetime

def test_calendar_blocks_past_dates():
    today = datetime.date.today()
    calendar = generate_calendar(today.year, today.month)
    
    # Проверяем, что прошлые даты неактивны
    # ...
```

### Integration Tests

```python
# tests/test_request_flow.py
import pytest
from aiogram.fsm.context import FSMContext

@pytest.mark.asyncio
async def test_full_request_flow():
    # Симуляция полного процесса создания заявки
    # 1. Выбор типа
    # 2. Цель
    # 3. Дата
    # 4. Время
    # 5. Фото
    # 6. Проверка в БД
    pass
```

---

*Техническая документация обновлена: 1 ноября 2025*
