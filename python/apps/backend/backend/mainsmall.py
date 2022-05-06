from fastapi import FastAPI
import json

import google.auth.transport.requests
import google.oauth2.id_token
import numpy as np
import official.nlp.bert.tokenization
import requests
from fastapi import (
    Depends,
    Request,
)
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from official.nlp import bert
from pydantic import BaseModel
from starlette.responses import (
    JSONResponse,
    RedirectResponse,
)

auth_req = google.auth.transport.requests.Request()
from backend.auth import (
    providers as auth_providers,
    schemes as auth_schemes,
    util as auth_util,
)
from backend import config
from backend import db_client
from backend.exceptions import (
    AuthorizationException,
    exception_handling,
)
from backend.models.db_models import (
    InternalUser
)
from backend.models.auth_models import (
    ExternalAuthToken,
    InternalAccessTokenData,
)

from backend.models.base import (
    engine, Session, Base
)

import uvicorn
from fastapi import FastAPI

import logging as log
import pandas as pd


# import backend.inference_model

app = FastAPI()


@app.get("/api/alive")
async def root():
    return {"message": "Hello World"}