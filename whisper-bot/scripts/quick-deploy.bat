@echo off
chcp 65001 >nul
echo === Deploying bot update ===
echo.
echo Pulling latest code on server...
ssh root@37.233.85.194 "cd /root/whisper-bot && git pull origin main"
echo.
echo Installing dependencies...
ssh root@37.233.85.194 "cd /root/whisper-bot && pip install -r requirements.txt"
echo.
echo Restarting bot...
ssh root@37.233.85.194 "systemctl restart whisper-bot"
timeout /t 3 /nobreak >nul
echo.
echo Checking status...
ssh root@37.233.85.194 "systemctl status whisper-bot --no-pager -n 20"
echo.
echo === Done! ===
pause
