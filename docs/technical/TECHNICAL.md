# 🔧 Техническая документация GuardBot

**Версия:** 0.8 Alpha  
**Дата обновления:** 1 ноября 2025  
**Python:** 3.12  
**Фреймворк:** aiogram 3.x

## 📚 Оглавление

1. [Архитектура](#архитектура)
2. [Модели данных](#модели-данных)
3. [Обработчики](#обработчики)
4. [FSM States](#fsm-states)
5. [Утилиты](#утилиты)
6. [База данных](#база-данных)
7. [API Callbacks](#api-callbacks)

## 🏗️ Архитектура

### Router-Based Architecture (aiogram 3.x)

Проект использует паттерн Router для модульной организации обработчиков:

```python
# handlers/__init__.py
from .auth_phone import router as auth_router
from .menu import router as menu_router
from .admin import router as admin_router
from .guard import router as guard_router  
from .applicant import register_applicant_handlers

def register_handlers(dp: Dispatcher):
    dp.include_router(auth_router)      # Приоритет: аутентификация
    dp.include_router(menu_router)      # Навигация
    dp.include_router(admin_router)     # Админ-панель
    # ... остальные роутеры
```

**Преимущества:**
- Изолированная логика каждого модуля
- Легкое добавление новых функций
- Четкая иерархия обработчиков
- Простое тестирование

### Async Architecture

Все операции выполняются асинхронно:

```python
# Асинхронная работа с БД
async with get_session() as session:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

# Асинхронная отправка сообщений
await message.answer("Text", reply_markup=keyboard)
await callback.message.edit_text("Updated text")
```

## 📊 Модели данных

### User Model

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(32), default="guest")  # guest, guard, admin
    is_blocked = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=lambda: datetime.datetime.utcnow())
    last_activity = Column(DateTime, nullable=True)
```

**Роли:**
- `guest` - обычный пользователь (заявитель)
- `guard` - охранник (утверждает заявки)
- `admin` - администратор (все права + управление пользователями)

### Request Model

```python
class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True)
    applicant_id = Column(Integer, ForeignKey("users.id"))
    
    # Данные заявки
    name = Column(String(255), nullable=False)          # ФИО заявителя
    pass_type = Column(String(32), default="pedestrian") # pedestrian / vehicle
    purpose = Column(String(512), nullable=False)        # Цель визита
    datetime = Column(String(64), nullable=True)         # Дата и время
    photo = Column(String(1024), nullable=True)          # Путь к фото
    car_number = Column(String(64), nullable=True)       # Номер авто (для vehicle)
    
    # Статус
    status = Column(String(32), default="pending")       # pending/approved/rejected/used/expired
    qr_code = Column(String(256), nullable=True)         # UUID для QR
    
    # Обработка
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=lambda: datetime.datetime.utcnow())
    valid_until = Column(DateTime, nullable=True)
```

**Статусы заявки:**
- `pending` - ожидает утверждения
- `approved` - утверждена
- `rejected` - отклонена
- `used` - использована (пропуск предъявлен)
- `expired` - истекла

**Типы пропуска:**
- `pedestrian` - пешеход
- `vehicle` - автомобиль

## 🎯 Обработчики

### 1. Authentication Handler (`handlers/auth_phone.py`)

**Основные функции:**

```python
@router.message(Command("start"))
async def cmd_start(message: types.Message)
```
- Точка входа в бота
- Проверка регистрации пользователя
- Показ role-based меню

```python
@router.message(F.contact)
async def process_contact(message: types.Message, state: FSMContext)
```
- Обработка Telegram contact (номер телефона)
- Проверка существующего пользователя
- Запрос ФИО для нового пользователя

```python
@router.message(AuthStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext)
```
- Сохранение ФИО нового пользователя
- Создание записи в БД с ролью `guest`
- Показ главного меню

### 2. Menu Handler (`handlers/menu.py`)

**Основные функции:**

```python
async def show_main_menu(message: types.Message, role: str)
```
- Генерация role-based главного меню
- Разные кнопки для admin/guard/guest

```python
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery)
```
- Возврат в главное меню из любого раздела

```python
@router.callback_query(F.data == "menu_request")
async def menu_request(callback: CallbackQuery, state: FSMContext)
```
- Запуск процесса подачи заявки
- Показ выбора типа пропуска

### 3. Applicant Handler (`handlers/applicant.py`)

**Процесс подачи заявки:**

```python
@router.message(Command("request"))
async def start_request(message: types.Message, state: FSMContext)
    
    req_id = int(args[1])
    async with get_session() as session:
        req = await session.get(DBRequest, req_id)
        if req and req.status == "pending":
            req.status = "approved"
            await session.commit()
            # Генерация QR кода
```

#### 3. Client Handler (`handlers/client.py`)

**Основные функции:**
- `cmd_list()` - список заявок
- `cmd_export()` - экспорт данных

### Модели базы данных

#### Request (Заявки)
```python
class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)      # ФИО заявителя
    purpose = Column(String(512), nullable=False)   # Цель визита
    datetime = Column(String(64), nullable=True)    # Дата/время
    photo = Column(String(1024), nullable=True)     # Путь к фото
    status = Column(String(32), default="pending")  # Статус заявки
```

#### Patrol (Патрулирование)
```python
class Patrol(Base):
    __tablename__ = "patrols"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    code = Column(String(256), nullable=True)       # QR код или координаты
    photo = Column(String(1024), nullable=True)     # Фото фиксации
```

#### User (Пользователи)
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    role = Column(String(32), default="applicant")  # Роль пользователя
    name = Column(String(255), nullable=True)       # Имя пользователя
```

### Утилиты

#### QR Generator (`utils/qr.py`)
```python
def generate_qr_bytes(data: str) -> BytesIO:
    """Генерация QR кода в памяти"""
    img = qrcode.make(data)
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio
```

#### Media Handler (`utils/media.py`)
```python
async def save_file(bot: Bot, photo: PhotoSize, prefix: str) -> str:
    """Сохранение медиафайла на диск"""
    file = await bot.get_file(photo.file_id)
    filename = f"{prefix}{photo.file_id}_{int(time.time())}.jpg"
    # ... логика сохранения
```

## Конфигурация

### Настройки бота (`bot/config.py`)
```python
@dataclass
class Settings:
    bot_token: str          # Токен Telegram бота
    db_url: str            # URL базы данных
    media_path: str        # Путь для медиафайлов
    export_path: str       # Путь для экспорта
```

### Переменные окружения
```bash
BOT_TOKEN=8213953486:AAHv4BjxfzaRYl52RQeQy_pVshYkBrY4pLM
DB_URL=sqlite+aiosqlite:///./guardbot.db
```

## Workflow диаграммы

### Подача заявки
```
Пользователь -> /request -> ApplicantStates.name
     ↓
   Ввод ФИО -> ApplicantStates.purpose
     ↓
   Цель визита -> ApplicantStates.datetime
     ↓
   Дата/время -> ApplicantStates.photo
     ↓
   Фото документа -> Сохранение в БД -> QR код
```

### Одобрение заявки
```
Админ -> /approve ID -> Поиск в БД
     ↓
   Найдена? -> Статус pending?
     ↓             ↓
    НЕТ          ДА -> Смена статуса -> QR код
     ↓
   Ошибка
```

### Патрулирование
```
Охранник -> /patrol -> GuardStates.check_in
     ↓
   Координаты/QR -> GuardStates.photo
     ↓
   Фото -> Сохранение в БД
```

## API Reference

### Команды бота

#### `/start`
- **Роль**: Все
- **Описание**: Приветствие и справка
- **Ответ**: Текстовое сообщение

#### `/request`
- **Роль**: Applicant
- **Описание**: Начало подачи заявки
- **FSM**: Переход в ApplicantStates.name
- **Результат**: QR код после завершения

#### `/approve <ID>`
- **Роль**: Guard
- **Параметры**: ID заявки (число)
- **Описание**: Одобрение заявки
- **Результат**: QR код или сообщение об ошибке

#### `/patrol`
- **Роль**: Guard
- **Описание**: Начало патрулирования
- **FSM**: Переход в GuardStates.check_in

#### `/list_requests`
- **Роль**: Client
- **Описание**: Список всех заявок
- **Результат**: Текстовый список

#### `/export_requests`
- **Роль**: Client
- **Описание**: Экспорт данных
- **Результат**: Файл с данными

### Форматы данных

#### QR код заявки
```
request:123
```
Где 123 - ID заявки в базе данных

#### Структура медиафайла
```
applicant_AgACAgIAAxkBAAMM...._1761160434.jpg
patrol_AgACAgIAAxkBAANi...._1761161162.jpg
```

Формат: `{prefix}_{file_id}_{timestamp}.jpg`

## Безопасность

### Обработка ошибок
- Все SQL запросы выполняются через SQLAlchemy ORM
- Файлы сохраняются с безопасными именами
- Входные данные валидируются

### Логирование
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"cmd_approve вызван: {message.text}")
```

## Производительность

### Асинхронность
- Все операции с БД асинхронные
- Файловые операции не блокируют основной поток
- Использование connection pooling

### Оптимизация
- Ленивая загрузка медиафайлов
- Кэширование сессий БД
- Batch операции для экспорта

## Мониторинг

### Логи
```bash
# Основные логи
tail -f guardbot.log

# Ошибки
grep -i error guardbot.log

# Команды approve
grep "cmd_approve" guardbot.log
```

### Метрики
- Количество обработанных заявок
- Время ответа команд
- Размер базы данных
- Использование дискового пространства

## Развертывание

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "bot.main"]
```

### Systemd Service
```ini
[Unit]
Description=GuardBot Telegram Bot
After=network.target

[Service]
Type=simple
User=guardbot
WorkingDirectory=/opt/guardbot
ExecStart=/opt/guardbot/.venv/bin/python -m bot.main
Restart=always

[Install]
WantedBy=multi-user.target
```

## Бэкапы

### База данных
```bash
# SQLite
cp guardbot.db guardbot.db.$(date +%Y%m%d_%H%M%S)

# PostgreSQL
pg_dump guardbot > guardbot_$(date +%Y%m%d_%H%M%S).sql
```

### Медиафайлы
```bash
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz data/media/
```

---

*Техническая документация обновлена: 22.10.2025*