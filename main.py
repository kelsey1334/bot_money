import os
import json
from datetime import datetime, timedelta
from pytz import timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

from apscheduler.schedulers.background import BackgroundScheduler

# Đường dẫn file dữ liệu
DATA_FILE = "expenses.json"

# Hàm đọc dữ liệu
def read_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Hàm ghi dữ liệu
def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Format ngày theo giờ VN
def today_str():
    return datetime.now(timezone('Asia/Ho_Chi_Minh')).strftime("%Y-%m-%d")

# Lưu dữ liệu vào file
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

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào bạn! Dùng lệnh:\n/in [số tiền]\n/out [số tiền]")

# /in
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
        await update.message.reply_text("Nguồn thu?", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("Sai cú pháp. Dùng: /in 500000")

# /out
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
        await update.message.reply_text("Chi tiêu vào đâu?", reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await update.message.reply_text("Sai cú pháp. Dùng: /out 200000")

# Xử lý chọn hạng mục
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, category = query.data.split("|")
    amount = context.user_data.get(f"{action}_amount", 0)
    save_transaction(query.from_user.id, amount, category, action)
    await query.edit_message_text(f"Đã ghi nhận {action} {amount:,}đ vào mục: {category}")

# Gửi báo cáo hằng ngày
async def daily_report(application):
    data = read_data()
    for user_id, user_data in data.items():
        uid = int(user_id)
        today = (datetime.now(timezone('Asia/Ho_Chi_Minh')) - timedelta(days=1)).strftime("%Y-%m-%d")
        month_prefix = today[:7]
        message = f"📊 Báo cáo chi tiêu ngày {today}:\n\n"

        # Ngày hôm qua
        in_today = user_data["in"].get(today, [])
        out_today = user_data["out"].get(today, [])
        total_in = sum(i["amount"] for i in in_today)
        total_out = sum(i["amount"] for i in out_today)

        message += f"✅ Thu: {total_in:,}đ từ {len(in_today)} khoản\n"
        message += f"❌ Chi: {total_out:,}đ từ {len(out_today)} khoản\n\n"

        # Tháng
        month_in = sum(
            i["amount"] for d, lst in user_data["in"].items() if d.startswith(month_prefix) for i in lst
        )
        month_out = sum(
            i["amount"] for d, lst in user_data["out"].items() if d.startswith(month_prefix) for i in lst
        )

        message += f"📅 Tổng tháng {month_prefix}:\n"
        message += f"➕ Thu: {month_in:,}đ\n"
        message += f"➖ Chi: {month_out:,}đ\n"
        try:
            await application.bot.send_message(chat_id=uid, text=message)
        except:
            pass

# Hàm chính
async def main():
    TOKEN = os.environ["BOT_TOKEN"]
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", handle_in))
    app.add_handler(CommandHandler("out", handle_out))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Scheduler báo cáo mỗi 8h sáng giờ VN
    scheduler = BackgroundScheduler(timezone='Asia/Ho_Chi_Minh')
    scheduler.add_job(lambda: daily_report(app), 'cron', hour=8, minute=0)
    scheduler.start()

    print("Bot đang chạy...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
