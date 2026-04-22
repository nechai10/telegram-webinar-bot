import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram.filters import Command
from dotenv import load_dotenv
from db import init_db
from handlers import handle_message

# Main entry point of the Telegram bot
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(level=logging.INFO)

# Bot setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Register the bot commands
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="register", description="Register for an event"),
        BotCommand(command="cancel", description="Cancel registration"),
        BotCommand(command="view", description="View registered users (admin only)"),
    ]
    await bot.set_my_commands(commands)


# Bot startup
async def on_startup():
    await init_db()
    await set_commands(bot)
    logging.info("Bot is up and running!")

async def main():
    dp.message.register(handle_message)
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
