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

        if msg.text:
            await app.send_message(user_id, text=msg.text)

        media = (
            msg.photo or
            msg.video or
            msg.audio or
            msg.document or
            msg.animation
        )

        if media:
            await app.send_media(
                chat_id=user_id,
                media=media.file_id,
                caption=msg.caption
            )

        await message.reply(f"**Message sent to {user.first_name} successfully.**")

    except Exception as e:
        await message.reply(f"An unexpected error occurred: {str(e)}")


@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(f"**Hello {message.from_user.first_name}!\nI am a feedback bot. Send me a message and I will forward it to my Admin.**")


@app.on_message(filters.private & filters.text)
async def forward(client, message):

    if message.text.startswith("/"):
        return
    
    if message.from_user.id == ADMIN:
        return

    success = await app.send_message(
            chat_id=ADMIN,
            text=f"**New Feedback\nUser:** {message.from_user.mention} {message.from_user.id}\n\n{message.text}"
        )
    if success:
        await message.reply_text("**Your message has been sent to my master, please wait for reply**")
    else:
        await message.reply_text("**Something went wrong, please try again later.**")

@app.on_message(filters.private & filters.media)
async def send_media(client, message):
        
        if message.from_user.id == ADMIN:
            return
    
        success = await message.copy(
             chat_id=ADMIN,
             caption=f"<b>Message:</b>{message.caption}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>"
        )
        if success:
            await message.reply_text("**Your message has been sent to my master, please wait for reply.**")
        else:
            await message.reply_text("**Something went wrong, please try again later.**")


@web.route('/')
def index():
    return redirect(f"https://telegram.me/{BOT_USERNAME}")

def run():
    web.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    app.run()