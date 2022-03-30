FROM python:3.7 as base
RUN pip install pipenv


FROM base as dev

WORKDIR /app
COPY ./Pipfile* /app
RUN pipenv install

COPY . /app

CMD pipenv run uvicorn backend.main:app --host 0.0.0.0 --reload
