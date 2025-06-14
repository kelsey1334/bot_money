import os
import json
from datetime import datetime, timedelta
from pytz import timezone

import nest_asyncio
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

from apscheduler.schedulers.background import BackgroundScheduler

# -------------------- Quản lý dữ liệu --------------------
DATA_FILE = "expenses.json"

def read_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def today_str():
    return datetime.now(timezone('Asia/Ho_Chi_Minh')).strftime("%Y-%m-%d")

def save_transaction(user_id, amount, category, trans_type):
    data = read_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"in": {}, "out": {}}
    date = today_str()
    if date not in data[user_id][trans_type]:
        data[user_id][trans_type][date] = []
    data[user_id][trans_type][date].append({"amount": amount, "category": category})
    write_data(data)

# -------------------- Bot command --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Xin chào! Dùng lệnh:\n/in [số tiền]\n/out [số tiền]")

async def handle_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        context.user_data["in_amount"] = amount
        keyboard = [
            [InlineKeyboardButton("Lương", callback_data="in|Lương")],
            [InlineKeyboardButton("Bán hàng", callback_data="in|Bán hàng")],
            [InlineKeyboardButton("Thu nợ", callback_data="in|Thu nợ")],
            [InlineKeyboardButton("Được cho", callback_data="in|Được cho")]
        ]
        await update.message.reply_text("📥 Nguồn thu?", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("❗ Sai cú pháp. Dùng: /in 500000")

async def handle_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(context.args[0])
        context.user_data["out_amount"] = amount
        keyboard = [
            [InlineKeyboardButton("Tiền đi lại", callback_data="out|Tiền đi lại")],
            [InlineKeyboardButton("Ăn uống", callback_data="out|Ăn uống")],
            [InlineKeyboardButton("Mua sắm", callback_data="out|Mua sắm")],
            [InlineKeyboardButton("Y tế", callback_data="out|Y tế")],
            [InlineKeyboardButton("Việc riêng", callback_data="out|Việc riêng")],
            [InlineKeyboardButton("Đi chơi", callback_data="out|Đi chơi")]
        ]
        await update.message.reply_text("📤 Chi vào đâu?", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("❗ Sai cú pháp. Dùng: /out 200000")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, category = query.data.split("|")
    amount = context.user_data.get(f"{action}_amount", 0)
    save_transaction(query.from_user.id, amount, category, action)
    await query.edit_message_text(f"✅ Đã ghi {amount:,}đ vào mục: {category}")

# -------------------- Hẹn giờ báo cáo --------------------
async def daily_report(application):
    data = read_data()
    for user_id, user_data in data.items():
        uid = int(user_id)
        today = (datetime.now(timezone('Asia/Ho_Chi_Minh')) - timedelta(days=1)).strftime("%Y-%m-%d")
        month_prefix = today[:7]
        message = f"📊 Báo cáo chi tiêu ngày {today}:\n\n"

        # Chi tiết hôm qua
        in_today = user_data["in"].get(today, [])
        out_today = user_data["out"].get(today, [])
        total_in = sum(i["amount"] for i in in_today)
        total_out = sum(i["amount"] for i in out_today)

        message += f"➕ Thu: {total_in:,}đ ({len(in_today)} mục)\n"
        message += f"➖ Chi: {total_out:,}đ ({len(out_today)} mục)\n\n"

        # Thống kê tháng
        month_in = sum(
            i["amount"] for d, lst in user_data["in"].items() if d.startswith(month_prefix) for i in lst
        )
        month_out = sum(
            i["amount"] for d, lst in user_data["out"].items() if d.startswith(month_prefix) for i in lst
        )

        message += f"📅 Tổng tháng {month_prefix}:\n"
        message += f"✅ Thu: {month_in:,}đ\n"
        message += f"❌ Chi: {month_out:,}đ\n"

        try:
            await application.bot.send_message(chat_id=uid, text=message)
        except Exception as e:
            print(f"Không thể gửi báo cáo cho user {uid}: {e}")

# -------------------- Khởi chạy bot --------------------
async def main():
    TOKEN = os.environ["BOT_TOKEN"]
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", handle_in))
    app.add_handler(CommandHandler("out", handle_out))
    app.add_handler(CallbackQueryHandler(button_handler))

    scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(lambda: asyncio.create_task(daily_report(app)), 'cron', hour=8, minute=0)
    scheduler.start()

    print("🤖 Bot đang chạy...")
    await app.run_polling()

# -------------------- Chạy --------------------
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
