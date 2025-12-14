"""
Модуль для работы с Google Calendar и создания .ics файлов
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from icalendar import Calendar, Event
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .parser import parse_datetime, calculate_end_time


# Области доступа для Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']


def create_ics_file(meeting_info: Dict[str, Any], output_dir: str = "/tmp") -> Optional[str]:
    """
    Создает .ics файл для добавления события в календарь.
    
    Args:
        meeting_info: Информация о встрече из calendar_parser
        output_dir: Директория для сохранения файла
        
    Returns:
        Путь к созданному файлу или None при ошибке
    """
    try:
        # Создаем календарь
        cal = Calendar()
        cal.add('prodid', '-//Whisper Bot Calendar//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        
        # Создаем событие
        event = Event()
        event.add('summary', meeting_info['title'])
        
        # Парсим дату и время
        if meeting_info.get('start_time'):
            start_dt = parse_datetime(
                meeting_info['date'],
                meeting_info['start_time']
            )
            
            # Вычисляем время окончания
            if meeting_info.get('end_time'):
                end_dt = parse_datetime(
                    meeting_info['date'],
                    meeting_info['end_time']
                )
            else:
                duration = meeting_info.get('duration_minutes', 60)
                end_dt = calculate_end_time(start_dt, duration)
        else:
            # Если время не указано, создаем событие на весь день
            start_dt = datetime.strptime(meeting_info['date'], "%Y-%m-%d").date()
            end_dt = start_dt
            event.add('dtstart', start_dt)
            event.add('dtend', end_dt)
            event.add('summary', meeting_info['title'])
            
            if meeting_info.get('description'):
                event.add('description', meeting_info['description'])
                
            if meeting_info.get('location'):
                event.add('location', meeting_info['location'])
                
            cal.add_component(event)
            
            # Сохраняем файл
            filename = f"event_{meeting_info['date']}.ics"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'wb') as f:
                f.write(cal.to_ical())
                
            return str(filepath)
        
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        
        # Добавляем описание
        if meeting_info.get('description'):
            event.add('description', meeting_info['description'])
            
        # Добавляем место
        if meeting_info.get('location'):
            event.add('location', meeting_info['location'])
            
        # Добавляем участников
        if meeting_info.get('participants'):
            for participant in meeting_info['participants']:
                event.add('attendee', f'mailto:{participant}')
        
        # Добавляем напоминание за 15 минут
        from icalendar import Alarm
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('trigger', '-PT15M')
        alarm.add('description', f"Напоминание: {meeting_info['title']}")
        event.add_component(alarm)
        
        # Добавляем уникальный ID
        import uuid
        event.add('uid', str(uuid.uuid4()))
        event.add('dtstamp', datetime.now())
        
        # Добавляем событие в календарь
        cal.add_component(event)
        
        # Сохраняем файл
        filename = f"meeting_{start_dt.strftime('%Y%m%d_%H%M')}.ics"
        filepath = Path(output_dir) / filename
        
        with open(filepath, 'wb') as f:
            f.write(cal.to_ical())
            
        return str(filepath)
        
    except Exception as e:
        print(f"Ошибка при создании .ics файла: {e}")
        return None


def get_google_calendar_service(user_id: int, credentials_dir: str = "credentials"):
    """
    Получает сервис Google Calendar для пользователя.
    Выполняет OAuth авторизацию если необходимо.
    
    Args:
        user_id: ID пользователя Telegram
        credentials_dir: Директория с credentials.json
        
    Returns:
        Google Calendar service объект
    """
    creds = None
    token_file = Path(credentials_dir) / "user_tokens" / f"{user_id}_token.json"
    credentials_file = Path(credentials_dir) / "google_credentials.json"
    
    # Проверяем наличие сохраненного токена
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    
    # Если нет валидных credentials, авторизуемся
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_file.exists():
                raise FileNotFoundError(
                    f"Файл {credentials_file} не найден. "
                    "Получите credentials.json в Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Сохраняем токен для будущего использования
        token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    
    service = build('calendar', 'v3', credentials=creds)
    return service


def create_google_calendar_event(
    user_id: int,
    meeting_info: Dict[str, Any],
    credentials_dir: str = "credentials"
) -> Optional[str]:
    """
    Создает событие в Google Calendar пользователя.
    
    Args:
        user_id: ID пользователя Telegram
        meeting_info: Информация о встрече
        credentials_dir: Директория с credentials
        
    Returns:
        URL созданного события или None при ошибке
    """
    try:
        service = get_google_calendar_service(user_id, credentials_dir)
        
        # Формируем событие для Google Calendar API
        event_body = {
            'summary': meeting_info['title'],
        }
        
        # Добавляем дату/время
        if meeting_info.get('start_time'):
            start_dt = parse_datetime(
                meeting_info['date'],
                meeting_info['start_time']
            )
            
            if meeting_info.get('end_time'):
                end_dt = parse_datetime(
                    meeting_info['date'],
                    meeting_info['end_time']
                )
            else:
                duration = meeting_info.get('duration_minutes', 60)
                end_dt = calculate_end_time(start_dt, duration)
            
            event_body['start'] = {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Europe/Moscow',
            }
            event_body['end'] = {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Europe/Moscow',
            }
        else:
            # Событие на весь день
            event_body['start'] = {
                'date': meeting_info['date'],
            }
            event_body['end'] = {
                'date': meeting_info['date'],
            }
        
        # Добавляем описание
        if meeting_info.get('description'):
            event_body['description'] = meeting_info['description']
        
        # Добавляем место
        if meeting_info.get('location'):
            event_body['location'] = meeting_info['location']
        
        # Добавляем участников
        if meeting_info.get('participants'):
            event_body['attendees'] = [
                {'email': p} for p in meeting_info['participants']
            ]
        
        # Добавляем напоминание
        event_body['reminders'] = {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 15},
            ],
        }
        
        # Создаем событие
        event = service.events().insert(
            calendarId='primary',
            body=event_body
        ).execute()
        
        return event.get('htmlLink')
        
    except Exception as e:
        print(f"Ошибка при создании события в Google Calendar: {e}")
        return None


def check_calendar_auth(user_id: int, credentials_dir: str = "credentials") -> bool:
    """
    Проверяет, авторизован ли пользователь в Google Calendar.
    
    Args:
        user_id: ID пользователя
        credentials_dir: Директория с credentials
        
    Returns:
        True если авторизован, False иначе
    """
    token_file = Path(credentials_dir) / "user_tokens" / f"{user_id}_token.json"
    
    if not token_file.exists():
        return False
    
    try:
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        return creds.valid or (creds.expired and creds.refresh_token)
    except:
        return False
