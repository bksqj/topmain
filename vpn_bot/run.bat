@echo off
REM Быстрый запуск бота на Windows. Двойной клик или: run.bat
cd /d "%~dp0"

if not exist ".venv" (
  echo -^> создаю виртуальное окружение...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo -^> устанавливаю зависимости...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

if not exist ".env" (
  echo.
  echo [!] Нет файла .env — создаю из шаблона.
  copy .env.example .env >nul
  echo     Открой .env, впиши BOT_TOKEN и ADMIN_IDS, затем запусти run.bat снова.
  pause
  exit /b 1
)

echo -^> запускаю бота (Ctrl+C для остановки)...
python -m bot.main
pause
