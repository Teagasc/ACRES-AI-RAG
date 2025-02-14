FROM python:3.12

ENV REDIS_URL=redis://redis
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

RUN pip install reflex>=0.4.7 \
                openai>=1.14.0 \
                reflex-chakra>=0.6.0 \
                python-dotenv \
                ragflow-sdk

ENTRYPOINT ["reflex", "run", "--env", "prod", "--backend-only", "--loglevel", "debug"]
