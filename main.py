import string
from fastapi import FastAPI, HTTPException
from app.routers.auth import router as auth_router
from firebase_admin import credentials
import firebase_admin
from app.middleware import PyInstrumentMiddleWare, setup_logging
import dotenv
import os
import json
from starlette.concurrency import iterate_in_threadpool

dotenv.load_dotenv()

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
async def log_request(request, call_next):

    LOGGER.info(f"Request received: {request.method} {request.url}")

    response = await call_next(request)
    response_body = [section async for section in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(response_body))
    LOGGER.info(f"Request received: {request.method} {request.url} , response_body={response_body[0].decode()}")
    if response.status_code >= 400:
        ERROR_LOGGER.error(f"Error: {response.status_code}, response_body={response_body[0].decode()}")

    return response

app.include_router(auth_router)

app.add_middleware(PyInstrumentMiddleWare)
