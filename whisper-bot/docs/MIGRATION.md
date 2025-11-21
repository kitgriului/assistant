# 🔄 Migration Guide: v1.0 → v2.0

This guide explains how to migrate from the old monolithic structure to the new modular architecture.

## 📋 What Changed

### Structure
- **Old**: All code in `bot.py` (408 lines)
- **New**: Modular structure with separate services, handlers, and utilities

### Key Improvements
✅ **Modularity**: Code split into logical components  
✅ **Type Safety**: Better type hints and validation  
✅ **Testability**: Each module can be tested independently  
✅ **Maintainability**: Easier to understand and modify  
✅ **Scalability**: Can add new features without bloating main file  

## 🚀 Migration Steps

### Step 1: Verify Old Bot Works
```bash
# Test current bot
python bot.py
```

### Step 2: Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Step 3: Run New Bot (Parallel Testing)
```bash
# Keep old bot running, test new one separately
python -m src.main
```

### Step 4: Validate Functionality
Test all features:
- [x] Voice message transcription
- [x] Audio file transcription  
- [x] Video transcription
- [x] Note generation
- [x] Meeting extraction
- [x] Summary creation
- [x] Calendar event creation

### Step 5: Switch Production
Once validated, update server:
```bash
# On server
cd /root/whisper-bot
git pull
pip install -r requirements.txt

# Update systemd service
sudo nano /etc/systemd/system/whisper-bot.service

# Change ExecStart to:
ExecStart=/usr/bin/python3 -m src.main

sudo systemctl daemon-reload
sudo systemctl restart whisper-bot
```

## 📁 File Mapping

| Old Location | New Location | Notes |
|-------------|--------------|-------|
| `bot.py` (lines 1-50) | `src/config.py` | Configuration |
| `bot.py` (lines 51-80) | `src/services/media.py` | Media processing |
| `bot.py` (lines 81-95) | `src/services/whisper.py` | Transcription |
| `bot.py` (lines 96-165) | `src/services/gpt.py` | GPT processing |
| `bot.py` (lines 166-180) | `src/bot/keyboards.py` | UI elements |
| `bot.py` (lines 210-260) | `src/main.py` | Media handlers |
| `bot.py` (lines 309-390) | `src/main.py` | Action handlers |
| `calendar_parser.py` | `src/services/calendar/parser.py` | Moved |
| `calendar_integration.py` | `src/services/calendar/integration.py` | Moved |

## 🔧 Configuration Changes

### Old `.env`
```env
BOT_TOKEN=...
OPENAI_API_KEY=...
```

### New `.env` (Extended)
```env
# Required
BOT_TOKEN=...
OPENAI_API_KEY=...

# Optional (with defaults)
WHISPER_MODEL=whisper-1
GPT_MODEL=gpt-4o-mini
GPT_TEMPERATURE=0.7
LOG_LEVEL=INFO
CALENDAR_ENABLED=true
CALENDAR_TIMEZONE=Europe/Moscow
TEMP_DIR=/tmp
MAX_FILE_SIZE_MB=20
```

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Manual Testing Checklist
- [ ] Bot starts without errors
- [ ] `/start` command works
- [ ] Voice message transcription
- [ ] Audio file handling
- [ ] Video processing
- [ ] Note generation works
- [ ] Meeting extraction works
- [ ] Summary creation works
- [ ] Calendar button appears
- [ ] Calendar .ics file generated
- [ ] Error handling graceful

## 🔙 Rollback Plan

If something goes wrong:

```bash
# On server
cd /root/whisper-bot
git checkout <previous-commit-hash>

# Update service back to old entry point
sudo nano /etc/systemd/system/whisper-bot.service
# Change ExecStart to: /usr/bin/python3 bot.py

sudo systemctl daemon-reload
sudo systemctl restart whisper-bot
```

## ⚠️ Breaking Changes

### Import Changes
```python
# Old
from calendar_parser import extract_meeting_info
from calendar_integration import create_ics_file

# New
from src.services.calendar import extract_meeting_info, create_ics_file
```

### Running Bot
```bash
# Old
python bot.py

# New
python -m src.main
```

### Service File
```ini
# Old
ExecStart=/usr/bin/python3 /root/whisper-bot/bot.py

# New
ExecStart=/usr/bin/python3 -m src.main
```

## ✅ Benefits of New Structure

### 1. **Separation of Concerns**
- Configuration → `config.py`
- Logging → `utils/logger.py`
- Services → `services/`
- Bot logic → `bot/` + `main.py`

### 2. **Easier Testing**
```python
# Can now test individual components
from src.services.gpt import GPTService
from src.config import Config

def test_gpt_service():
    config = Config.from_env()
    gpt = GPTService(client, config.gpt_model)
    # Test specific functionality
```

### 3. **Better Error Handling**
- Centralized logging
- Service-specific exceptions
- Graceful degradation

### 4. **Scalability**
Easy to add new features:
```python
# New service
src/services/translation.py

# New handler
src/bot/handlers/admin.py
```

## 📊 Code Metrics

| Metric | Old | New | Improvement |
|--------|-----|-----|-------------|
| Files | 3 | 15+ | Better organization |
| Largest file | 408 lines | ~250 lines | More readable |
| Test coverage | 0% | 40%+ | Quality assurance |
| Type hints | Partial | Comprehensive | Better IDE support |

## 🎯 Next Steps

After successful migration:

1. **Add more tests**: Increase coverage to 80%+
2. **Add linting**: Integrate pre-commit hooks
3. **Database**: Replace in-memory storage
4. **Monitoring**: Add Prometheus metrics
5. **Documentation**: API docs with Sphinx

## 🆘 Troubleshooting

### Import Errors
```bash
# Make sure you're in project root
cd /root/whisper-bot

# Run as module
python -m src.main
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Calendar Not Working
```bash
pip install icalendar python-dateutil
```

### Check Logs
```bash
# On server
journalctl -u whisper-bot -n 50 --no-pager
```

## 📞 Support

If you encounter issues:
1. Check logs: `journalctl -u whisper-bot`
2. Verify config: Check `.env` file
3. Test locally: `python -m src.main`
4. Rollback if needed (see above)

---

**Migration Time**: ~15 minutes  
**Downtime**: < 1 minute (service restart)  
**Risk Level**: Low (easy rollback)
