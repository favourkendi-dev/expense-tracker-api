
FROM python:3.12-slim


WORKDIR /app


RUN pip install --no-cache-dir pipenv


COPY Pipfile Pipfile.lock ./


RUN pipenv install --system --deploy


COPY . .

EXPOSE 5555


CMD flask db upgrade && python run.py