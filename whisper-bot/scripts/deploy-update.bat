@echo off
echo === Updating bot on server ===
echo.
echo Step 1: Cloning/pulling repository...
ssh root@37.233.85.194 "cd /root && rm -rf whisper-bot-new && git clone git@github.com:kitgriului/assistant.git whisper-bot-new && cp /root/whisper-bot/.env /root/whisper-bot-new/ && rm -rf /root/whisper-bot-old && mv /root/whisper-bot /root/whisper-bot-old && mv /root/whisper-bot-new /root/whisper-bot"
echo.
echo Step 2: Installing dependencies...
ssh root@37.233.85.194 "cd /root/whisper-bot && pip install -r requirements.txt"
echo.
echo Step 3: Restarting bot...
ssh root@37.233.85.194 "systemctl restart whisper-bot"
timeout /t 3 /nobreak >nul
echo.
echo Step 4: Checking status...
ssh root@37.233.85.194 "systemctl status whisper-bot"
echo.
echo === Done! ===
pause
