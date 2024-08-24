import asyncio
import discord
from fastapi import FastAPI
from contextlib import asynccontextmanager

client = discord.Client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(client.start('token'))
    yield


api = FastAPI(lifespan=lifespan)


@api.get("/")
async def health_check():
    return {"status": "ok"}
