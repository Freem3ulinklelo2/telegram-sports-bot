import asyncio
from telegram import Bot
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROUP_ID = int(os.environ.get('GROUP_ID'))

async def test():
    bot = Bot(BOT_TOKEN)
    await bot.send_message(GROUP_ID, "🎉 Test message from GitHub Actions!")
    print(f"✅ Message sent to {GROUP_ID}")

asyncio.run(test())
