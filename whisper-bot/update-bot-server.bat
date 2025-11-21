@echo off
REM Быстрое обновление бота на сервере
REM Использование: update-bot-server.bat [commit message]

echo ====================================
echo   Обновление бота на сервере
echo ====================================
echo.

REM Проверка что мы в правильной директории
if not exist "bot.py" (
    echo Ошибка: bot.py не найден!
    echo Запустите скрипт из директории whisper-bot
    pause
    exit /b 1
)

echo 1. Проверяю статус git...
git status --short
echo.

REM Проверка наличия изменений
for /f %%i in ('git status --porcelain ^| find /c /v ""') do set CHANGES=%%i

if %CHANGES% GTR 0 (
    echo Обнаружены несохраненные изменения.
    set /p COMMIT="Хотите закоммитить? (y/n): "
    
    if /i "%COMMIT%"=="y" (
        git add .
        set /p MESSAGE="Введите сообщение коммита: "
        git commit -m "%MESSAGE%"
        echo Изменения закоммичены.
    ) else (
        echo Отменено. Сначала закоммитьте изменения.
        pause
        exit /b 1
    )
)

echo.
echo 2. Отправляю изменения в GitHub...
git push origin main
if errorlevel 1 (
    echo Ошибка при push в GitHub!
    pause
    exit /b 1
)
echo Изменения отправлены в GitHub.

echo.
echo 3. Подключаюсь к серверу и обновляю бота...
echo.
ssh root@37.233.85.194 "cd /root/whisper-bot && bash update-bot.sh"

echo.
echo ====================================
echo   Обновление завершено!
echo ====================================
echo.
echo Проверьте бота в Telegram: @softmachina_bot
pause
