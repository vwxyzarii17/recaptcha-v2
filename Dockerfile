FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# =========================
# INSTALL PACKAGE
# =========================

RUN apt-get update && apt-get install -y \
    firefox-esr \
    tor \
    netcat-openbsd \
    wget \
    curl \
    unzip \
    xvfb \
    ffmpeg \
    gcc \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libx11-xcb1 \
    libxt6 \
    libxrender1 \
    libdbus-glib-1-2 \
    libasound2 \
    libgtk-3-0 \
    libgbm1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# =========================
# INSTALL GECKODRIVER
# =========================

RUN wget -O geckodriver.tar.gz \
    https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz && \
    tar -xvzf geckodriver.tar.gz && \
    mkdir -p /data/data/com.termux/files/usr/bin && \
    mv geckodriver /data/data/com.termux/files/usr/bin/geckodriver && \
    chmod +x /data/data/com.termux/files/usr/bin/geckodriver && \
    rm geckodriver.tar.gz

# =========================
# TOR CONFIG
# =========================

RUN mkdir -p /etc/tor

RUN echo "ControlPort 9051" >> /etc/tor/torrc && \
    echo "CookieAuthentication 0" >> /etc/tor/torrc && \
    echo "HashedControlPassword" >> /etc/tor/torrc && \
    echo "MaxCircuitDirtiness 10" >> /etc/tor/torrc && \
    echo "NewCircuitPeriod 5" >> /etc/tor/torrc

# =========================
# WORKDIR
# =========================

WORKDIR /app

# =========================
# COPY
# =========================

COPY . /app

# =========================
# INSTALL PYTHON PACKAGE
# =========================

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# =========================
# DISPLAY
# =========================

ENV DISPLAY=:1

# =========================
# PORT
# =========================

EXPOSE 7860

# =========================
# RUN
# =========================

CMD tor & \
    Xvfb :1 -screen 0 1280x720x24 & \
    while ! nc -z 127.0.0.1 9050; do sleep 1; done && \
    python app.py
