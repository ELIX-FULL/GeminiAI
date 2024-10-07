import os
import time

import google.generativeai as genai
import telebot
from dotenv import load_dotenv

import texts
from database import (add_user, check_user, be_active, get_channel_ids, get_user_profile)
from keyboards import channels_url, menu

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))


@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    user = message.from_user
    # Проверка подписки
    is_subscribed = check_subscription(user_id)
    action = "/start"
    name = f"<a href='https://t.me/{user.username}'>{user.first_name}</a>"
    if not check_user(user_id):
        add_user(user_id)
        if is_subscribed == 'НЕТ':
            be_active(user_id, action)
            # Пользователь не подписан - отображение информации о подписке
            text = (f"<b>👋Приветствую! {name if user.username else user.first_name}</b>"
                    f"<i>\n👇Для использования бота, пожалуйста, подпишитесь на наши каналы:</i>")
            bot.send_message(user_id, text, reply_markup=channels_url(), parse_mode='HTML',
                             disable_web_page_preview=True)
        elif is_subscribed == 'ДА':
            be_active(user_id, action)
            bot.send_message(user_id, f"<b>👋Приветствую! {name if user.username else user.first_name}</b>",
                             parse_mode='HTML', disable_web_page_preview=True, reply_markup=menu(user_id))
    else:
        if is_subscribed == 'НЕТ':
            be_active(user_id, action)
            # Пользователь не подписан - отображение информации о подписке
            text = (f"👋<b>Приветствую! {name if user.username else user.first_name}</b>"
                    f"<i>\n👇Для использования бота, пожалуйста, подпишитесь на наши каналы:</i>")
            bot.send_message(user_id, text, reply_markup=channels_url(), parse_mode="HTML",
                             disable_web_page_preview=True)
        elif is_subscribed == 'ДА':
            be_active(user_id, action)
            bot.send_message(user_id, f"<b>👋Приветствую! {name if user.username else user.first_name}</b>",
                             parse_mode="HTML", disable_web_page_preview=True, reply_markup=menu(user_id))


def check_subscription(user_id):
    try:
        channel_ids = get_channel_ids()
        for channel_id in channel_ids:
            try:
                result = bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if result.status in ["administrator", "creator", "member"]:
                    return "ДА"
                else:
                    return "НЕТ"
            except telebot.apihelper.ApiException:
                return "НЕТ"
    except telebot.apihelper.ApiException as e:
        return "НЕТ"


@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription_callback(call):
    user_id = call.from_user.id
    user = call.from_user
    name = f"<a href='https://t.me/{user.username}'>{user.first_name}</a>"
    # Проверка подписки
    is_subscribed = check_subscription(user_id)
    if is_subscribed == 'ДА':
        bot.answer_callback_query(call.id, '✅ Вы подписаны')
        time.sleep(1)
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(chat_id=user_id, text=f"<b>👋Приветствую! {name if user.username else user.first_name}</b>",
                         parse_mode="HTML", disable_web_page_preview=True, reply_markup=menu(user_id))

    else:
        bot.answer_callback_query(call.id, '❌ Вы не подписаны')
        time.sleep(1)
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(chat_id=user_id,
                         text="<i>👇Для использования бота, пожалуйста, подпишитесь на наши каналы ниже:</i>",
                         reply_markup=channels_url(), parse_mode="HTML", disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile(call):
    user_id, balance, plan = get_user_profile(call.from_user.id)
    is_subscribed = check_subscription(user_id)
    user = call.from_user
    name = f"<a href='https://t.me/{user.username}'>{user.first_name}</a>"

    if is_subscribed == 'ДА':
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                              text=f"<b>👤Профиль:\n\n"
                                   f"🆔: <i>{user_id}</i>\n"
                                   f"🚀: <i>Подписка {plan}</i>\n"
                                   f"💰: <i>{balance} запросов</i>\n</b>",
                              parse_mode="HTML", disable_web_page_preview=True)
    else:
        bot.send_message(chat_id=user_id, text=f"<b>{name if user.username else user.first_name}</b>\n"
                                               f"<i>❌Вы не подписаны. 👇Для использования бота, пожалуйста, "
                                               f"подпишитесь на наши каналы:</i>", reply_markup=channels_url(),
                         parse_mode='HTML', disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data == "plans")
def plans(call):
    user_id = call.from_user.id
    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                          text=texts.see_plans,
                          parse_mode="HTML", disable_web_page_preview=True)


@bot.message_handler(func=lambda message: message.chat.type == "private")
def generate_text(message):
    user_id, balance, plan = get_user_profile(message.from_user.id)
    user = message.from_user
    name = f"<a href='https://t.me/{user.username}'>{user.first_name}</a>"
    model = genai.GenerativeModel("gemini-1.5-flash")

    if balance == 0:
        bot.send_message(user_id, f'{name if user.username else user.first_name} К сожалению у вас 0 запросов',
                         reply_markup=menu(user_id), parse_mode='HTML', disable_web_page_preview=True)
    else:
        response = model.generate_content(message.text).text
        if response:
            bot.send_message(user_id, response, parse_mode='HTML', disable_web_page_preview=True)
        else:
            bot.send_message(user_id, 'Извините, но я не смогу сгенерировать текст по вашему запросу',
                             reply_markup=menu(user_id), parse_mode='HTML', disable_web_page_preview=True)


@bot.message_handler(content_types=['photo'])
def answer_photo(message):
    # Получение ID фотографии
    photo_id = message.photo[-1].file_id
    text = message.caption
    if text:
        # Получение информации о фотографии
        file_info = bot.get_file(photo_id)

        # Загрузка и сохранение фотографии
        response = bot.download_file(file_info.file_path)
        file_path = os.path.join('media', f"{message.message_id}.jpg")

        with open(file_path, 'wb') as f:
            f.write(response)
        file = genai.upload_file(f'media/{message.message_id}.jpg')
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(
            [file, "\n\n", text]
        )
        if result:
            bot.send_message(message.chat.id, result.text, parse_mode='HTML', disable_web_page_preview=True)
            os.remove(f'media/{message.message_id}.jpg')
        else:
            bot.send_message(message.chat.id, 'Извините, но я не смогу сгенерировать текст по вашему запросу',
                             parse_mode='HTML', disable_web_page_preview=True)
    else:
        # Получение информации о фотографии
        file_info = bot.get_file(photo_id)

        # Загрузка и сохранение фотографии
        response = bot.download_file(file_info.file_path)
        file_path = os.path.join('media', f"{message.message_id}.jpg")

        with open(file_path, 'wb') as f:
            f.write(response)
        file = genai.upload_file(f'media/{message.message_id}.jpg')
        model = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(
            [file, "\n\n", 'Ответь по этому фото']
        )
        if result:
            bot.send_message(message.chat.id, result.text, parse_mode='HTML', disable_web_page_preview=True)
            os.remove(f'media/{message.message_id}.jpg')
        else:
            bot.send_message(message.chat.id, 'Извините, но я не смогу сгенерировать текст по вашему запросу',
                             parse_mode='HTML', disable_web_page_preview=True)


if __name__ == "__main__":
    bot.infinity_polling()
