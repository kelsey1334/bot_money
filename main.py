import logging
import json
from datetime import datetime, timedelta
from pytz import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

# Kết nối Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_NAME = "Chi tiêu cá nhân"
creds = Credentials.from_service_account_file("rosy-cache-462916-t6-be560f1dfced.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME)
sheet_thu = sheet.worksheet("Thu")
sheet_chi = sheet.worksheet("Chi")

# Biến lưu tạm số tiền chờ người dùng chọn danh mục
pending_data = {}

# Hàm lưu dữ liệu vào Google Sheets
def save_transaction_to_sheets(user_id, amount, category, trans_type):
    today = datetime.now(timezone('Asia/Ho_Chi_Minh')).strftime("%Y-%m-%d")
    row = [today, str(user_id), amount, category]
    if trans_type == "in":
        sheet_thu.append_row(row)
    else:
        sheet_chi.append_row(row)

# Lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào bạn! Nhập /in [số tiền] hoặc /out [số tiền] để ghi chi tiêu nhé.")

# Lệnh /in
async def income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        user_id = update.message.from_user.id
        pending_data[user_id] = {"amount": amount, "type": "in"}
        keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in ["Lương", "Bán hàng", "Thu nợ", "Được cho"]]
        await update.message.reply_text("Nguồn tiền từ đâu?", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("Sai cú pháp. Hãy dùng: /in [số tiền]")

# Lệnh /out
async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        user_id = update.message.from_user.id
        pending_data[user_id] = {"amount": amount, "type": "out"}
        keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in ["Tiền đi lại", "Ăn uống", "Mua sắm", "Y tế", "Việc riêng", "Đi chơi"]]
        await update.message.reply_text("Khoản chi này là gì?", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("Sai cú pháp. Hãy dùng: /out [số tiền]")

# Xử lý lựa chọn danh mục
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id in pending_data:
        amount = pending_data[user_id]["amount"]
        action = pending_data[user_id]["type"]
        category = query.data
        save_transaction_to_sheets(user_id, amount, category, action)
        await query.edit_message_text(f"✅ Đã ghi {'thu' if action == 'in' else 'chi'}: {amount}đ - {category}")
        del pending_data[user_id]
    else:
        await query.edit_message_text("❌ Không tìm thấy dữ liệu giao dịch.")

# Hàm chạy bot
async def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", income))
    app.add_handler(CommandHandler("out", expense))
    app.add_handler(CallbackQueryHandler(button_handler))

    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
