"""Fast API app and handler"""
import argparse
import json
import pathlib
from decimal import Decimal
import uvicorn
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader, APIKeyQuery
from mangum import Mangum
from pydantic import BaseSettings

import sygno_api
import sygno_api.api
from sygno_api.api.schema import (
    WriteResponse,
    ExposeResponse,
    ExposeRequest,
    WriteRequest,
)
from sygno_api.events import event_logger


class Settings(BaseSettings):
    """Settings will set default values if these are not found in environment variables"""

    application: str = "api-solution"
    deploy_env: str = "dev"
    component: str = "fastapi"
    app_version: str = "R0.1"
    api_table_name: str = (
        "cdk-solution-ApiDBApiTable9B6DE511-4CSR3FGGI5VI"
    )

    events_table_name: str = (
        "cdk-solution-ApiDBApiTable9B6DE511-4CSR3FGGI5VI"
    )


settings = Settings()

logger.info(f" Initial API Service settings: {settings}")

sygno_api = sygno_api.api.sygnoAPI(settings)
event_log = event_logger.EventLogger(settings)

# Define a list of valid API keys
READ_KEYS = [
    "A39658387A1C13B94E78A7F37BDCB",
    "513792269572187F57A1FFBC8DC3D",
    "ceasar"
]

WRITE_KEYS = [
    "CC519BF33D11DBFB46B8787BECF96",
    "584F6E17FADB24258E75EF645EAA1",
    "ceasar"
]

# Define the name of HTTP header to retrieve an API key from
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_read_api_key(
    api_key_header: str = Security(api_key_header),
):
    """Retrieve & validate an API key from the query parameters or HTTP header"""

    # If the API Key is present in the header of the request & is valid, return it
    if api_key_header in READ_KEYS:
        return api_key_header

    # Otherwise, we can raise a 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


def get_write_api_key(
    api_key_header: str = Security(api_key_header),
):
    """Retrieve & validate an API key from the query parameters or HTTP header"""

    # If the API Key is present in the header of the request & is valid, return it
    if api_key_header in WRITE_KEYS:
        return api_key_header

    # Otherwise, we can raise a 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


app = FastAPI(
    title="sygno API",
    description="Service to stand up sygno assignment API",
)


# Setup headers for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
    allow_headers=[
        "Content-Type",
        "X-Amz-Date",
        "X-Amz-Security-Token",
        "Authorization",
        "X-Api-Key",
        "X-Requested-With",
        "Accept",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
    ],
)


@app.post(
    "/sygno/write_raw",
    response_model=WriteResponse,
    response_model_exclude_none=True,
)
async def save_raw_data(
    item: WriteRequest,
    api_key: str = Security(get_write_api_key),
):
    """write raw climate data"""

    logger.info(f"writing climate item:{item}")
    # log request event
    request_data = json.loads(json.dumps(item.dict()), parse_float=Decimal)
    event_log.log(
        api_key, "write_request", request_data
    )

    res = sygno_api.save_raw_data(item, api_key)
    if not res:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write {item} to database",
        )

    # log response event
    response_data = {"response": res}
    event_log.log(
        api_key, "write_response", response_data
    )

    return res


@app.post(
    "/sygno/expose",
    response_model=ExposeResponse,
    response_model_exclude_none=True,
)
async def get_data(
    item: ExposeRequest,
    api_key: str = Security(get_read_api_key),
):
    """read climate data"""

    logger.info(f"reading climate item:{item}")
    # log request event
    request_data = json.loads(json.dumps(item.dict()), parse_float=Decimal)
    event_log.log(
        api_key, "read_request", request_data
    )

    res = sygno_api.get_data(item)
    if not res:
        raise HTTPException(
            status_code=404,
            detail=f"Data for request {item} not found",
        )

    # log response event
    response_data = {"response": res}
    event_log.log(
        api_key, "read_response", response_data
    )

    return res


handler = Mangum(app)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launches FastAPI service app")
    parser.add_argument("--openapi_fileout", type=pathlib.Path, default=None)

    args = parser.parse_args()

    if args.openapi_fileout:
        # Dump Open API file
        with args.openapi_fileout.open("w") as fout:
            json.dump(
                get_openapi(
                    title=app.title,
                    version=app.version,
                    openapi_version=app.openapi_version,
                    description=app.description,
                    routes=app.routes,
                ),
                fout,
            )
    else:
        # launch service
        uvicorn.run(app, host="0.0.0.0", port=5005)
