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
                
        user_id = int(message.command[1])
        user = await app.get_users(user_id)

        if not user:
            return await message.reply("Invalid user id")

        msg = message.reply_to_message

        if not msg:
            return await message.reply("Please reply to a message.")
        
        media = (
            msg.photo or
            msg.video or
            msg.audio or
            msg.document or
            msg.animation
        )
        caption = msg.caption if msg.caption else None

        if msg.text:
            await app.send_message(user_id, text=msg.text)
            
        if media :
            await app.send_cached_media(
                chat_id=user_id,
                caption=caption,
                file_id=media.file_id
            )

        await message.reply(f"**Message sent to {user.first_name} successfully.**")

    except Exception as e:
        await message.reply(f"An unexpected error occurred: {str(e)}")

@app.on_message(filters.private)
async def forward(client, message):
    if message.text and message.text.startswith("/"):
        return
    
    if message.from_user.id == ADMIN:
        return
    
    caption = message.caption if message.caption else None

    media = (
        message.photo or
        message.video or
        message.audio or
        message.document or
        message.animation
    )

    if message.reply_to_message:
        replied_msg = message.reply_to_message
        reply_caption = replied_msg.caption if replied_msg.caption else None

        # Forward the replied message along with the user's reply
        if replied_msg.text:
            await client.send_message(ADMIN, text=f"{replied_msg.text}\nn\n<b>User's Reply:</b>\n{message.text}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>")
        else:
            await replied_msg.copy(
                chat_id=ADMIN,
                caption=f"{reply_caption}n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>\n\n<b>User's Reply:</b>\n{message.text}",
            )
    else:
        if message.text:
            await app.send_message(ADMIN, text=f"{message.text}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>")

        if media:
            await app.send_cached_media(
                chat_id=ADMIN,
                caption=f"{caption}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>",
                file_id=media.file_id
            )

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(f"**Hello {message.from_user.first_name}!\nI am a support bot. Send me a message and I will forward it to my Admin.**")


@web.route('/')
def index():
    return redirect(f"https://telegram.me/{BOT_USERNAME}")

def run():
    web.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    app.run()