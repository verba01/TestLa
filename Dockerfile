FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./

RUN pip install --no-cache-dir poetry

RUN poetry install --only main --no-root

COPY . .



EXPOSE 8000

CMD ["poetry", "run", "python", "fastapi-application/run"]