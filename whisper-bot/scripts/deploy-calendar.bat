@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Deploying Calendar Integration
echo ========================================
echo.

echo [1/5] Checking current bot version on server...
ssh root@37.233.85.194 "cd /root/whisper-bot && git log --oneline -1"
echo.

echo [2/5] Pulling latest code from GitHub...
ssh root@37.233.85.194 "cd /root/whisper-bot && git pull origin main"
echo.

echo [3/5] Installing calendar dependencies...
ssh root@37.233.85.194 "cd /root/whisper-bot && pip install --no-cache-dir icalendar python-dateutil google-auth google-auth-oauthlib google-api-python-client"
echo.

echo [4/5] Verifying calendar modules exist...
ssh root@37.233.85.194 "cd /root/whisper-bot && ls -la calendar*.py"
echo.

echo [5/5] Restarting bot...
ssh root@37.233.85.194 "systemctl restart whisper-bot"
timeout /t 3 /nobreak >nul
ssh root@37.233.85.194 "systemctl status whisper-bot --no-pager"
echo.

echo ========================================
echo   Checking calendar module status...
echo ========================================
ssh root@37.233.85.194 "journalctl -u whisper-bot -n 20 --no-pager | grep -E '(Calendar|calendar|CALENDAR)'"
echo.

echo ========================================
echo   DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Next: Send a voice message about a meeting to test!
echo Example: "Завтра в 15:00 встреча с командой"
echo.
pause
