from pyrogram import Client, filters
from flask import Flask, redirect
from threading import Thread
import os
from motor.motor_asyncio import AsyncIOMotorClient


API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN = int(os.getenv("ADMIN"))
BOT_USERNAME = os.getenv("BOT_USERNAME")
DATABASE_URL = os.getenv("DATABASE_URL")


client = AsyncIOMotorClient(DATABASE_URL)
db = client['databas']
banned_users = db['banned_users']

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
        
        text_mssg = ' '.join(message.command[2:]) if len(message.command) > 2 else None
                
        user_id = int(message.command[1])
        user = await app.get_users(user_id)

        if not user:
            return await message.reply("Invalid user id")

        msg = message.reply_to_message

        if not msg and not text_mssg:
            return await message.reply("Please reply to a message.")
        
        if not msg and text_mssg is not None:
            await app.send_message(user_id, text=f"{text_mssg}")
        elif msg:
            media = (
                msg.photo or
                msg.video or
                msg.audio or
                msg.document or
                msg.animation
            )
            caption = msg.caption if msg.caption else None

            if msg.text and not text_mssg:
                await app.send_message(user_id, text=msg.text)
                
            if media and not text_mssg:
                await app.send_cached_media(
                    chat_id=user_id,
                    caption=caption,
                    file_id=media.file_id
                )

    except Exception as e:
        await message.reply(f"An unexpected error occurred: {str(e)}")



  
@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text(f"**Hello {message.from_user.first_name}!\nI am a support bot. Send me a message and I will forward it to my Admin.**")

@app.on_message(filters.command("ban") & filters.user(ADMIN))
async def ban_user(_, message):
    if len(message.command) < 2:
        return await message.reply("Please provide a user id.")
    
    user_id = int(message.command[1])
    await banned_users.insert_one({'_id': user_id})
    await message.reply(f"User {user_id} has been banned.")

@app.on_message(filters.command("unban") & filters.user(ADMIN))
async def unban_user(_, message):
    if len(message.command) < 2:
        return await message.reply("Please provide a user id.")
    
    user_id = int(message.command[1])
    await banned_users.delete_one({'_id': user_id})
    await message.reply(f"User {user_id} has been unbanned.")    

@app.on_message(filters.private)
async def forward(client, message):
    if message.text and message.text.startswith("/"):
        return
    
    if await banned_users.find_one({'_id': message.from_user.id}):
        return await message.reply("You are banned from using this bot.")
    
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
        replied_media = replied_msg.photo or replied_msg.video or replied_msg.audio or replied_msg.document or replied_msg.animation

        if replied_msg.text:
            await client.send_message(ADMIN, text=f"{replied_msg.text}\n\n<b>User's Reply:</b>\n{message.text}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>")

        if replied_media:
            await client.send_cached_media(
                chat_id=ADMIN,
                caption=f"{reply_caption}\n\n<b>User's Reply:</b>\n{message.text}\n\n<b>User:</b>\n{message.from_user.mention} <code>{message.from_user.id}</code>",
                file_id=replied_media.file_id
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



@web.route('/')
def index():
    return redirect(f"https://telegram.me/{BOT_USERNAME}")

def run():
    web.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    app.run()