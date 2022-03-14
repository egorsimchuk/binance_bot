import logging

logger = logging.getLogger(__name__)

from src.utils.utils import load_config_json

API_TOKEN = load_config_json('config/telegram_bot/token.json')['token']

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

bot = Bot(token=API_TOKEN)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    user_api_key = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    row_btns = [types.InlineKeyboardButton('set api key', callback_data='set_api_key'),
                types.InlineKeyboardButton('get report', callback_data='get_report')]
    keyboard_markup.row(*row_btns)
    keyboard_markup.add(
        types.InlineKeyboardButton('get energy', callback_data='get_report'),
    )

    # Set state
    await message.answer("Hi there! Available commands:\n\n/set_api_key — set or update binance api key"
                         "\n\n/get_report — ask for creating html report",
                         reply_markup=keyboard_markup)


# Check age. Age gotta be digit
@dp.message_handler(state=Form.user_api_key)
async def process_set_api_key(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_api_key = message.text
        data['user_api_key'] = user_api_key
        if user_api_key == 'key':
            await message.reply(f"Api key: {user_api_key}\nKey is known. You are able to get report with old dumped transactions.")
        else:
            await message.reply(f"Api key: {user_api_key}\nKey is not known. You are able to get report, but with newest transactions only.")

    await state.finish()


@dp.callback_query_handler(text='set_api_key')
async def inline_set_api_key_callback_handler(query: types.CallbackQuery):
    await bot.send_message(query.from_user.id, "Type your token")
    await Form.user_api_key.set()


@dp.message_handler(commands='set_api_key')
async def cmd_set_api_key(message: types.Message):
    await message.answer("Type your token")
    await Form.user_api_key.set()


@dp.callback_query_handler(text='get_report')
async def inline_get_report_callback_handler(query: types.CallbackQuery):
    answer_data = query.data
    # always answer callback queries, even if you have nothing to say
    await bot.send_message(query.from_user.id, f'Building report, wait a couple of minutes. 🐌')
    await query.answer(f'You click {answer_data!r}')


@dp.message_handler(commands='get_report')
async def cmd_set_api_key(message: types.Message):
    await message.answer("Type your token")
    await Form.user_api_key.set()


def start_bot():
    executor.start_polling(dp, skip_updates=True)
