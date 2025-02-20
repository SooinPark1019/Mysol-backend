import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from mysol.api import api_router
from mysol.database.middleware import DefaultSessionMiddleware

SECRET_KEY = os.urandom(32).hex()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(DefaultSessionMiddleware)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}