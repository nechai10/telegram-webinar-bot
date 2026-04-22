from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db import SessionLocal
from sqlalchemy.future import select
from models import User
import os

command_handlers = {}


def command_handler(command):
    def decorator(func):
        command_handlers[command] = func
        return func

    return decorator


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/start")],
            [KeyboardButton(text="/help")],
            [KeyboardButton(text="/register")],
            [KeyboardButton(text="/cancel")],
            [KeyboardButton(text="/view")],
        ],
        resize_keyboard=True,
    )

# Command handlers for bot logic
@command_handler("start")
async def start_command(message: types.Message):
    async with SessionLocal() as session:
        query = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(query)
        user = result.scalar()
        if not user:
            new_user = User(
                telegram_id=message.from_user.id, username=message.from_user.full_name
            )
            session.add(new_user)
            await session.commit()
    await message.answer(
        "Welcome! You can register for the event, request help, or cancel your registration.",
        reply_markup=get_main_keyboard(),
    )


@command_handler("help")
async def help_command(message: types.Message):
    await message.answer(
        "This bot allows you to register for events. Use the buttons to navigate."
    )


@command_handler("register")
async def register_event(message: types.Message):
    from bot import bot

    try:
        user_in_group = await bot.get_chat_member(
            chat_id=f"@{os.getenv('TELEGRAM_GROUP_USERNAME')}",
            user_id=message.from_user.id
        )

        if user_in_group.status in ["member", "administrator", "creator"]:
            async with SessionLocal() as session:
                query = select(User).where(User.telegram_id == message.from_user.id)
                result = await session.execute(query)
                user = result.scalar()

                if user:
                    if user.is_registered:
                        await message.answer("You are already registered for the event.")
                        return

                    user.is_registered = True
                    await session.commit()

            await message.answer(
                "You have successfully registered! Here is the link to the event: https://example.com"
            )
            return

        else:
            raise Exception("User not in group")

    except Exception:
        join_button = InlineKeyboardButton(
            text=f"Join the group @{os.getenv('TELEGRAM_GROUP_USERNAME')}",
            url=f"https://t.me/{os.getenv('TELEGRAM_GROUP_USERNAME')}"
        )

        join_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[join_button]]
        )

        await message.answer(
            "Please join our group to register.",
            reply_markup=join_keyboard
        )


@command_handler("cancel")
async def cancel_registration(message: types.Message):
    async with SessionLocal() as session:
        query = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(query)
        user = result.scalar()
        if user:
            if not user.is_registered:
                await message.answer("You are not registered for the event.")
                return
            user.is_registered = False
            await session.commit()
            await message.answer("Your registration has been canceled.")
        else:
            await message.answer("You are not registered for the event.")


@command_handler("view")
async def view_registered_users(message: types.Message):
    # Check if the user is an admin
    admin_id = os.getenv("ADMIN_ID")
    if str(message.from_user.id) != admin_id:
        await message.answer("You do not have permission to use this command.")
        return

    async with SessionLocal() as session:
        query = select(User.telegram_id, User.username).where(
            User.is_registered == True
        )
        result = await session.execute(query)
        registered_users = result.fetchall()

    if registered_users:
        user_links = [
            f"<a href='tg://user?id={user.telegram_id}'>{user.username}</a>"
            for user in registered_users
        ]
        user_list = "\n".join(user_links)
        await message.answer(
            f"Registered users:\n{user_list}\n\nTotal: {len(registered_users)}",
            parse_mode="HTML",
        )
    else:
        await message.answer("No users are registered for the event.")


async def handle_message(message: types.Message):
    command = message.text.lower()
    if command.startswith("/"):
        command = command[1:]  # Убираем слэш перед командой
    if command in command_handlers:
        await command_handlers[command](message)
    else:
        await message.answer("Unknown command. Use the buttons to navigate.")
