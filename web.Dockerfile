FROM python:3.12 AS builder

WORKDIR /app
COPY . .
COPY .env .env

RUN pip install reflex>=0.4.7 \
                openai>=1.14.0 \
                reflex-chakra>=0.6.0 \
                python-dotenv \
                ragflow-sdk
RUN reflex export --no-zip --frontend-only

FROM nginx:1.21-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/.web/_static /usr/share/nginx/html
