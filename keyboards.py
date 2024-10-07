from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_channel_info, is_admin


def channels_url():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for title, url in get_channel_info():
        keyboard.add(InlineKeyboardButton(text=title, url=url))

    keyboard.add(InlineKeyboardButton("✅Проверить подписку", callback_data="check_subscription"))
    return keyboard


def menu(user_id):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if is_admin(user_id):
        keyboard.add(InlineKeyboardButton("👨‍💻Панель Администратора"))
    keyboard.add(InlineKeyboardButton("👤Профиль", callback_data='profile'))
    keyboard.add(InlineKeyboardButton("🚀Подписки", callback_data='plans'))
    keyboard.add(InlineKeyboardButton("⁉️Помощь", callback_data='help'))
    return keyboard
