import asyncpg
import os
from fastapi import Depends

DB_URL = os.getenv("postgres://minjunsz:'ep1kh1gh@'@supa.minjunpark.com:5432/daily_paper_summary")

async def connect_db():
    return await asyncpg.connect(DB_URL)

async def get_db():
    db = await connect_db()
    try:
        yield db
    finally:
        await db.close()
