from pyinstrument import Profiler
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse
import dotenv
import os
import watchtower
import logging
from time import strftime
import boto3
from starlette.concurrency import iterate_in_threadpool
import json

dotenv.load_dotenv()
cloudwatch = boto3.client('cloudwatch')

boto3.Session(
    region_name=os.environ.get("AWS_DEFAULT_REGION"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

def setup_logging():
    LOGGER = logging.getLogger(__name__)
    LOGGER.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    cw_handler = watchtower.CloudWatchLogHandler(
        log_group="auth",
        stream_name=strftime("%Y-%m-%d") + "-auth"
    )
    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(cw_handler)

    ERROR_LOGGER = logging.getLogger('error_logger')
    ERROR_LOGGER.setLevel(logging.ERROR)

    error_console_handler = logging.StreamHandler()
    ERROR_LOGGER.addHandler(error_console_handler)

    error_cw_handler = watchtower.CloudWatchLogHandler(
        log_group="auth-errors",
        stream_name=strftime("%Y-%m-%d") + "-auth"
    )
    ERROR_LOGGER.addHandler(error_cw_handler)

    return LOGGER, ERROR_LOGGER

def track_error_to_cloudwatch(error_message, ERROR_LOGGER):
    try:
        cloudwatch.put_metric_data(
            Namespace='Custom/Errors',
            MetricData=[
                {
                    'MetricName': 'ErrorEvent',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'AuthErrorType',
                            'Value': str(error_message)
                        }
                    ]
                }
            ]
        )
    except Exception as e:
        ERROR_LOGGER.exception("Error while tracking error event: %s", e)


class PyInstrumentMiddleWare(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> HTMLResponse:
        if "prof" in request.query_params:
            profiler = Profiler(interval=0.001, async_mode="enabled")
            profiler.start()
            response = await call_next(request)
            profiler.stop()

            profiler.write_html("profile.html")

            with open("profile.html", "r") as f:
                profile_content = f.read()

            return HTMLResponse(content=profile_content, status_code=response.status_code)
        else:
            return await call_next(request)

async def log_request(request, call_next):

    LOGGER, ERROR_LOGGER = setup_logging()
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
