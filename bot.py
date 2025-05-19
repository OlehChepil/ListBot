from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Спільний список записів (у пам'яті)
entries = []
entry_id_counter = 1

# Зв'язки для переписки між користувачами
user_pairs = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я бот. Використовуй /add, /list, /positive, /delete для роботи з записами. /connect <@username> — для переписки.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global entry_id_counter
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Будь ласка, введіть текст запису після команди /add")
        return
    entries.append({"id": entry_id_counter, "text": text, "status": "negative"})
    await update.message.reply_text(f"Додано запис з ID {entry_id_counter}.")
    entry_id_counter += 1

async def list_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not entries:
        await update.message.reply_text("Список порожній.")
        return
    response = "\n".join([f"{e['id']}: {e['text']} [{e['status']}]" for e in entries])
    await update.message.reply_text(response)

async def positive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        entry_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Вкажіть коректний ID: /positive <id>")
        return
    for e in entries:
        if e['id'] == entry_id:
            e['status'] = 'positive'
            await update.message.reply_text(f"Статус запису {entry_id} змінено на positive.")
            return
    await update.message.reply_text("Запис не знайдено.")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        entry_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Вкажіть коректний ID: /delete <id>")
        return
    global entries
    new_entries = [e for e in entries if e['id'] != entry_id]
    if len(new_entries) == len(entries):
        await update.message.reply_text("Запис не знайдено.")
    else:
        entries[:] = new_entries
        await update.message.reply_text(f"Запис {entry_id} видалено.")

async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Використовуйте: /connect <@username>")
        return
    from_user = update.effective_user.id
    to_username = context.args[0].lstrip('@')
    to_user = None

    for user in context.application.chat_data:
        if context.application.chat_data[user].get('username') == to_username:
            to_user = user
            break

    if not to_user:
        await update.message.reply_text("Користувача не знайдено або він ще не писав боту.")
        return

    user_pairs[from_user] = to_user
    user_pairs[to_user] = from_user
    await update.message.reply_text("Зв'язок встановлено. Тепер ваші повідомлення будуть пересилатись.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner = user_pairs.pop(user_id, None)
    if partner:
        user_pairs.pop(partner, None)
    await update.message.reply_text("Зв'язок розірвано.")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_pairs:
        partner_id = user_pairs[user_id]
        try:
            await context.bot.send_message(chat_id=partner_id, text=update.message.text)
        except Exception as e:
            await update.message.reply_text("Не вдалося надіслати повідомлення користувачу.")

async def store_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.application.chat_data[update.effective_user.id] = {'username': update.effective_user.username}

if __name__ == '__main__':
    app = ApplicationBuilder().token("7561246127:AAEgKE1s61hM9d3si2eQ1gSECX5cMdC_-bM").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_entries))
    app.add_handler(CommandHandler("positive", positive))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("connect", connect))
    app.add_handler(CommandHandler("stop", stop))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
    app.add_handler(MessageHandler(filters.ALL, store_username))

    app.run_polling()
