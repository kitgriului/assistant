@echo off
chcp 65001 >nul
echo Checking bot logs on server...
ssh root@37.233.85.194 "journalctl -u whisper-bot -n 50 --no-pager | grep -i calendar"
echo.
echo === Full recent logs ===
ssh root@37.233.85.194 "journalctl -u whisper-bot -n 30 --no-pager"
pause
