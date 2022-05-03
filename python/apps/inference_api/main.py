import logging
import time
from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    Request,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import (
    JSONResponse,
    RedirectResponse,
)
import os
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'config'
#os.environ['GOOGLE_CLOUD_PROJECT'] = 'mal-l7'

import uvicorn
from fastapi import FastAPI

import logging as log
import inference_model

logger = log.getLogger(__name__)
log.info('Setting up app')
app = FastAPI()
#app.fitted = False
# Allow CORS. DON'T do that on production!

if "INSTANCE_CONNECTION_NAME" in os.environ:
    FRONTEND_URL = "https://mal-6wcv5jbs7a-nw.a.run.app"
else:
    FRONTEND_URL = "http://localhost:8080"


origins = [
    'locahost' #set this up
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel

class PredictorInput(BaseModel):
    embedding: list
    k: int
    use_custom_embeddings: bool
    n: int
    query:str
    with_v1:bool

#TURN OFF SOMETIMES
@app.on_event("startup")
async def startup_event():
    """ Startup functionality """
    log.info('startup up app yo ho')
    app.mc = inference_model.PatentClassifier()
    #metadata_frame_path = "gs://mal-l7-mlflow/mlflow-artifacts/0/3dbc8c6efc7240ec8c8bcdf095274257/artifacts/pandas_0.parquet"
    #custom_embedding_frame_path = "gs://mal-l7-mlflow/mlflow-artifacts/0/3dbc8c6efc7240ec8c8bcdf095274257/artifacts/custom_embedding_array_0.parquet"
    #v1_frame_path = "gs://mal-l7-mlflow/mlflow-artifacts/0/3dbc8c6efc7240ec8c8bcdf095274257/artifacts/v1_0.parquet"
    app.mc.fit(os.environ['v1_frame_path'], os.environ['metadata_frame_path'] , os.environ['custom_embedding_frame_path'])
    #app.mc.fit(v1_frame_path, metadata_frame_path, custom_embedding_frame_path)

    log.info('Loaded the stuff')
    #app.fitted = True

@app.post("/predict")
async def give_predictions(piv: PredictorInput) -> PredictorInput:
    output = app.mc.predict(piv.embedding, piv.k, piv.use_custom_embeddings, piv.n, piv.query, piv.with_v1)
    return {"predictions": output.to_json(orient='records')}


@app.on_event("shutdown")
async def shutdown_event():
    """ Shutdown functionality """
    log.info('SHUTTING up app')
    # async with exception_handling():
    # 	await db_client.end_session()
    # 	await db_client.close_connection()

@app.get("/")
async def base():
    print('in business')

if __name__ == "__main__":
    log.info('startup up app')
    uvicorn.run(app, host="0.0.0.0", port=8000)
    log.info('app should be running again')