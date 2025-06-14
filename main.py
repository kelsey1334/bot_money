import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
import gspread
from google.oauth2.service_account import Credentials

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Google Sheets Setup ===
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds_json = os.getenv("GOOGLE_CREDS")
creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_NAME = os.getenv("SHEET_NAME", "ChiTieu")
worksheet = gc.open(SHEET_NAME).sheet1

# === Category Options ===
IN_CATEGORIES = ["Lương", "Bán hàng", "Thu nợ", "Được cho"]
OUT_CATEGORIES = ["Tiền đi lại", "Ăn uống", "Mua sắm", "Y tế", "Việc riêng", "Đi chơi"]

# === Store temporary data ===
user_data = {}

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào bạn! Dùng /in hoặc /out để ghi thu chi.")

# === /in ===
async def handle_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
    except:
        await update.message.reply_text("Vui lòng nhập số tiền: /in 500000")
        return
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"in|{amount}|{cat}")]
                for cat in IN_CATEGORIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Nguồn tiền đến từ đâu?", reply_markup=reply_markup)

# === /out ===
async def handle_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
    except:
        await update.message.reply_text("Vui lòng nhập số tiền: /out 200000")
        return
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"out|{amount}|{cat}")]
                for cat in OUT_CATEGORIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Tiền đã dùng vào đâu?", reply_markup=reply_markup)

# === Callback for category selection ===
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, amount, category = query.data.split("|")
    now = datetime.utcnow() + timedelta(hours=7)  # Giờ VN
    worksheet.append_row([now.strftime("%Y-%m-%d %H:%M:%S"), action, amount, category])
    await query.edit_message_text(f"✅ Đã ghi nhận {action.upper()} {amount} vào '{category}'")

# === Daily summary ===
async def daily_summary(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow() + timedelta(hours=7)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    month = now.strftime("%Y-%m")

    data = worksheet.get_all_records()
    in_yesterday = sum(float(row['amount']) for row in data
                       if row['type'] == 'in' and row['timestamp'].startswith(yesterday))
    out_yesterday = sum(float(row['amount']) for row in data
                        if row['type'] == 'out' and row['timestamp'].startswith(yesterday))
    in_month = sum(float(row['amount']) for row in data
                   if row['type'] == 'in' and row['timestamp'].startswith(month))
    out_month = sum(float(row['amount']) for row in data
                    if row['type'] == 'out' and row['timestamp'].startswith(month))

    msg = (
        f"📊 *Tổng kết ngày {yesterday}*\n"
        f"🟢 Thu hôm qua: {in_yesterday:,.0f} đ\n"
        f"🔴 Chi hôm qua: {out_yesterday:,.0f} đ\n\n"
        f"📅 *Tháng này*\n"
        f"🟢 Tổng thu: {in_month:,.0f} đ\n"
        f"🔴 Tổng chi: {out_month:,.0f} đ"
    )
    await context.bot.send_message(chat_id=context.job.chat_id, text=msg, parse_mode="Markdown")

# === /subscribe ===
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    time = datetime.time(hour=8, tzinfo=datetime.timezone(timedelta(hours=7)))
    context.job_queue.run_daily(daily_summary, time=time, chat_id=chat_id)
    await update.message.reply_text("✅ Bạn đã đăng ký nhận báo cáo hằng ngày lúc 8h sáng.")

# === Main ===
async def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", handle_in))
    app.add_handler(CommandHandler("out", handle_out))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CallbackQueryHandler(button))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
