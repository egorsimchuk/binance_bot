from src.telegram_bot.aiogram_bot import start_bot
import logging
from src.utils.logging import log_format, log_level
logging.basicConfig(format=log_format, level=log_level)

if __name__ == '__main__':
    start_bot()