import aiosqlite
import asyncio
from typing import List
from app.services.logger import logger

DB_FILE = "chat_log.db"


async def ensure_schema():
    """Ensure the chat_logs table exists."""
    async with aiosqlite.connect(DB_FILE) as connection:
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                session_id TEXT,
                user_query TEXT,
                gpt_response TEXT
            )
        ''')
        await connection.commit()
        logger.info("Database schema ensured.")


async def add_conversation_async(session_id: str, user_query: str, gpt_response: str):
    """Add a conversation entry to the database."""
    try:
        await ensure_schema()
        async with aiosqlite.connect(DB_FILE) as connection:
            await connection.execute(
                "INSERT INTO chat_logs (session_id, user_query, gpt_response) VALUES (?, ?, ?)",
                (session_id, user_query, gpt_response)
            )
            await connection.commit()
            logger.info(f"Conversation added for session {session_id}")
    except Exception as e:
        logger.exception(f"Error occurred while adding conversation: {str(e)}")
        raise


async def get_past_conversation_async(session_id: str) -> List[dict]:
    """Retrieve all past conversations for a given session_id."""
    start_time = asyncio.get_event_loop().time()
    messages = []

    try:
        await ensure_schema()
        async with aiosqlite.connect(DB_FILE) as connection:
            async with connection.execute(
                "SELECT user_query, gpt_response FROM chat_logs WHERE session_id=?",
                (session_id,)
            ) as cursor:
                async for row in cursor:
                    messages.append({"role": "user", "content": row[0]})
                    messages.append({"role": "assistant", "content": row[1]})

        elapsed_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"History fetched for session {session_id} in {elapsed_time:.2f}s: {messages}")
        return messages
    except Exception as e:
        logger.exception(f"Error retrieving conversation: {str(e)}")
        raise
