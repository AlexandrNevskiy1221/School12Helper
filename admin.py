from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import telebot
import telebot.types as types
import os
load_dotenv()

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
    data = sheet.values().get(spreadsheetId = SHEET_ID, range = "Sheet!A3:E").execute()
    if data.get('values') == None:
        bot.send_message(uid, "Проблем нет!")
    else:
        head = "id | описание | крыло | этаж | статус"
        wings = {
                "left": "левое",
                "right": "правое"
        }
        floors = {
                "third": "третий", 
                "second": "второй", 
                "first": "первый", 
                "zero": "мастерские"
        }
        statuses = {
                '0': "открыта",
                '1': "закрыта"
        }
        body = "\n".join(f"{qid} | {txt} | {wings[wing]} | {floors[floor]} | {statuses[status]}" for qid, txt, wing, floor, status in data['values'])
        foot = "Ты можешь закрыть заявку с помощью /close"
        text = f"{head}\n{body}\n{foot}"
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
        range="Sheet!A2:A"
    ).execute().get("values", [])

    row = None
    for i, val in enumerate(data, start=2):
        if val[0] == qid:
            row = i
            break

    if row is None:
        bot.send_message(uid, "Заявка не найдена.")
        return

    sheet.values().update(
        spreadsheetId=SHEET_ID,
        range=f"Sheet!E{row}",
        valueInputOption="RAW",
        body={"values": [["1"]]}
    ).execute()

    bot.send_message(uid, f"Заявка #{qid} закрыта.")


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
