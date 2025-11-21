@echo off
echo Updating bot on server...
ssh root@37.233.85.194 "cd /root/whisper-bot && git pull && pip install -r requirements.txt && systemctl restart whisper-bot && systemctl status whisper-bot"
echo Done!
pause
