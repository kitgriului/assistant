"""
Inline календарь для выбора даты и времени
"""
import calendar
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def generate_calendar(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """Генерирует inline клавиатуру календаря для выбора даты"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    # Создаём календарь
    cal = calendar.monthcalendar(year, month)
    
    # Название месяца и года
    month_name = calendar.month_name[month]
    
    keyboard = []
    
    # Заголовок: Месяц Год
    keyboard.append([
        InlineKeyboardButton(text="<<", callback_data=f"cal_prev_{year}_{month}"),
        InlineKeyboardButton(text=f"{month_name} {year}", callback_data="cal_ignore"),
        InlineKeyboardButton(text=">>", callback_data=f"cal_next_{year}_{month}")
    ])
    
    # Дни недели
    keyboard.append([
        InlineKeyboardButton(text=day, callback_data="cal_ignore") 
        for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    ])
    
    # Даты
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                # Пустая ячейка
                row.append(InlineKeyboardButton(text=" ", callback_data="cal_ignore"))
            else:
                # Проверяем, не прошедшая ли это дата
                date = datetime(year, month, day)
                if date.date() < now.date():
                    # Прошедшая дата - неактивна
                    row.append(InlineKeyboardButton(text=f"·{day}·", callback_data="cal_ignore"))
                else:
                    # Активная дата
                    row.append(InlineKeyboardButton(
                        text=str(day), 
                        callback_data=f"cal_day_{year}_{month}_{day}"
                    ))
        keyboard.append(row)
    
    # Кнопка отмены
    keyboard.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def generate_time_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора времени с интервалом 30 минут"""
    keyboard = []
    
    # Часы работы: с 8:00 до 20:00
    for hour in range(8, 21):
        row = []
        for minute in [0, 30]:
            if hour == 20 and minute == 30:
                # Не добавляем 20:30
                break
            time_str = f"{hour:02d}:{minute:02d}"
            row.append(InlineKeyboardButton(
                text=time_str,
                callback_data=f"time_{hour:02d}_{minute:02d}"
            ))
        if row:
            keyboard.append(row)
    
    # Кнопка отмены
    keyboard.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def format_datetime(year: int, month: int, day: int, hour: int, minute: int) -> str:
    """Форматирует дату и время в строку для сохранения"""
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
