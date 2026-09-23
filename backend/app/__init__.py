from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.init_db import initialize_database
from app.main import app as app_instance


app = app_instance

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()
