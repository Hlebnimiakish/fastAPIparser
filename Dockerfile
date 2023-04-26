FROM python:3.10.10

RUN pip install pipenv

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /fastAPIparser

COPY Pipfile Pipfile.lock /fastAPIparser/

RUN pipenv install --dev --system --deploy --ignore-pipfile

COPY app /fastAPIparser/app/

COPY kafka_starter /fastAPIparser/kafka_starter/

RUN chmod +x ./kafka_starter/kafka-entrypoint.sh
RUN chmod +x ./app/entrypoint.sh

ENV PYTHONPATH "${PYTHONPATH}:/fastAPIparser/"
