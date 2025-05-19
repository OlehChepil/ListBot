import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

# Заміни цей токен своїм
BOT_TOKEN = "7561246127:AAEgKE1s61hM9d3si2eQ1gSECX5cMdC_-bM"

# Глобальні словники
user_data = {}  # username → user_id
connected_users = {}  # user_id → user_id

# Налаштування логів
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# /start — зберігає username користувача
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username:
        user_data[user.username.lower()] = user.id
        await update.message.reply_text(f"Привіт, @{user.username}! Вас зареєстровано ✅")
    else:
        await update.message.reply_text("У вас немає username — встановіть його в Telegram ⚠️")

# /connect @username — встановлює з’єднання
async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Вкажіть username користувача. Наприклад:\n/connect @username")
        return

    target_username = context.args[0].lstrip('@').lower()
    sender_id = update.effective_user.id

    if target_username not in user_data:
        await update.message.reply_text("Користувач не знайдений або не писав боту 😕")
        return

    receiver_id = user_data[target_username]

    connected_users[sender_id] = receiver_id
    connected_users[receiver_id] = sender_id

    await update.message.reply_text(f"🔗 Ви підключились до @{target_username}")
    try:
        await context.bot.send_message(chat_id=receiver_id, text=f"🔗 @{update.effective_user.username} підключився до вас")
    except Exception as e:
        logger.error("Не вдалося надіслати повідомлення: %s", e)

# /stop — роз'єднує користувачів
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = connected_users.pop(user_id, None)

    if partner_id:
        connected_users.pop(partner_id, None)
        await context.bot.send_message(chat_id=partner_id, text="❌ Співрозмовник завершив діалог.")
        await update.message.reply_text("Ви завершили діалог.")
    else:
        await update.message.reply_text("Ви не підключені до жодного користувача.")

# Пересилання повідомлень
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    partner_id = connected_users.get(sender_id)

    if partner_id:
        try:
            await context.bot.send_message(chat_id=partner_id, text=update.message.text)
        except Exception as e:
            logger.error("Не вдалося переслати повідомлення: %s", e)
    else:
        await update.message.reply_text("Ви не підключені до жодного користувача. Використайте /connect")

# Запуск бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("connect", connect))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    print("✅ Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()
