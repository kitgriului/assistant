@echo off
echo Checking bot status...
ssh root@37.233.85.194 "systemctl restart whisper-bot"
timeout /t 3 /nobreak >nul
ssh root@37.233.85.194 "systemctl status whisper-bot"
echo.
echo === Recent logs ===
ssh root@37.233.85.194 "journalctl -u whisper-bot -n 10 --no-pager"
