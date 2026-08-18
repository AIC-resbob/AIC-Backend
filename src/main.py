from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os 
import uvicorn
from scalar_fastapi import get_scalar_api_reference
from middleware import setup_middleware, limiter
from database import engine, Base
import db_models

load_dotenv()
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 3000))

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print(f"Server is listening on {PORT}")
    yield

app = FastAPI(
    title="AIC Backend API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
    )
setup_middleware(app)

@app.get("/docs", include_in_schema=False)
async def scalar_docs(request: Request):
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title
    )

@app.get('/')
async def root(request: Request):
    return {f"Server is listening on port {PORT}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)