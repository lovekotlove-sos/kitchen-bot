# Создай файл:
touch webhook.py
import os
from flask import Flask, request
from telegram import Update, Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import asyncio

# Загружаем секреты
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "920573512"))

app = Flask(__name__)
bot = Bot(TOKEN)
application = Application.builder().token(TOKEN).build()

# === ТВОИ ФУНКЦИИ (скопируй из bot.py) ===
# ВСТАВЬ СЮДА ВСЁ ОТ async def start ДО async def cancel

# (S, M, C...) = range(8)
(SIZE, MATERIAL, COLOR, COUNTERTOP, HARDWARE, APPLIANCES, PHOTO, CONFIRM) = range(8)

material_keyboard = ReplyKeyboardMarkup([['МДФ', 'Массив дерева'], ['ЛДСП', 'Акрил']], resize_keyboard=True, one_time_keyboard=True)
color_keyboard = ReplyKeyboardMarkup([['Белый глянец', 'Серый матовый'], ['Дуб сонома', 'Чёрный']], resize_keyboard=True, one_time_keyboard=True)
countertop_keyboard = ReplyKeyboardMarkup([['Иск. камень', 'ЛДСП'], ['Натуральный камень', 'Дерево']], resize_keyboard=True, one_time_keyboard=True)
hardware_keyboard = ReplyKeyboardMarkup([['Blum', 'Hettich'], ['Китай (эконом)', 'Без фурнитуры']], resize_keyboard=True, one_time_keyboard=True)
appliances_keyboard = ReplyKeyboardMarkup([['Встроенная (духовка, варка)', 'Отдельностоящая'], ['Без техники']], resize_keyboard=True, one_time_keyboard=True)
confirm_keyboard = ReplyKeyboardMarkup([['Подтвердить', 'Отменить']], resize_keyboard=True, one_time_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /order, чтобы заказать кухню.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1. Укажи размеры (длина × ширина × высота):", reply_markup=ReplyKeyboardRemove())
    return SIZE

async def size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['size'] = update.message.text
    await update.message.reply_text("2. Материал фасадов:", reply_markup=material_keyboard)
    return MATERIAL

async def material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['material'] = update.message.text
    await update.message.reply_text("3. Цвет:", reply_markup=color_keyboard)
    return COLOR

async def color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['color'] = update.message.text
    await update.message.reply_text("4. Столешница:", reply_markup=countertop_keyboard)
    return COUNTERTOP

async def countertop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['countertop'] = update.message.text
    await update.message.reply_text("5. Фурнитура:", reply_markup=hardware_keyboard)
    return HARDWARE

async def hardware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hardware'] = update.message.text
    await update.message.reply_text("6. Бытовая техника:", reply_markup=appliances_keyboard)
    return APPLIANCES

async def appliances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['appliances'] = update.message.text
    await update.message.reply_text("7. Пришлите фото кухни (или напишите 'без фото'):")
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id
        await update.message.reply_text("Фото получено!")
    else:
        context.user_data['photo'] = None
        await update.message.reply_text("Фото не получено.")

    # Расчёт цены
    size = context.user_data['size']
    try:
        l, w, h = map(float, size.replace('×', 'x').split('x'))
        area = l * w * 2 + l * h * 2 + w * h * 2
    except:
        area = 10
    prices = {
        'МДФ': 80000, 'Массив дерева': 150000, 'ЛДСП': 50000, 'Акрил': 100000,
        'Иск. камень': 30000, 'ЛДСП': 10000, 'Натуральный камень': 80000, 'Дерево': 40000,
        'Blum': 20000, 'Hettich': 15000, 'Китай (эконом)': 5000, 'Без фурнитуры': 0,
        'Встроенная (духовка, варка)': 40000, 'Отдельностоящая': 20000, 'Без техники': 0
    }
    total = area * 5000
    total += prices.get(context.user_data['material'], 0)
    total += prices.get(context.user_data['countertop'], 0)
    total += prices.get(context.user_data['hardware'], 0)
    total += prices.get(context.user_data['appliances'], 0)
    context.user_data['total'] = total

    summary = (
        f"Заказ принят!\n\n"
        f"Кухня: {context.user_data['size']}\n"
        f"Фасады: {context.user_data['material']}\n"
        f"Цвет: {context.user_data['color']}\n"
        f"Столешница: {context.user_data['countertop']}\n"
        f"Фурнитура: {context.user_data['hardware']}\n"
        f"Техника: {context.user_data['appliances']}\n"
        f"Цена: ~{int(total):,} ₽"
    )
    if context.user_data['photo']:
        await update.message.reply_photo(context.user_data['photo'], caption=summary, reply_markup=confirm_keyboard)
    else:
        await update.message.reply_text(summary, reply_markup=confirm_keyboard)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    summary = (
        f"НОВЫЙ ЗАКАЗ ОТ КЛИЕНТА\n\n"
        f"Клиент: {update.effective_user.first_name} (@{update.effective_user.username or 'нет'})\n"
        f"Кухня: {user_data['size']}\n"
        f"Фасады: {user_data['material']}\n"
        f"Цвет: {user_data['color']}\n"
        f"Столешница: {user_data['countertop']}\n"
        f"Фурнитура: {user_data['hardware']}\n"
        f"Техника: {user_data['appliances']}\n"
        f"Цена: ~{int(user_data['total']):,} ₽"
    )
    if 'Подтвердить' in update.message.text:
        await update.message.reply_text("Заказ подтверждён! Скоро свяжемся.")
    else:
        await update.message.reply_text("Заказ отменён.")
        return ConversationHandler.END

    try:
        if user_data['photo']:
            await context.bot.send_photo(ADMIN_CHAT_ID, user_data['photo'], caption=summary)
        else:
            await context.bot.send_message(ADMIN_CHAT_ID, summary)
    except Exception as e:
        print(f"Ошибка: {e}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заказ отменён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# === Хендлеры ===
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('order', order)],
    states={
        SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, size)],
        MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, material)],
        COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, color)],
        COUNTERTOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, countertop)],
        HARDWARE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hardware)],
        APPLIANCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, appliances)],
        PHOTO: [MessageHandler(filters.TEXT | filters.PHOTO, photo)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

application.add_handler(CommandHandler('start', start))
application.add_handler(conv_handler)

# === Вебхук ===
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return 'OK', 200

@app.route('/')
def index():
    return "Бот работает 24/7!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
