from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os 
import uvicorn

load_dotenv()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 3000))
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Server is listening on {PORT}")
    yield
app = FastAPI(lifespan=lifespan)
@app.get('/')
async def read_root():
    return{"status": "online", "port" : PORT}

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)