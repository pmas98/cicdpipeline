from fastapi import FastAPI
from app.routers.auth import router as auth_router
from firebase_admin import credentials
import firebase_admin

import dotenv
import os
import json

dotenv.load_dotenv()

encoded_json = os.environ.get("FIREBASE_SETTINGS")
json_data = json.loads(encoded_json)
cred = credentials.Certificate(json_data)
firebase_admin.initialize_app(cred)

app = FastAPI(
    title="Identity",
    description="Valid8 Identity Service.",
    version="1.0",
    root_path="/develop",
)

app.include_router(auth_router)
