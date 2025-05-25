FROM python:3.12.1-bookworm AS base

WORKDIR /app

COPY poetry.toml poetry.lock pyproject.toml /app/

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN pip install poetry

RUN poetry install

FROM base AS dev

COPY . /app

EXPOSE 80

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
