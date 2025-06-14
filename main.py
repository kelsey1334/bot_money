{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # bot.py\
import logging\
import os\
import requests\
from datetime import datetime\
from telegram import Update, BotCommand\
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes\
\
# === C\uc0\u7844 U H\'ccNH ===\
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")\
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")\
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # API th\uc0\u7901 i ti\u7871 t t\u7915  OpenWeatherMap\
EXCHANGE_API_URL = "https://api.exchangerate.host/latest?base=THB&symbols=VND"  # API t\uc0\u7927  gi\'e1 THB-VND\
\
# === GHI LOG ===\
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)\
\
# === C\'c1C L\uc0\u7878 NH ===\
async def bat_dau(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    thong_diep = (\
        "\uc0\u55358 \u56598  Xin ch\'e0o! T\'f4i l\'e0 tr\u7907  l\'fd Telegram h\u7895  tr\u7907  cu\u7897 c s\u7889 ng t\u7841 i Bangkok \u55356 \u56825 \u55356 \u56813 \\n\\n"\
        "C\'e1c l\uc0\u7879 nh b\u7841 n c\'f3 th\u7875  d\'f9ng:\\n"\
        "/weather - Xem th\uc0\u7901 i ti\u7871 t h\'f4m nay\\n"\
        "/exchange - T\uc0\u7927  gi\'e1 THB \u8594  VND\\n"\
        "/quote - C\'e2u n\'f3i truy\uc0\u7873 n \u273 \u7897 ng l\u7921 c\\n"\
        "/food - G\uc0\u7907 i \'fd m\'f3n \u259 n s\'e1ng\\n"\
        "/translate <n\uc0\u7897 i dung> - D\u7883 ch TH-VI-EN\\n"\
        "/remind <n\uc0\u7897 i dung> - Nh\u7855 c vi\u7879 c (gi\u7843  l\u7853 p)\\n"\
        "/note <ghi ch\'fa> - Ghi ch\'fa nhanh"\
    )\
    await update.message.reply_text(thong_diep)\
\
async def thoi_tiet(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Bangkok&appid=\{WEATHER_API_KEY\}&units=metric"\
    res = requests.get(url).json()\
    mo_ta = res['weather'][0]['description'].capitalize()\
    nhiet_do = res['main']['temp']\
    ket_qua = f"\uc0\u55356 \u57124 \u65039  Th\u7901 i ti\u7871 t Bangkok: \{mo_ta\}, \{nhiet_do\}\'b0C"\
    await update.message.reply_text(ket_qua)\
\
async def ty_gia(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    res = requests.get(EXCHANGE_API_URL).json()\
    gia = res['rates']['VND']\
    ket_qua = f"\uc0\u55357 \u56497  100 THB \u8776  \{int(gia*100):,\} VND"\
    await update.message.reply_text(ket_qua)\
\
async def cau_noi_truyen_dong_luc(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    headers = \{"Authorization": f"Bearer \{GEMINI_API_KEY\}"\}\
    noi_dung = \{"contents": [\{"parts": [\{"text": "Give me one short motivational quote in English."\}]\}]\}\
    res = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent", json=noi_dung, headers=headers)\
    trich_dan = res.json()["candidates"][0]["content"]["parts"][0]["text"]\
    await update.message.reply_text(f"\uc0\u10024  \{trich_dan\}")\
\
async def goi_y_mon_an(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    headers = \{"Authorization": f"Bearer \{GEMINI_API_KEY\}"\}\
    noi_dung = \{"contents": [\{"parts": [\{"text": "Suggest one Thai breakfast dish with short description."\}]\}]\}\
    res = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent", json=noi_dung, headers=headers)\
    mon_an = res.json()["candidates"][0]["content"]["parts"][0]["text"]\
    await update.message.reply_text(f"\uc0\u55356 \u57180  \{mon_an\}")\
\
async def dich_ngon_ngu(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    if not context.args:\
        return await update.message.reply_text("Vui l\'f2ng nh\uc0\u7853 p n\u7897 i dung \u273 \u7875  d\u7883 ch. V\'ed d\u7909 : /translate Xin ch\'e0o")\
    van_ban = ' '.join(context.args)\
    headers = \{"Authorization": f"Bearer \{GEMINI_API_KEY\}"\}\
    prompt = f"Translate this between Thai, Vietnamese, and English automatically: \{van_ban\}"\
    body = \{"contents": [\{"parts": [\{"text": prompt\}]\}]\}\
    res = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent", json=body, headers=headers)\
    ket_qua = res.json()["candidates"][0]["content"]["parts"][0]["text"]\
    await update.message.reply_text(ket_qua)\
\
async def nhac_viec(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    cong_viec = ' '.join(context.args)\
    if not cong_viec:\
        return await update.message.reply_text("Vui l\'f2ng nh\uc0\u7853 p n\u7897 i dung c\u7847 n nh\u7855 c. V\'ed d\u7909 : /remind h\u7885 p l\'fac 2 gi\u7901  chi\u7873 u")\
    await update.message.reply_text(f"\uc0\u9200  \u272 \'e3 l\u432 u l\u7901 i nh\u7855 c: \{cong_viec\} (demo, ch\u432 a l\u432 u th\u7853 t)")\
\
async def ghi_chu(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    noi_dung = ' '.join(context.args)\
    if not noi_dung:\
        return await update.message.reply_text("Vui l\'f2ng nh\uc0\u7853 p ghi ch\'fa. V\'ed d\u7909 : /note G\u7885 i m\u7865 ")\
    await update.message.reply_text(f"\uc0\u55357 \u56541  \u272 \'e3 l\u432 u ghi ch\'fa: \{noi_dung\} (demo, ch\u432 a l\u432 u th\u7853 t)")\
\
# === KH\uc0\u7902 I \u272 \u7896 NG BOT ===\
if __name__ == '__main__':\
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()\
\
    app.add_handler(CommandHandler("start", bat_dau))\
    app.add_handler(CommandHandler("weather", thoi_tiet))\
    app.add_handler(CommandHandler("exchange", ty_gia))\
    app.add_handler(CommandHandler("quote", cau_noi_truyen_dong_luc))\
    app.add_handler(CommandHandler("food", goi_y_mon_an))\
    app.add_handler(CommandHandler("translate", dich_ngon_ngu))\
    app.add_handler(CommandHandler("remind", nhac_viec))\
    app.add_handler(CommandHandler("note", ghi_chu))\
\
    app.bot.set_my_commands([\
        BotCommand("start", "Kh\uc0\u7903 i \u273 \u7897 ng bot"),\
        BotCommand("weather", "Th\uc0\u7901 i ti\u7871 t Bangkok"),\
        BotCommand("exchange", "T\uc0\u7927  gi\'e1 THB-VND"),\
        BotCommand("quote", "C\'e2u n\'f3i truy\uc0\u7873 n \u273 \u7897 ng l\u7921 c"),\
        BotCommand("food", "G\uc0\u7907 i \'fd m\'f3n \u259 n s\'e1ng"),\
        BotCommand("translate", "D\uc0\u7883 ch ng\'f4n ng\u7919 "),\
        BotCommand("remind", "Nh\uc0\u7855 c vi\u7879 c"),\
        BotCommand("note", "Ghi ch\'fa")\
    ])\
\
    print("Bot \uc0\u273 ang ch\u7841 y...")\
    app.run_polling()}