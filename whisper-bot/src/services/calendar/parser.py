"""
Модуль для извлечения даты, времени и информации о встрече из текста
Использует GPT-4 для точного парсинга естественного языка
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo

from openai import OpenAI


def extract_meeting_info(client: OpenAI, text: str) -> Optional[Dict[str, Any]]:
    """
    Извлекает информацию о встрече из текста с помощью GPT-4.
    
    Args:
        client: OpenAI клиент
        text: Текст для анализа
        
    Returns:
        Dict с информацией о встрече или None если встреча не найдена
        {
            'title': str,           # Название встречи
            'date': str,            # Дата в формате YYYY-MM-DD
            'start_time': str,      # Время начала HH:MM
            'end_time': str,        # Время окончания HH:MM (опционально)
            'duration_minutes': int, # Длительность в минутах (если не указано время окончания)
            'description': str,     # Описание встречи
            'location': str,        # Место встречи (если указано)
            'participants': list,   # Участники (если указаны)
        }
    """
    
    # Текущая дата для контекста
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")
    current_weekday = datetime.now().strftime("%A")
    
    prompt = f"""
Ты помощник для извлечения информации о встречах из текста.

Текущая дата: {current_date} ({current_weekday})
Текущее время: {current_time}

Проанализируй следующий текст и извлеки информацию о встрече, если она там есть.
Если в тексте нет информации о встрече или событии с конкретной датой/временем, верни null.

Текст:
{text}

Верни JSON в следующем формате:
{{
    "title": "Название встречи",
    "date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "end_time": "HH:MM" или null,
    "duration_minutes": число или null,
    "description": "Краткое описание",
    "location": "Место встречи" или null,
    "participants": ["участник1", "участник2"] или []
}}

Правила:
1. Если указано "завтра", используй {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}
2. Если указано "послезавтра", используй {(datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")}
3. Если указан день недели без даты, выбери ближайший такой день
4. Если время не указано, используй null для start_time
5. Если длительность не указана, поставь 60 минут по умолчанию
6. Если это не встреча/событие, верни null

Верни ТОЛЬКО JSON без дополнительного текста.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник для извлечения структурированной информации о встречах. Отвечай только JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        if not result_text or result_text.strip() == "null":
            return None
            
        meeting_info = json.loads(result_text)
        
        # Валидация данных
        if not meeting_info or meeting_info == "null":
            return None
            
        if not meeting_info.get("date"):
            return None
            
        # Установка значений по умолчанию
        if not meeting_info.get("duration_minutes") and not meeting_info.get("end_time"):
            meeting_info["duration_minutes"] = 60
            
        if not meeting_info.get("title"):
            meeting_info["title"] = "Встреча"
            
        return meeting_info
        
    except Exception as e:
        print(f"Ошибка при извлечении информации о встрече: {e}")
        return None


def parse_datetime(date_str: str, time_str: str, timezone: str = "Europe/Moscow") -> datetime:
    """
    Конвертирует строковые дату и время в datetime объект с таймзоной.
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        time_str: Время в формате HH:MM
        timezone: Таймзона (по умолчанию Moscow)
        
    Returns:
        datetime объект в UTC
    """
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        tz = ZoneInfo(timezone)
        dt_local = dt.replace(tzinfo=tz)
        # Конвертируем в UTC для ICS файла
        return dt_local.astimezone(ZoneInfo('UTC'))
    except Exception as e:
        print(f"Ошибка парсинга даты/времени: {e}")
        raise


def calculate_end_time(start_dt: datetime, duration_minutes: int) -> datetime:
    """
    Вычисляет время окончания на основе времени начала и длительности.
    
    Args:
        start_dt: Время начала
        duration_minutes: Длительность в минутах
        
    Returns:
        Время окончания
    """
    return start_dt + timedelta(minutes=duration_minutes)


def format_meeting_summary(meeting_info: Dict[str, Any]) -> str:
    """
    Форматирует информацию о встрече в читаемый текст.
    
    Args:
        meeting_info: Словарь с информацией о встрече
        
    Returns:
        Отформатированный текст
    """
    lines = [
        f"📅 **{meeting_info['title']}**",
        f"",
        f"🗓 Дата: {meeting_info['date']}",
    ]
    
    if meeting_info.get('start_time'):
        lines.append(f"🕐 Время: {meeting_info['start_time']}")
        
        if meeting_info.get('end_time'):
            lines.append(f"   до {meeting_info['end_time']}")
        elif meeting_info.get('duration_minutes'):
            lines.append(f"   Длительность: {meeting_info['duration_minutes']} мин")
    
    if meeting_info.get('location'):
        lines.append(f"📍 Место: {meeting_info['location']}")
        
    if meeting_info.get('participants'):
        participants = ", ".join(meeting_info['participants'])
        lines.append(f"👥 Участники: {participants}")
        
    if meeting_info.get('description'):
        lines.append(f"")
        lines.append(f"📝 Описание:")
        lines.append(meeting_info['description'])
    
    return "\n".join(lines)
