from fastapi import FastAPI
from app.routers.auth import router as auth_router
from firebase_admin import credentials
import firebase_admin
from app.middleware import PyInstrumentMiddleWare, setup_logging, log_request
import dotenv
import os
import json

dotenv.load_dotenv()
DEBUG = True

LOGGER, ERROR_LOGGER = setup_logging()

encoded_json = os.environ.get("FIREBASE_SETTINGS")
json_data = json.loads(encoded_json)
cred = credentials.Certificate(json_data)
firebase_admin.initialize_app(cred)
app = FastAPI(
    title="CICD Pipeline",
    description="Service for an app.",
    version="1.0",
    root_path="/develop",
)

@app.middleware("http")
async def logger(request, call_next):
    return await log_request(request, call_next)
app.include_router(auth_router)

if DEBUG:
    app.add_middleware(PyInstrumentMiddleWare)
