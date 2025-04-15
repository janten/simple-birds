FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
    ffmpeg

# Set environment variables
ENV LOCALE=en
ENV LATITUDE=51
ENV LONGITUDE=7
ENV AUDIO_STREAMS=""

RUN mkdir -p /app
ADD main.py /app/main.py
ADD requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

CMD [ "python3", "/app/main.py" ]