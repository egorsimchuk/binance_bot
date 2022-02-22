from src.telegram_bot.main import TelegramBotHandler
from src.utils.utils import load_config_json

if __name__ == '__main__':
    token = load_config_json('config/telegram_bot/token.json')['token']
    TelegramBotHandler(token=token).run()