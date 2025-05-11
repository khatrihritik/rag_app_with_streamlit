# main.py (or keep as api.py if you prefer)
from fastapi import FastAPI
from app.routes.chat_routes import router as chat_router
import nest_asyncio
import asyncio
import aiomonitor
import uvicorn
from dotenv import load_dotenv


load_dotenv()  # This loads variables from .env into environment


nest_asyncio.apply()

app = FastAPI()
app.include_router(chat_router)

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    with aiomonitor.start_monitor(loop=asyncio.get_event_loop()):
        uvicorn.run(app, host="0.0.0.0", port=8000)
