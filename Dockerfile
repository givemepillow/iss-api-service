FROM python:3.11-bullseye as poetry
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /project
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.in-project true
COPY . .
RUN poetry install --no-interaction --no-ansi

FROM python:3.11-slim-bullseye as runtime
COPY --from=poetry /project /project
ENV PATH="/project/.venv/bin:$PATH"
WORKDIR /project

