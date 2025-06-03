import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pytz
from routers.routers import routers

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from tasks.product.update import update_product_statuses_async
from media import MEDIA_DIR

app = FastAPI()

# Монтируем директорию media на уровне приложения
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Bishkek'))

@app.on_event("startup")
async def on_startup():
    scheduler.add_job(update_product_statuses_async, IntervalTrigger(days=1))
    print("start sheduler")
    scheduler.start()


app.include_router(routers)