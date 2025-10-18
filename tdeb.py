from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import datetime

ASKING_PHOTO = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Type /askphoto to send me a photo (as image or file).")

async def ask_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send me a photo — either as an image or as a file.")
    return ASKING_PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Case 1: Sent as a normal photo
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        filename = f"telegram-images/{user.username or user.id}_{timestamp}.jpg"
        await photo_file.download_to_drive(filename)
        await update.message.reply_text(f"✅ Photo saved as {filename}")
        return ConversationHandler.END

    # Case 2: Sent as a file/document (uncompressed image)
    elif update.message.document and update.message.document.mime_type.startswith("image/"):
        doc_file = await update.message.document.get_file()
        filename = f"telegram-images/{user.username or user.id}_{timestamp}_{update.message.document.file_name}"
        await doc_file.download_to_drive(filename)
        await update.message.reply_text(f"✅ Image file saved as {filename}")
        return ConversationHandler.END

    else:
        await update.message.reply_text("❌ That’s not a valid image. Please send a photo or image file.")
        return ASKING_PHOTO

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Conversation cancelled.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("8167997146:AAE21KqvTiqQVJP5FDB6uEcFnJ5g1xvdK8U").build()

    photo_handler = ConversationHandler(
        entry_points=[CommandHandler("askphoto", ask_photo)],
        states={
            ASKING_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                MessageHandler(filters.Document.IMAGE, receive_photo)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(photo_handler)

    print("🤖 Bot running... send /askphoto to test.")
    app.run_polling()

if __name__ == "__main__":
    main()
