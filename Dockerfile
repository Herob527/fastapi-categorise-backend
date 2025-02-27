FROM python:3.12.1-bookworm

WORKDIR /app

COPY . /app

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN pip install poetry

COPY . /app

RUN poetry install

EXPOSE 80

CMD ["poetry", "run", "uvicorn", "main:app"]
