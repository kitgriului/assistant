@echo off
echo Checking git status on server...
ssh root@37.233.85.194 "cd /root/whisper-bot && pwd && ls -la .git 2>&1 || echo 'No .git directory' && git remote -v 2>&1 || echo 'Git not initialized'"
pause
