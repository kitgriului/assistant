@echo off
echo Checking server structure...
ssh root@37.233.85.194 "ls -la /root/ && echo --- && find /root -name whisper-bot -type d 2>/dev/null"
pause
