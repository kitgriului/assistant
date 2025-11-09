# Руководство по использованию улучшенного кода GuardBot

## Быстрый старт

### Настройка окружения

1. **Создайте файл `.env` в корне проекта:**

```env
# Обязательные параметры
BOT_TOKEN=your_telegram_bot_token_here

# Опциональные параметры (значения по умолчанию показаны)
DB_URL=sqlite+aiosqlite:///./guardbot.db
LOG_LEVEL=INFO
MAX_PHOTO_SIZE_MB=10
PASS_VALIDITY_DAYS=7
DEBUG=false
```

2. **Установите зависимости:**

```bash
pip install -r requirements.txt
```

3. **Запустите бота:**

```bash
python -m bot.main
```

---

## Использование новых утилит

### 1. Работа с пользователями (utils/user_helpers.py)

#### Получить или создать пользователя

```python
from utils.user_helpers import get_or_create_user

# В хэндлере
user = await get_or_create_user(
    telegram_id=message.from_user.id,
    name=message.from_user.full_name,
    phone_number=message.contact.phone_number  # опционально
)
```

#### Проверка прав доступа

```python
from utils.user_helpers import check_user_access
from utils.constants import Role

# Проверить, что пользователь админ или охранник
has_access, user = await check_user_access(
    message.from_user.id,
    [Role.ADMIN.value, Role.GUARD.value]
)

if not has_access:
    await message.answer("❌ Недостаточно прав")
    return

# Продолжаем с разрешённым доступом
```

#### Обновить активность пользователя

```python
from utils.user_helpers import update_user_activity

# Обновить timestamp последней активности
await update_user_activity(message.from_user.id)
```

#### Изменить роль пользователя

```python
from utils.user_helpers import set_user_role
from utils.constants import Role

success = await set_user_role(
    telegram_id=target_user_id,
    new_role=Role.GUARD.value
)

if success:
    await message.answer("✅ Роль успешно изменена")
```

---

### 2. Работа с заявками (utils/request_helpers.py)

#### Создать новую заявку

```python
from utils.request_helpers import create_request
from utils.constants import PassType

request = await create_request(
    applicant_id=user.id,
    name="Иван Иванов",
    purpose="Встреча с директором",
    pass_type=PassType.PEDESTRIAN.value,
    datetime_str="01.12.2025 14:00",
    photo="/path/to/photo.jpg"
)

await message.answer(f"✅ Заявка #{request.id} создана")
```

#### Утвердить заявку

```python
from utils.request_helpers import approve_request

request = await approve_request(
    request_id=request_id,
    processed_by_id=admin.id,
    validity_days=3  # опционально, по умолчанию из config
)

if request:
    # Отправить QR код заявителю
    qr_image = generate_qr_image(request.qr_code)
    await bot.send_photo(...)
```

#### Отклонить заявку

```python
from utils.request_helpers import reject_request

request = await reject_request(
    request_id=request_id,
    processed_by_id=admin.id,
    reason="Неполный пакет документов"
)

if request:
    # Уведомить заявителя
    await bot.send_message(
        request.applicant.telegram_id,
        f"❌ Ваша заявка отклонена\nПричина: {request.rejection_reason}"
    )
```

#### Получить список ожидающих заявок

```python
from utils.request_helpers import get_pending_requests

pending = await get_pending_requests()

for request in pending:
    # Показать каждую заявку админу/охраннику
    await send_request_card(message, request)
```

#### Получить активные пропуска

```python
from utils.request_helpers import get_active_passes

active = await get_active_passes()

for pass_request in active:
    # Показать активный пропуск
    await message.answer(
        f"✅ Пропуск #{pass_request.id}\n"
        f"Имя: {pass_request.name}\n"
        f"Действует до: {pass_request.valid_until}"
    )
```

#### Найти заявку по QR коду

```python
from utils.request_helpers import get_request_by_qr

request = await get_request_by_qr(scanned_qr_code)

if not request:
    await message.answer("❌ QR код не найден")
elif not request.is_active:
    await message.answer("❌ Пропуск недействителен")
else:
    await message.answer("✅ Пропуск действителен. Проход разрешён.")
```

---

### 3. Работа с медиафайлами (utils/media.py)

#### Сохранить фото

```python
from utils.media import save_photo, FileSizeError

try:
    # Сохранить самое большое фото
    photo_path = await save_photo(
        bot=message.bot,
        photo=message.photo[-1],
        prefix="request_photo_"
    )
    
    # Сохранить путь в БД
    request.photo = photo_path
    
except FileSizeError as e:
    await message.answer(f"❌ Файл слишком большой: {e}")
except Exception as e:
    await message.answer("❌ Ошибка при загрузке файла")
```

#### Сохранить документ с проверкой типа

```python
from utils.media import save_document, FileTypeError

try:
    doc_path = await save_document(
        bot=message.bot,
        document=message.document,
        prefix="patrol_doc_",
        allowed_extensions=['.pdf', '.jpg', '.png']
    )
    
except FileTypeError as e:
    await message.answer(f"❌ Недопустимый тип файла: {e}")
```

#### Универсальное сохранение файла

```python
from utils.media import save_file

# Работает и с фото, и с документами
if message.photo:
    file_path = await save_file(message.bot, message.photo[-1])
elif message.document:
    file_path = await save_file(message.bot, message.document)
```

---

### 4. Валидация данных (utils/validators.py)

#### Валидация номера телефона

```python
from utils.validators import validate_phone_number

is_valid, error = validate_phone_number(user_input)

if not is_valid:
    await message.answer(f"❌ {error}")
    return

# Продолжаем с валидным номером
```

#### Валидация номера машины

```python
from utils.validators import validate_car_number

is_valid, error = validate_car_number(user_input)

if not is_valid:
    await message.answer(f"❌ {error}")
    await message.answer("Пример правильного формата: А123БВ777")
    return
```

#### Валидация имени

```python
from utils.validators import validate_name

is_valid, error = validate_name(user_input)

if not is_valid:
    await message.answer(f"❌ {error}")
    return
```

#### Валидация даты/времени

```python
from utils.validators import validate_datetime_str

is_valid, error = validate_datetime_str(user_input)

if not is_valid:
    await message.answer(f"❌ {error}")
    await message.answer("Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ")
    return
```

#### Санитизация текста

```python
from utils.validators import sanitize_text

# Очистить и обрезать текст
safe_text = sanitize_text(user_input, max_length=500)

# Использовать в базе данных или для отображения
request.purpose = safe_text
```

---

## Примеры интеграции в хэндлеры

### Пример: Создание заявки

```python
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.user_helpers import get_or_create_user
from utils.request_helpers import create_request
from utils.validators import validate_name, validate_purpose
from utils.media import save_photo
from utils.constants import PassType
from states.applicant import ApplicantStates

router = Router()

@router.message(ApplicantStates.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка загруженного фото документа."""
    
    # Получить данные из state
    data = await state.get_data()
    
    # Валидация сохранённых данных
    is_valid, error = validate_name(data['name'])
    if not is_valid:
        await message.answer(f"❌ Ошибка в имени: {error}")
        await state.clear()
        return
    
    is_valid, error = validate_purpose(data['purpose'])
    if not is_valid:
        await message.answer(f"❌ Ошибка в цели: {error}")
        await state.clear()
        return
    
    # Сохранить фото
    try:
        photo_path = await save_photo(message.bot, message.photo[-1])
    except Exception as e:
        await message.answer("❌ Ошибка при сохранении фото")
        return
    
    # Получить или создать пользователя
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        name=message.from_user.full_name
    )
    
    # Создать заявку
    request = await create_request(
        applicant_id=user.id,
        name=data['name'],
        purpose=data['purpose'],
        pass_type=data.get('pass_type', PassType.PEDESTRIAN.value),
        datetime_str=data.get('datetime'),
        photo=photo_path,
        car_number=data.get('car_number')
    )
    
    # Очистить state
    await state.clear()
    
    # Отправить подтверждение
    await message.answer(
        f"✅ Заявка #{request.id} успешно создана!\n\n"
        f"Имя: {request.name}\n"
        f"Цель: {request.purpose}\n"
        f"Тип: {request.pass_type}\n\n"
        f"Ожидайте утверждения администратором."
    )
```

### Пример: Утверждение заявки

```python
@router.callback_query(F.data.startswith("approve_"))
async def approve_request_callback(callback: CallbackQuery):
    """Утверждение заявки администратором."""
    
    # Извлечь ID заявки
    request_id = int(callback.data.split("_")[1])
    
    # Проверить права доступа
    has_access, admin = await check_user_access(
        callback.from_user.id,
        [Role.ADMIN.value, Role.GUARD.value]
    )
    
    if not has_access:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Утвердить заявку
    request = await approve_request(
        request_id=request_id,
        processed_by_id=admin.id,
        validity_days=7
    )
    
    if not request:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    # Отправить QR код заявителю
    from utils.qr import generate_qr_bytes
    from aiogram.types import BufferedInputFile
    
    qr_bytes = generate_qr_bytes(request.qr_code)
    qr_file = BufferedInputFile(qr_bytes.read(), filename="qr.png")
    
    await callback.bot.send_photo(
        chat_id=request.applicant.telegram_id,
        photo=qr_file,
        caption=(
            f"✅ Ваша заявка #{request.id} утверждена!\n\n"
            f"Действителен до: {request.valid_until.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Покажите этот QR код на входе."
        )
    )
    
    # Обновить сообщение админа
    await callback.message.edit_text(
        f"✅ Заявка #{request.id} утверждена\n"
        f"QR код отправлен заявителю"
    )
    await callback.answer("✅ Готово")
```

---

## Использование свойств моделей

### User модель

```python
user = await get_user_by_telegram_id(telegram_id)

# Проверка ролей
if user.is_admin:
    # Показать админское меню
    pass

if user.is_guard:
    # Показать меню охранника
    pass

if user.is_guest:
    # Показать меню гостя
    pass
```

### Request модель

```python
request = await get_request_by_id(request_id)

# Проверка статуса
if request.is_pending:
    # Показать кнопки утверждения/отклонения
    pass

if request.is_approved:
    # Показать QR код
    pass

if request.is_active:
    # Пропуск активен и действителен
    # Разрешить проход
    pass
```

### PatrolEvent модель

```python
patrol = await get_patrol_event(event_id)

if patrol.is_in_progress:
    # Обход ещё не завершён
    await message.answer("⏳ Обход в процессе...")

if patrol.is_completed:
    # Показать статистику
    duration = patrol.duration_minutes
    await message.answer(f"✅ Обход завершён за {duration} минут")
```

---

## Настройка логирования

### В коде

```python
import logging

logger = logging.getLogger(__name__)

# Использование
logger.debug("Детальная информация для отладки")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.exception("Ошибка с трейсбеком")
```

### Через переменную окружения

```env
# В .env файле
LOG_LEVEL=DEBUG  # для разработки
LOG_LEVEL=INFO   # для продакшена
LOG_LEVEL=WARNING # минимальные логи
```

---

## Best Practices

### 1. Всегда используйте валидацию

```python
# ❌ Плохо
request = await create_request(
    name=user_input,  # Не проверено
    purpose=user_input2
)

# ✅ Хорошо
is_valid, error = validate_name(user_input)
if not is_valid:
    await message.answer(f"❌ {error}")
    return

request = await create_request(
    name=user_input,
    purpose=user_input2
)
```

### 2. Используйте type hints

```python
# ✅ Хорошо
async def process_request(request_id: int, user_id: int) -> Optional[Request]:
    """..."""
    pass
```

### 3. Обрабатывайте ошибки

```python
# ✅ Хорошо
try:
    photo_path = await save_photo(bot, photo)
except FileSizeError as e:
    await message.answer("Файл слишком большой")
except Exception as e:
    logger.exception("Unexpected error saving photo")
    await message.answer("Произошла ошибка")
```

### 4. Используйте константы вместо строк

```python
# ❌ Плохо
if user.role == "admin":
    pass

# ✅ Хорошо
from utils.constants import Role

if user.role == Role.ADMIN.value:
    pass
```

### 5. Централизуйте бизнес-логику

```python
# ❌ Плохо - логика в хэндлере
@router.callback_query(...)
async def handler(callback):
    async with get_session() as session:
        request = await session.execute(...)
        request.status = "approved"
        request.qr_code = generate_random_code()
        # ...много кода...

# ✅ Хорошо - используйте helper
@router.callback_query(...)
async def handler(callback):
    request = await approve_request(request_id, admin_id)
    # Чистый и понятный код
```

---

## Миграция существующего кода

Если у вас есть старые хэндлеры, постепенно мигрируйте их:

1. **Замените прямые SQL запросы на helper функции**
2. **Добавьте валидацию пользовательского ввода**
3. **Используйте новые утилиты для работы с файлами**
4. **Добавьте обработку ошибок**
5. **Документируйте функции**

Пример миграции:

```python
# Старый код
@router.message(...)
async def old_handler(message: Message):
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != "admin":
            await message.answer("Access denied")
            return
        # ...

# Новый код
@router.message(...)
async def new_handler(message: Message):
    has_access, user = await check_user_access(
        message.from_user.id,
        [Role.ADMIN.value]
    )
    if not has_access:
        await message.answer("❌ Access denied")
        return
    # ...
```

---

Это руководство покрывает основные сценарии использования улучшенного кода. Для деталей смотрите документацию в самих модулях (docstrings).
