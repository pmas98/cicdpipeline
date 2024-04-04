from fastapi import FastAPI
from app.routers.auth import router as auth_router
from firebase_admin import credentials
import firebase_admin
from app.middleware import PyInstrumentMiddleWare, setup_logging
import dotenv
import os
import json
from starlette.concurrency import iterate_in_threadpool

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
async def log_request(request, call_next):

    response = await call_next(request)
    response_body = [section async for section in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(response_body))

    response_body_json = json.loads(response_body[0].decode())
    log_message = {"request": f"{request.method} {request.url}", "status_code": response.status_code}

    for key, value in response_body_json.items():
        log_message[key] = value

    if response.status_code >= 400:
        ERROR_LOGGER.error(log_message)
    else:
        LOGGER.info(log_message)
    return response

app.include_router(auth_router)

if DEBUG:
    app.add_middleware(PyInstrumentMiddleWare)
