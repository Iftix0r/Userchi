"""
Bir marta ishlatiladi — SESSION_STRING ni olish uchun.
Bu skriptni ishga tushiring, telefon raqam va kodni kiriting,
so'ng chiqadigan SESSION_STRING ni .env fayliga nusxalang.
"""
import asyncio
from pyrogram import Client
from config import API_ID, API_HASH


async def main():
    async with Client("temp_gen", api_id=API_ID, api_hash=API_HASH) as app:
        session = await app.export_session_string()
        print("\n" + "=" * 60)
        print("SESSION_STRING (ni .env ga nusxalang):")
        print("=" * 60)
        print(session)
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())