# SB24GZ – ផ្សាយផ្ទាល់

Telegram-native live updates bot.

## Core functions

1. 🔴 Live Now
2. 📣 Latest Updates
3. 📝 Submit Update

## Commands

- `/start` — open the main menu
- `/help` — show help

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add BOT_TOKEN to .env
python bot.py
```

## Render

This repository is configured as a Docker worker. Set the `BOT_TOKEN` environment variable in Render; the Dockerfile starts `python bot.py`.
