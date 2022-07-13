FROM python:3.7.13-alpine3.15 as build

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.poetry/bin:${PATH}"

RUN apk add \
    curl \
    g++ \
    gcc \
    linux-headers \
    make \
    musl-dev \
    sqlite \
    python3-dev \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python \
    && poetry config virtualenvs.in-project false \
    && poetry config virtualenvs.path /.venv


WORKDIR /src
ADD poetry.lock pyproject.toml ./
RUN sed -i 's/^packages =.*$//g' /src/pyproject.toml && poetry install --no-dev

FROM python:3.7.13-alpine3.15 as runtime

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.poetry/bin:${PATH}"

COPY --from=build /root/.poetry /root/.poetry/
COPY --from=build /.venv /.venv

WORKDIR /src
ADD . ./
RUN apk add --no-cache libpq \
    && poetry config virtualenvs.in-project false \
    && poetry config virtualenvs.path /.venv \
    && poetry install --no-dev
