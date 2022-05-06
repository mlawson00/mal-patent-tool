from fastapi import FastAPI
from official.nlp import bert
import official.nlp.bert.tokenization
import tensorflow_text
import requests
import json
from pydantic import BaseModel
import google.auth.transport.requests
import google.oauth2.id_token
import numpy as np
from fastapi import FastAPI, HTTPException

from fastapi.encoders import jsonable_encoder
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
    InternalUser, postgresInternalUser
)
from backend.models.auth_models import (
    ExternalAuthToken,
    ExternalUser,
    postgresExternalUser,
    InternalAccessTokenData,
)

from backend.models.base import (
    engine, Session, Base
)

import uvicorn
from fastapi import FastAPI

import logging as log


class custom_bert_encoder:
    def __init__(self, vocab_file, max_len=128):
        self.bert = bert.tokenization.FullTokenizer(vocab_file)
        self.max_len = max_len

    def bert_encode(self, text):
        text = self.bert.tokenize(text)
        text = text[: self.max_len - 2]
        input_sequence = ["[CLS]"] + text + ["[SEP]"]
        pad_len = self.max_len - len(input_sequence)
        tokens = self.bert.convert_tokens_to_ids(input_sequence) + [0] * pad_len
        pad_masks = [1] * len(input_sequence) + [0] * pad_len
        segment_ids = [0] * self.max_len
        return {"text": text, "input_mask": [pad_masks], "input_type_ids": [segment_ids], "input_word_ids": [tokens]}


b = custom_bert_encoder('backend/vocab.txt')


class AbstractDraft(BaseModel):
    abstract: str


class BERT_input(BaseModel):
    input_mask: list
    input_type_ids: list
    input_word_ids: list

logger = log.getLogger(__name__)

log.info('Setting up sql')
Base.metadata.create_all(engine)
log.info('Setting up session')
session = Session()
log.info('Setting up app')

import backend.inference_model

app = FastAPI()
global mc


mc = backend.inference_model.bqPatentPredictor(max_distance=1,
                                               bq_table=f"mal-l7.mal_l7_us.c064bcccce114c9a8cfa67e36d0580cf",
                                               est_file_path = 'gs://mal-l7-mlflow/mlflow-artifacts/0/671fc6ef094d4ee3b52fc476a768ccac/artifacts/embedding_normalisiation.csv')

origins = [
    config.FRONTEND_URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

csrf_token_redirect_cookie_scheme = auth_schemes.CSRFTokenRedirectCookieBearer()
auth_token_scheme = auth_schemes.AuthTokenBearer()
access_token_cookie_scheme = auth_schemes.AccessTokenCookieBearer()


# TURN OFF SOMETIMES
@app.on_event("startup")
async def startup_event():
    """ Startup functionality """
    log.info('startup up app yo ho')


@app.on_event("shutdown")
async def shutdown_event():
    """ Shutdown functionality """
    log.info('SHUTTING up app')
    # async with exception_handling():
    # 	await db_client.end_session()
    # 	await db_client.close_connection()


@app.middleware("http")
async def setup_request(request: Request, call_next) -> JSONResponse:
    """ A middleware for setting up a request. It creates a new request_id
        and adds some basic metrics.

        Args:
            request: The incoming request
            call_next (obj): The wrapper as per FastAPI docs

        Returns:
            response: The JSON response
    """
    response = await call_next(request)

    return response


@app.get("/api/login-redirect")
async def login_redirect(auth_provider: str):
    log.info('startup up app yo ho')
    log.info(f'The redirect URL is meant to be {config.GOOGLE_REDIRECT_URL}')
    """ Redirects the user to the external authentication pop-up

        Args:
            auth_provider: The authentication provider (i.e google-iodc)

        Returns:
            Redirect response to the external provider's auth endpoint
    """
    log.info('login-redirect')
    async with exception_handling():

        # think this is an instance of class of GoogleAuthProvider
        provider = await auth_providers.get_auth_provider(auth_provider)
        try:
            log.info(f'the provider is {provider}')
        except:
            log.info(f'cant log and awaited paremeter')
        request_uri, state_csrf_token = await provider.get_request_uri()
        log.info(f'the request_uri {request_uri}')

        response = RedirectResponse(url=request_uri)

        # Make this a secure cookie for production use
        response.set_cookie(key="state", value=f"Bearer {state_csrf_token}", httponly=True)
        log.info(f'you\'re on the response point now {response}')
        return response


@app.get("/api/google-login-callback/")
async def google_login_callback(
        request: Request,
        _=Depends(csrf_token_redirect_cookie_scheme)
):
    """ Callback triggered when the user logs in to Google's pop-up.

        Receives an authentication_token from Google which then
        exchanges for an access_token. The latter is used to
        gain user information from Google's userinfo_endpoint.



        Args:
            request: The incoming request as redirected by Google
    """
    log.info('google callback')
    async with exception_handling():
        code = request.query_params.get("code")

        if not code:
            raise AuthorizationException("Missing external authentication token")

        provider = await auth_providers.get_auth_provider(config.GOOGLE)

        # Authenticate token and get user's info from external provider
        external_user = await provider.get_user(
            auth_token=ExternalAuthToken(code=code)
        )

        # Get or create the internal user
        internal_user = await db_client.get_user_by_external_sub_id(external_user)

        if internal_user is None:
            internal_user = await db_client.create_internal_user(external_user)

        internal_auth_token = await auth_util.create_internal_auth_token(internal_user)

        # Redirect the user to the home page
        redirect_url = f"{config.FRONTEND_URL}?authToken={internal_auth_token}"
        log.info(f'the redirect url is supposed to be {redirect_url}')
        response = RedirectResponse(url=redirect_url)

        # Delete state cookie. No longer required
        response.delete_cookie(key="state")

        return response


@app.get("/api/azure-login-callback/")
async def azure_login_callback():
    print('yo')
    pass


#

@app.get("/api/login/")
async def login(
        response: JSONResponse,
        internal_user: str = Depends(auth_token_scheme)
) -> JSONResponse:
    """ Login endpoint for authenticating a user after he has received
        an authentication token. If the token is valid it generates
        an access token and inserts it in a HTTPOnly cookie.

        Args:
            internal_auth_token: Internal authentication token

        Returns:
            response: A JSON response with the status of the user's session
    """
    async with exception_handling():
        print('making an access token')
        access_token = await auth_util.create_internal_access_token(
            InternalAccessTokenData(
                sub=internal_user.internal_sub_id,
            )
        )

        response = JSONResponse(
            content=jsonable_encoder({
                "userLoggedIn": True,
                "userName": internal_user.username,
            }),
        )

        # Make this a secure cookie for production use
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)

        return response


#
@app.get("/api/logout/")
async def logout(
        response: JSONResponse,
        internal_user: str = Depends(access_token_cookie_scheme)
) -> JSONResponse:
    """ Logout endpoint for deleting the HTTPOnly cookie on the user's browser.

        Args:
            internal_auth_token: Internal authentication token

        Returns:
            response: A JSON response with the status of the user's session
    """
    async with exception_handling():
        response = JSONResponse(
            content=jsonable_encoder({
                "userLoggedIn": False,
            }),
        )

        response.delete_cookie(key="access_token")

        return response


@app.get("/api/user-session-status/")
async def user_session_status(
        internal_user: InternalUser = Depends(access_token_cookie_scheme)
) -> JSONResponse:
    """ User status endpoint for checking whether the user currently holds
        an HTTPOnly cookie with a valid access token.

        Args:
            internal_user: A user object that has meaning in this application

        Returns:
            response: A JSON response with the status of the user's session
    """
    async with exception_handling():
        logged_id = True if internal_user else False

        response = JSONResponse(
            content=jsonable_encoder({
                "userLoggedIn": logged_id,
                "userName": internal_user.username,
            }),
        )

        return response


class probabilityInput(BaseModel):
    probs: list

class customEmbeddingOutput(BaseModel):
    cpc_prob: list
    raw_emb: list

class PredictorInput(BaseModel):
    embedding: list
    k: int
    query:dict


import pandas as pd
labels_frame = pd.read_csv('backend/labels_group_id.tsv', sep='\t')
threshold=0.2

def query_generator(raw_query: dict):
    country_list = '", "'.join(
        [country for country in raw_query['countries'].keys() if raw_query['countries'][country]['selected']])
    country_query = f'country_code IN ("{country_list}")'
    start_date_query = f'filing_date >= "{raw_query["start_year"]}-01-01"'
    end_date_query = f'filing_date <= "{raw_query["end_year"]}-01-01"'
    cleaned_query = " AND ".join([start_date_query,end_date_query,country_query])
    return cleaned_query


@app.post("/api/give_similar_patents")
async def give_similar_patents(input_args: PredictorInput) -> PredictorInput:


    id_token = google.oauth2.id_token.fetch_id_token(auth_req, 'https://test-image-6wcv5jbs7a-nw.a.run.app/predict')
    print(id_token)
    Headers = {"Authorization": f"Bearer {id_token}"}

    out = requests.post('https://test-image-6wcv5jbs7a-nw.a.run.app/predict', headers=Headers,
    json = {"embedding": input_args.embedding,
            'k': input_args.k,
            'use_custom_embeddings': input_args.use_custom_embeddings,
            'n': input_args.n,
            'query': input_args.query})
    return(out.text)

@app.post("/api/give_similar_patents_bq")
async def give_similar_patents_bq(input_args: PredictorInput) -> PredictorInput:


    cleaned_query = query_generator(input_args.query)
    print(cleaned_query)
    mc.where_statements = cleaned_query

    try:
        df, cost = mc.bq_get_nearest_patents(np.array(input_args.embedding))
        print(f'that cost {cost}p, ouch')
        print(df)

        return({'predictions':df.to_json(orient='records'), 'cost':np.round(cost,2)})

    except:
        raise HTTPException(status_code=404, detail=f"Items not found, expected query costs {mc.costs*500/(1024**4)}p")


@app.post("/api/give_likely_classes")
async def give_likely_classes(probs: probabilityInput) -> probabilityInput:
    raw_data = jsonable_encoder(probs.probs)[0]
    probs_array = np.array(raw_data)
    return_ob = labels_frame.loc[probs_array >= threshold]
    return_ob.loc[:, 'probability'] = np.round(probs_array[probs_array >= threshold] * 100, 2)
    return_ob = return_ob.sort_values('probability', ascending=False)
    print(return_ob)
    return {return_ob.to_json(orient='records')}

@app.post("/api/give_custom_embedding")
async def give_custom_embedding(probs: probabilityInput) -> probabilityInput:
    raw_data = jsonable_encoder(probs.probs)

    id_token = google.oauth2.id_token.fetch_id_token(auth_req, 'https://mlflow-ae-prototype-6wcv5jbs7a-nw.a.run.app')
    Headers = {"Authorization": f"Bearer {id_token}"}
    custom_embeddings = requests.post('https://mlflow-ae-prototype-6wcv5jbs7a-nw.a.run.app/invocations',
                          headers=Headers, json={"inputs":raw_data})
    # print(custom_embeddings.text)

    return custom_embeddings.text


@app.post("/api/abstract_search")
async def abstract_search(abstract_draft: AbstractDraft) -> AbstractDraft:
    raw_data = jsonable_encoder(abstract_draft.abstract)

    data = b.bert_encode(raw_data)
    # output = requests.post('http://localhost:8080/invocations', json={"inputs": data})
    return {"inputs": data}


@app.post("/api/get_BERT_probs")
async def make_cpc_pred(bert_input: BERT_input) -> BERT_input:
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, 'https://mlflow-patentbert-6wcv5jbs7a-nw.a.run.app')
    print('id_token_is', id_token)
    Headers = {"Authorization": f"Bearer {id_token}"}

    probs = requests.post('https://mlflow-patentbert-6wcv5jbs7a-nw.a.run.app/invocations',
                          headers=Headers, json={"inputs": bert_input.dict()})

    print(probs.text)
    return {'probs': json.loads(probs.text)}


if __name__ == "__main__":
    log.info('startup up app')
    uvicorn.run(app, host="0.0.0.0", port=8000)
    log.info('app should be running again')
