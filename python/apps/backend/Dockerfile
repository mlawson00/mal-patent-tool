FROM python:3.7 as base
RUN pip install pipenv
#RUN pip install psycopg2
#RUN pip install fastapi
#RUN pip install uvicorn
#RUN pip install motor
#RUN pip install requests
#RUN pip install oauthlib
#
#RUN pip install passlib[bcrypt]
#RUN pip install aiocache
#RUN pip install msal
#RUN pip install pyjwt
#sqlalchemy = "*"
#psycopg2-binary = "*"

FROM base as dev

WORKDIR /app
COPY ./Pipfile* /app
RUN pipenv install
#RUN  pipenv run pip install psycopg2

COPY . /app

CMD pipenv run uvicorn backend.main:app --host 0.0.0.0 --reload
