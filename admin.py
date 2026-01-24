from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import telebot
import pickle
import re
import telebot.types as types
import os
load_dotenv()

with open("misc/categories.pkl", "rb") as f:
    vectorizer, model = pickle.load(f)

creds = Credentials.from_service_account_file(
    "creds.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

service = build("sheets", "v4", credentials=creds)
SHEET_ID = "15-GVlpKITU5Tq_M_8tWo9Ko9H9IWUpaJEUn-J15GiQ0"
sheet = service.spreadsheets()

API_TOKEN = os.getenv("ADMIN_TOKEN")
bot = telebot.TeleBot(API_TOKEN)
password = os.getenv("ADMIN_PASSWORD")
admin_state = {}


def list_queries(uid):
    data = sheet.values().get(spreadsheetId=SHEET_ID, range="Sheet!A3:E").execute()
    if not data.get('values'):
        bot.send_message(uid, "Проблем нет!")
        return

    head = "id | описание | крыло | этаж | статус"
    wings = {"left": "левое", "right": "правое"}
    floors = {"third": "третий", "second": "второй", "first": "первый", "zero": "мастерские"}
    statuses = {'0': "открыта", '1': "закрыта"}

    body_lines = []
    categories_count = {}
    rooms_count = {}

    for qid, txt, wing, floor, status in data['values']:
        body_lines.append(f"{qid} | {txt} | {wings[wing]} | {floors[floor]} | {statuses[status]}")
        if status == '0':
            cat = model.predict(vectorizer.transform([txt]))[0]
            categories_count[cat] = categories_count.get(cat, 0) + 1

            rooms = re.findall(r'\b\d+\b', txt)
            for room in rooms:
                rooms_count[room] = rooms_count.get(room, 0) + 1

    body = "\n".join(body_lines)

    stats_lines = ["Статистика открытых проблем по категориям:"]
    for cat, c in categories_count.items():
        stats_lines.append(f"{cat}: {c}")

    stats_lines.append("\nСтатистика по кабинетам:")
    for room, c in rooms_count.items():
        stats_lines.append(f"{room} кабинет: {c}")

    stats_text = "\n".join(stats_lines)
    foot = "Ты можешь закрыть заявку с помощью /close"
    text = f"{head}\n{body}\n\n{stats_text}\n\n{foot}"
    bot.send_message(uid, text)

@bot.message_handler(commands=["start"])
def send_welcome(msg):
    uid = msg.from_user.id
    admin_state[uid] = {
        "entering_pass": False,
        "is_admin": False
    }
    bot.send_message(uid, "Привет. Для доступа к проблемам школы, используй команду /login. Если ты думаешь, что попал сюда случайно - то перейди в этого бота @School12Support_bot")

@bot.message_handler(commands=["login"])
def login(msg):
    uid = msg.from_user.id
    admin_state.setdefault(uid, {})
    admin_state[uid]["entering_pass"] = True
    bot.send_message(uid, "Введи пароль: ")

@bot.message_handler(commands=["close"])
def close_query(msg):
    uid = msg.from_user.id
    state = admin_state.get(uid)

    if not state or not state.get("is_admin"):
        bot.send_message(uid, "Сначала /login, потом команды.")
        return

    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.send_message(uid, "Формат: /close <id>")
        return

    qid = parts[1]

    data = sheet.values().get(
        spreadsheetId=SHEET_ID,
        range="Sheet!A2:F"
    ).execute().get("values", [])

    row = None
    status = None
    for i, val in enumerate(data, start=2):
        if val[0] == qid:
            row = i
            status = val[4]
            uts = int(val[5])
            break
    if status == '1':
        bot.send_message(uid, f"Заявка №{qid} уже закрыта.")
        return

    if row is None:
        bot.send_message(uid, "Заявка не найдена.")
        return

    sheet.values().update(
        spreadsheetId=SHEET_ID,
        range=f"Sheet!E{row}",
        valueInputOption="RAW",
        body={"values": [["1"]]}
    ).execute()

    supBot = telebot.TeleBot(os.getenv("SUPPORT_TOKEN"))
    supBot.send_message(uts, f"Твоя заявка №{qid} закрыта!")

    bot.send_message(uid, f"Заявка №{qid} закрыта.")

@bot.message_handler(commands=["list"])
def list(msg):
    state = admin_state.get(msg.from_user.id)
    if state.get("is_admin") != None and state.get('is_admin') != False:
        list_queries(msg.from_user.id)
    else:
        bot.send_message(msg.from_user.id, "Недостаточно прав! Введи пароль с помощью /login или сообщи о проблеме в @School12SupportBot")


@bot.message_handler(content_types=["text"])
def answ(msg):
    uid = msg.from_user.id
    state = admin_state.get(uid)

    if not state or not state.get("entering_pass"):
        bot.reply_to(msg, "Я не понимаю чего ты хочешь")
        return

    if msg.text == password:
        state["entering_pass"] = False
        state["is_admin"] = True
        bot.send_message(uid, f"Добро пожаловать, {msg.from_user.first_name}")
        list_queries(uid)
    else:
        bot.send_message(uid, "Пароль неверный!")


bot.infinity_polling()
