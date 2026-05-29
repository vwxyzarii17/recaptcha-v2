FROM python:3.11-slim

# =========================
# INSTALL SYSTEM PACKAGE
# =========================

RUN apt-get update && apt-get install -y \
    firefox-esr \
    tor \
    ffmpeg \
    wget \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# =========================
# INSTALL GECKODRIVER
# =========================

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz && \
    tar -xvzf geckodriver-v0.34.0-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-v0.34.0-linux64.tar.gz

# =========================
# WORKDIR
# =========================

WORKDIR /app

# =========================
# COPY FILE
# =========================

COPY . /app

# =========================
# INSTALL PYTHON PACKAGE
# =========================

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# =========================
# TOR CONFIG
# =========================

RUN echo "ControlPort 9051" >> /etc/tor/torrc

RUN echo 'CookieAuthentication 0' >> /etc/tor/torrc

RUN echo 'HashedControlPassword ""' >> /etc/tor/torrc

# =========================
# PORT
# =========================

EXPOSE 8080

# =========================
# RUN
# =========================

CMD tor & \
    sleep 10 && \
    python app.py
