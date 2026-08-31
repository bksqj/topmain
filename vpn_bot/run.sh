#!/usr/bin/env bash
# Быстрый запуск бота на macOS / Linux.
# Использование: ./run.sh
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "→ создаю виртуальное окружение..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "→ устанавливаю зависимости..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo
  echo "⚠️  Нет файла .env — создаю из шаблона."
  cp .env.example .env
  echo "    Открой .env и впиши BOT_TOKEN (и ADMIN_IDS), затем запусти ./run.sh снова."
  exit 1
fi

echo "→ запускаю бота (Ctrl+C для остановки)..."
python -m bot.main
