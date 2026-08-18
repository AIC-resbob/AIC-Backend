from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
def setup_middleware(app:FastAPI)->None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    origins = [
        "http://localhost:5173"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins =origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )