FROM python:3.12-slim


RUN adduser --disabled-password --gecos '' tsar && \
    mkdir -p /app && \
    chown -R tsar:tsar /app


USER tsar

WORKDIR /app

LABEL version="1.0" \
      description="Царский питон - изолированная среда выполнения" \
      maintainer="Tsar Python"

CMD ["python", "--version"]