import logging

from telegram import Bot, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from src.analysis.html_report import make_report
from src.utils.logging import log_format
from src.utils.utils import load_config_json

logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(__name__)


#
# def start(update: Update, context: CallbackContext):
#     context.bot.send_message(chat_id=update.effective_chat.id, text="I can analyse your Binance portfolio!")
#
#
def help(update: Update, context: CallbackContext):
    update.message.reply_text(
        """Available Commands :
    /set_binance_api_key
    /get_report
    """
    )


API_KEY, _, _, _ = range(4)


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their gender."""

    update.message.reply_text(
        "I can analyse your Binance portfolio! Enter your api key."
    )
    return API_KEY


def unknown_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="Sorry, I didn't understand that command. List of commands: /help"
    )


def unknown_text(update: Update, context: CallbackContext):
    update.message.reply_text(text="Sorry, I don't understand messages")


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


class TelegramBotHandler:
    def __init__(self, token):
        self._token = token
        self._is_token_ok = False
        self._bot = None

    def set_binance_api_key(self, update: Update, context: CallbackContext):
        ok_api_key = load_config_json("config/telegram_bot/binance_keys.json")[
            "api_key"
        ]
        user = update.message.from_user
        user_api_key = update.message.text
        logger.info(f"api key of {user.first_name}: {user_api_key}")

        if user_api_key == ok_api_key:
            update.message.reply_text(
                "Api key is correct, you are able to build reports. Use /get_report"
            )
            logger.info("api key is ok")
            self._is_token_ok = True
        else:
            update.message.reply_text(
                f"Api key is not correct: {user_api_key}.\nTry again."
            )
            return API_KEY

        return ConversationHandler.END

    def get_report(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(f"Wait for a couple minutes.")

        api_keys = load_config_json("config/telegram_bot/binance_keys.json")
        html_fpath = make_report(
            api_keys["api_key"], api_keys["api_secret"], open_file=False
        )

        with open(html_fpath, "rb") as html_file:
            response = self._bot.sendDocument(
                chat_id=update.effective_chat.id, document=html_file
            )
        logger.info(f"html file was sended to user")

    def run(self):
        updater = Updater(self._token)
        dispatcher = updater.dispatcher
        self._bot = Bot(self._token)

        # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                API_KEY: [MessageHandler(Filters.text, self.set_binance_api_key)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        # dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(conv_handler)
        dispatcher.add_handler(
            CommandHandler("set_binance_api_key", self.set_binance_api_key)
        )

        dispatcher.add_handler(CommandHandler("get_report", self.get_report))
        dispatcher.add_handler(CommandHandler("help", help))
        dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))
        dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))

        updater.start_polling()
        updater.idle()
