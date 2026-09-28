FROM mwader/static-ffmpeg:7.1.1 AS ffmpeg

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /ffprobe /usr/local/bin/ffprobe

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --create-home --home-dir /app app

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY auth /app/auth
COPY hub /app/hub
COPY crud /app/crud
COPY meeting /app/meeting
COPY finance /app/finance
COPY reminder /app/reminder
COPY stats /app/stats
COPY stt /app/stt
COPY ner /app/ner
COPY nlp /app/nlp
COPY embedding /app/embedding
COPY deploy/backend/entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /app/stt/media \
    && chown -R app:app /app

USER app
EXPOSE 8080

USER root
ENTRYPOINT ["/app/entrypoint.sh"]
