from fastapi import FastAPI
from app.routers.auth import router as auth_router
from firebase_admin import credentials
import firebase_admin
from app.middleware import PyInstrumentMiddleWare
import dotenv
import os
import json
import watchtower
import logging
from time import strftime
import boto3

dotenv.load_dotenv()

boto3.Session(
    region_name=os.environ.get("AWS_DEFAULT_REGION"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
cw_handler = watchtower.CloudWatchLogHandler(
    log_group="identity",
    stream_name=strftime("%Y-%m-%d-%H-%M-%S")
)
LOGGER.addHandler(console_handler)
LOGGER.addHandler(cw_handler)

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

@app.middleware("http")
async def log_request(request, call_next):
    LOGGER.info(f"Request received: {request.method} {request.url}")
    response = await call_next(request)
    return response

app.include_router(auth_router)
app.add_middleware(PyInstrumentMiddleWare)
