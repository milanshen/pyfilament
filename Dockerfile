FROM ubuntu:noble AS ubuntu-base
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update

RUN apt-get install -y software-properties-common

FROM ubuntu-base AS ubuntu-python-base
# https://github.com/pyenv/pyenv/wiki#suggested-build-environment
RUN apt-get install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl git \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

COPY .python-version ./
RUN curl -fsSL https://pyenv.run | bash
ENV PYENV_ROOT=/root/.pyenv
ENV PATH=$PYENV_ROOT/bin:$PATH
RUN pyenv install
RUN pyenv global $(cat .python-version)
RUN pyenv exec pip install poetry

FROM ubuntu-python-base AS filament
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pyenv exec poetry config virtualenvs.in-project true
RUN pyenv exec poetry install --no-root --only main

COPY . .

RUN pyenv exec poetry run python -m compileall -q -j 0 .
