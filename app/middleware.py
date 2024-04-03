from pyinstrument import Profiler
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse

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
