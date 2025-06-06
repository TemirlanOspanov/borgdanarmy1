#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import datetime
from datetime import timezone, timedelta
import time
import pytz

# Попытка загрузить .env файл
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv не установлен, используем обычный подход

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Даты для отсчета
ARMY_DATE = datetime.datetime(2024, 6, 16, tzinfo=pytz.timezone('Asia/Dubai'))  # UTC+4
DEMOBILIZATION_LENGTH_DAYS = 365  # Пример: срок службы 1 год

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот для отсчета дней до армии и дембеля.\n"
        "Используй /status для проверки текущего статуса."
    )

# Функция для отображения текущего статуса
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.datetime.now(pytz.timezone('Asia/Dubai'))
    
    if now < ARMY_DATE:
        # До армии
        days_left = (ARMY_DATE - now).days
        await update.message.reply_text(f"Осталось {days_left} дней до армии.")
    else:
        # После армии (считаем до дембеля)
        demob_date = ARMY_DATE + timedelta(days=DEMOBILIZATION_LENGTH_DAYS)
        days_left = (demob_date - now).days
        await update.message.reply_text(f"Остался {days_left} дней до дембеля.")

# Функция для ежедневного уведомления
async def daily_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data
    now = datetime.datetime.now(pytz.timezone('Asia/Dubai'))
    
    if now < ARMY_DATE:
        # До армии
        days_left = (ARMY_DATE - now).days
        await context.bot.send_message(chat_id=chat_id, text=f"Осталось {days_left} дней до армии.")
    else:
        # После армии (считаем до дембеля)
        demob_date = ARMY_DATE + timedelta(days=DEMOBILIZATION_LENGTH_DAYS)
        days_left = (demob_date - now).days
        await context.bot.send_message(chat_id=chat_id, text=f"Остался {days_left} дней до дембеля.")

# Функция для настройки ежедневных уведомлений
async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    
    # Удаляем существующие задачи для этого чата
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    
    # Устанавливаем время для отправки уведомлений (00:00 UTC+4)
    dubai_tz = pytz.timezone('Asia/Dubai')
    now = datetime.datetime.now(dubai_tz)
    
    # Вычисляем время первого запуска (следующие 00:00 по UTC+4)
    if now.hour == 0 and now.minute == 0:
        first_time = now
    else:
        tomorrow = now + timedelta(days=1)
        first_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Переводим в UTC для JobQueue
    first_time_utc = first_time.astimezone(timezone.utc).time()
    
    # Устанавливаем ежедневный запуск в 00:00 UTC+4
    context.job_queue.run_daily(
        daily_notification,
        time=first_time_utc,
        days=(0, 1, 2, 3, 4, 5, 6),
        data=chat_id,
        name=str(chat_id)
    )
    
    await update.message.reply_text("Ежедневные уведомления настроены!")

def main() -> None:
    # Получаем токен из переменной окружения или задаем вручную
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")
    
    # Создаем приложение
    application = Application.builder().token(token).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("set_timer", set_timer))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main() 