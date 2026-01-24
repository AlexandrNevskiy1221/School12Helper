from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import telebot
import telebot.types as types
import os
load_dotenv()

API_TOKEN = os.getenv("SUPPORT_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

creds = Credentials.from_service_account_file(
    "creds.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

service = build("sheets", "v4", credentials=creds)
SHEET_ID = "15-GVlpKITU5Tq_M_8tWo9Ko9H9IWUpaJEUn-J15GiQ0"
sheet = service.spreadsheets()
user_state = {}

@bot.message_handler(commands=["start"])
def send_welcome(msg):
    bot.send_message(msg.from_user.id, "Привет! Я - бот поддержки твоей школы. Чтобы сообщить о проблеме используй /report")

@bot.message_handler(commands=["report"])
def list_problems(msg):
    kb = types.InlineKeyboardMarkup()
    left = types.InlineKeyboardButton(text = "Левое крыло", callback_data = "left")
    right = types.InlineKeyboardButton(text = "Правое крыло", callback_data = "right")
    kb.add(left,right)
    
    bot.send_message(msg.chat.id, "В каком крыле проблема?", reply_markup = kb)

@bot.callback_query_handler()
def handler(call):
    user = call.from_user.id
    if user not in user_state:
        user_state[user] = {}
    third = types.InlineKeyboardButton(text = "Третий этаж", callback_data = "third_" + call.data)
    second = types.InlineKeyboardButton(text = "Второй этаж", callback_data = "second_" + call.data)
    first = types.InlineKeyboardButton(text = "Первый этаж", callback_data = "first")
    zero = types.InlineKeyboardButton(text = "Мастерские", callback_data = "zero")
    if call.data == "left":
        user_state[user]["wing"] = call.data
        kb = types.InlineKeyboardMarkup()
        kb.add(third)
        kb.add(second)
        kb.add(first)
        kb.add(zero)
        bot.edit_message_text("Окей. Запомнил: проблема в левом крыле. На каком этаже?", chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = kb)
    elif call.data == "right":
        user_state[user]["wing"] = call.data
        kb = types.InlineKeyboardMarkup()
        kb.add(third)
        kb.add(second)
        bot.edit_message_text("Окей. Запомнил: проблема в правом крыле. На каком этаже?", chat_id = call.message.chat.id, message_id = call.message.message_id, reply_markup = kb)
    elif call.data == "third_right":
        user_state[user]["floor"] = call.data
        bot.edit_message_text("Понял. Проблема на третьем этаже правого крыла. Пожалуйста опиши проблему и в каком кабинете она находится", chat_id = call.message.chat.id, message_id = call.message.message_id)
    elif call.data == "second_right":
        user_state[user]["floor"] = call.data
        bot.edit_message_text("Понял. Проблема на втором этаже правого крыла. Пожалуйста опиши проблему и в каком кабинете она находится", chat_id = call.message.chat.id, message_id = call.message.message_id)
    elif call.data == "third_left":
        user_state[user]["floor"] = call.data
        bot.edit_message_text("Понял. Проблема на третьем этаже левого крыла. Пожалуйста опиши проблему и в каком кабинете она находится", chat_id = call.message.chat.id, message_id = call.message.message_id)
    elif call.data == "second_left":
        user_state[user]["floor"] = call.data
        bot.edit_message_text("Понял. Проблема на втором этаже левого крыла. Пожалуйста опиши проблему и в каком кабинете она находится", chat_id = call.message.chat.id, message_id = call.message.message_id)
    elif call.data == "first":
        user_state[user]["floor"] = call.data
        bot.edit_message_text("Понял. Проблема на первом этаже левого крыла. Пожалуйста опиши проблему и в каком кабинете она находится", chat_id = call.message.chat.id, message_id = call.message.message_id)
    elif call.data == "zero":
        user_state[user]["floor"] = call.data
        bot.edit_message_text("Понял. Проблема в мастерских. Пожалуйста опиши проблему и в каком кабинете она находится", chat_id = call.message.chat.id, message_id = call.message.message_id)

@bot.message_handler(content_types = ["text"])
def query(msg):
    user = msg.from_user.id
    data = int(max(sheet.values().get(spreadsheetId = SHEET_ID, range = "Sheet!A2:A").execute().get("values", []))[0]) + 1
    if user_state[user] and user_state[user]["wing"] and user_state[user]["floor"]:
        user_state[user]["query"] = msg.text
        bot.send_message(msg.chat.id, f"Окей. Запомнил. Проблема:\n{msg.text}\nid заявки: {data}")
    else:
        bot.send_message(msg.chat.id, "Сначала выбери крыло и этаж с помощью /report!")

    query = user_state[user]["query"]
    wing = user_state[user]["wing"]
    floor = user_state[user]["floor"]
    if "_" in floor:
        floor = floor[0:floor.find('_')]

    dtw = {
            "values": [[data, query, wing, floor, 0, user]]
    }
    sheet.values().append(spreadsheetId = SHEET_ID, range = "Sheet", valueInputOption = "RAW", body = dtw).execute()

    user_state[user] = {}

bot.infinity_polling()
