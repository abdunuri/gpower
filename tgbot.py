# gpower_bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ConversationHandler, ContextTypes
)
import os
import sqlite3
from datetime import datetime
import json
import asyncio
from PIL import Image

# Conversation states
PHOTO, HEADING, CAPTION, CONFIRM = range(4)

# Database setup
def init_db():
    conn = sqlite3.connect('blog_posts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_path TEXT NOT NULL,
            heading TEXT NOT NULL,
            caption TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_published BOOLEAN DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def save_post_to_db(photo_path, heading, caption):
    conn = sqlite3.connect('blog_posts.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO blog_posts (photo_path, heading, caption)
        VALUES (?, ?, ?)
    ''', (photo_path, heading, caption))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_all_posts():
    conn = sqlite3.connect('blog_posts.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, photo_path, heading, caption, created_at 
        FROM blog_posts 
        WHERE is_published = 1 
        ORDER BY created_at DESC
    ''')
    posts = cursor.fetchall()
    conn.close()
    return posts

# Optimize image
def optimize_image(image_path, max_size=(1200, 1200), quality=85):
    try:
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            optimized_path = image_path.replace('.jpg', '_optimized.jpg')
            img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
            return optimized_path
    except Exception as e:
        print(f"Image optimization failed: {e}")
        return image_path

# --- Start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *G-Power Blog Bot*\n\n"
        "Welcome! I help you manage blog posts for G-Power Ethiopia.\n\n"
        "Available commands:\n"
        "• /start - Show this message\n"
        "• /post - Create a new blog post\n"
        "• /list - Show recent posts\n"
        "• /cancel - Cancel current operation\n\n"
        "Use /post to start creating content!",
        parse_mode="Markdown"
    )

# --- Post command ---
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 *Let's create a blog post!*\n\n"
        "Please send me the photo for your blog post.\n\n"
        "💡 *Tip:* For best results, send images under 5MB.",
        parse_mode="Markdown"
    )
    return PHOTO

# --- Receive photo ---
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo_file = await update.message.photo[-1].get_file()
        
        # Create images directory
        os.makedirs("images/tg", exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_path = f"images/tg/blog_{timestamp}.jpg"
        
        # Download image
        await photo_file.download_to_drive(photo_path)
        
        # Optimize image
        optimized_path = optimize_image(photo_path)
        
        context.user_data["photo_path"] = photo_path
        context.user_data["optimized_path"] = optimized_path

        await update.message.reply_text("✅ *Photo received!*\n\nNow send me the heading (title). 📰", parse_mode="Markdown")
        return HEADING
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\nPlease try again with /post")
        return ConversationHandler.END

# --- Receive heading ---
async def receive_heading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["heading"] = update.message.text
    await update.message.reply_text("📝 *Heading received!*\n\nNow send me the detailed caption/description. ✍️", parse_mode="Markdown")
    return CAPTION

# --- Receive caption ---
async def receive_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["caption"] = update.message.text

    photo = context.user_data.get("optimized_path") or context.user_data.get("photo_path")
    heading = context.user_data["heading"]
    caption = context.user_data["caption"]

    # Create preview
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Post", callback_data="confirm"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open(photo, "rb") as image_file:
            await update.message.reply_photo(
                photo=InputFile(image_file),
                caption=f"📰 *Blog Post Preview*\n\n*{heading}*\n\n{caption}",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating preview: {str(e)}")
        return ConversationHandler.END

    return CONFIRM

# --- Handle confirmation ---
async def confirm_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm":
        photo = context.user_data.get("optimized_path") or context.user_data.get("photo_path")
        heading = context.user_data["heading"]
        caption = context.user_data["caption"]

        try:
            # Save to database
            post_id = save_post_to_db(photo, heading, caption)
            
            # Generate JSON file
            generate_posts_json()

            await query.edit_message_caption(
                caption=f"✅ *Post Published Successfully!*\n\n"
                       f"*{heading}*\n\n"
                       f"Post ID: #{post_id}\n"
                       f"The post is now live on the G-Power website! 🎉",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            await query.edit_message_caption(
                caption=f"❌ *Error saving post:* {str(e)}"
            )
            
    else:
        # Clean up files if canceled
        photo_path = context.user_data.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
        optimized_path = context.user_data.get("optimized_path")
        if optimized_path and os.path.exists(optimized_path):
            os.remove(optimized_path)
            
        await query.edit_message_caption(caption="❌ Post creation canceled.")
    
    context.user_data.clear()
    return ConversationHandler.END

# --- Generate JSON file ---
def generate_posts_json():
    try:
        posts = get_all_posts()
        posts_data = []
        
        for post in posts:
            post_id, photo_path, heading, caption, created_at = post
            posts_data.append({
                'id': post_id,
                'photo_path': photo_path,
                'heading': heading,
                'caption': caption,
                'created_at': created_at
            })
        
        with open('blog_posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error generating JSON: {e}")

# --- List posts ---
async def list_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = get_all_posts()
    
    if not posts:
        await update.message.reply_text("📭 No blog posts found.")
        return
    
    message = "📝 *Recent Blog Posts:*\n\n"
    for post in posts[:5]:
        post_id, photo_path, heading, caption, created_at = post
        date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y')
        message += f"*#{post_id}* - {heading}\n"
        message += f"📅 {date}\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# --- Cancel command ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Clean up files
    photo_path = context.user_data.get("photo_path")
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)
    optimized_path = context.user_data.get("optimized_path")
    if optimized_path and os.path.exists(optimized_path):
        os.remove(optimized_path)
    
    await update.message.reply_text("❌ Operation canceled.")
    context.user_data.clear()
    return ConversationHandler.END

# --- Error handler ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ An error occurred. Please try again.")
    except:
        pass

def main():
    # Initialize database
    init_db()
    print("G-Power Blog Bot starting...")
    
    # Create application
    application = Application.builder()\
        .token("8076860650:AAEprRHsyLQFya7gZjQItySYtEyHHX8UsV8")\
        .read_timeout(30)\
        .write_timeout(30)\
        .build()

    # Conversation handler for post creation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("post", post)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            HEADING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_heading)],
            CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_caption)],
            CONFIRM: [CallbackQueryHandler(confirm_post)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_posts))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    print("✅ G-Power Blog Bot is running successfully!")
    print("🤖 Bot: @automationanbubot")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()