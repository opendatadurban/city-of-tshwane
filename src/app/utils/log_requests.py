from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
import logging
import traceback
import random
import time
import string
from datetime import datetime

from app.core.config import settings


filtered_routes = [
    "/api/v3/health",
    "/app/api/v2/preview",
    "/app/api/v2/ping",
    "/api/v3/thingsRegistration",
]


async def log_requests(request: Request, call_next):
    if request.url.path in filtered_routes:
        try:
            return await call_next(request)
        except Exception as e:
            tb = traceback.format_exc()

            exception_details = {
                "url": request.url,
                "path": request.path_params,
                "query_params": request.query_params,
                # "body": await request.body(),
                "error": e.args,
                "stackTrace": tb,
            }

            # For local debugging
            logging.info(f"Captured unexpected exception: {exception_details}")
            return JSONResponse(
                content={
                    "data": None,
                    "response": {"status": 500, "message": "Internal Server Error"},
                },
                status_code=500,
            )

    idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    logging.info(
        f"Start request Endpoint= {request.url.path} rid={idem} method= {request.method}"
    )
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        logging.info(f"Exception caught in Middleware {e}")
        if settings.ENVIRONMENT != "local":
            # await log_to_sentry(request, e)
            # logging.info("Logged to Sentry")
            await log_to_xray(request, e)
            logging.info("Logged to Xray")
        return JSONResponse(
            content={
                "data": None,
                "response": {"status": 500, "message": "Internal Server Error"},
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )
    else:

        process_time = (time.time() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        logging.info(
            f"{datetime.now()} Finish Endpoint= {request.url.path}  rid={idem} "
            f"completed_in={formatted_process_time}ms  method= {request.method} "
            f"status_code={response.status_code}"
        )

        return response
