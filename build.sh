#!/bin/bash
apt-get update && apt-get install -y \
    libjpeg-turbo8-dev \
    libfreetype6-dev \
    libpng-dev \
    gcc \
    python3-dev

pip install -r requirements.txt
