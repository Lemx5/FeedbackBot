from pyrogram import Client, filters
from flask import Flask, redirect
from threading import Thread
import os

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN = int(os.getenv("ADMIN"))
BOT_USERNAME = os.getenv("BOT_USERNAME")

web = Flask(__name__)

app = Client(
    "feedbackbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN)


@app.on_message(filters.command("reply"))
async def send_message_user(client, message):
    try:
        if message.from_user.id != ADMIN:
            return await message.reply("You are not allowed to use this command.")
        
        if len(message.command) < 2:
            return await message.reply("Please provide a user id.")
        
        if len(message.command) < 3:
            text_message = str(message.command[2])
        
        user_id = int(message.command[1])
        user = await app.get_users(user_id)

        if not user:
            return await message.reply("Invalid user id")

        msg = message.reply_to_message

        if not msg:
            return await message.reply("Please reply to a message.")

        if msg.text:
            await app.send_message(user_id, text=msg.text)

        media = (
            msg.photo or
            msg.video or
            msg.audio or
            msg.document or
            msg.animation
        )
        caption = msg.caption if msg.caption else None

        if media and text_message:
            await message.reply(
                chat_id = user_id,
                text = f"{text_message}",
                reply_to_message_id = msg.id
            )

        if media:
            await media.copy(
                chat_id=user_id,
                caption=caption
            )

        await message.reply(f"**Message sent to {user.first_name} successfully.**")

    except Exception as e:
        await message.reply(f"An unexpected error occurred: {str(e)}")


@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(f"**Hello {message.from_user.first_name}!\nI am a support bot. Send me a message and I will forward it to my Admin.**")


@app.on_message(filters.private)
async def forward(client, message):
    if message.text and message.text.startswith("/"):
        return
    
    if message.from_user.id == ADMIN:
        return
    
    caption = message.caption if message.caption else None

    if message.reply_to_message:
        replied_msg = message.reply_to_message
        reply_caption = replied_msg.caption if replied_msg.caption else None

        # Forward the replied message along with the user's reply
        await replied_msg.copy(
            chat_id=ADMIN,
            caption=f"<b>Original Message:</b>\n{reply_caption}\n\n<b>User's Reply:</b>\n{caption}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>"
        )
    else:
        # Forward the user's message
        await message.copy(
            chat_id=ADMIN,
            caption=f"<b>Message:</b>\n{caption}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>"
        )
    
    # Forward the user's text message (if any)
    if message.text:
        await app.send_message(
            chat_id=ADMIN,
            text=f"**New Feedback\nUser:** {message.from_user.mention} {message.from_user.id}\n\n{message.text}"
        )

    await message.reply_text("**Your message has been sent to my admin; the admin will reply to you soon.**")


@web.route('/')
def index():
    return redirect(f"https://telegram.me/{BOT_USERNAME}")

def run():
    web.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    app.run()