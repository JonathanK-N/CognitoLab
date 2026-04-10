# Base: image officielle Renode (Ubuntu 22.04 + Mono/.NET + Renode pre-installé)
FROM ghcr.io/renode/renode:latest

USER root

# Installer Python 3.11 et pip
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11 par défaut
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python  python  /usr/bin/python3.11 1

WORKDIR /app

# Firmwares démo pré-compilés (Zephyr Hello World depuis CDN Antmicro/Renode)
RUN mkdir -p /app/firmwares

# STM32F4 Discovery — Zephyr hello_world (UART sur usart2)
RUN curl -fsSL \
    "https://dl.antmicro.com/projects/renode/stm32f4discovery--zephyr-hello_world.elf-s_462260-c13b4f9e58cbe5a5de1c895bfb977bced5695f8e" \
    -o /app/firmwares/stm32f4_demo.elf || echo "[warn] stm32f4 firmware not downloaded"

# RP2040 (Raspberry Pi Pico) — Zephyr hello_world (UART sur uart0)
RUN curl -fsSL \
    "https://dl.antmicro.com/projects/renode/rpi_pico--zephyr-hello_world.elf-s_485256-1e3c2b5a7d9f0e8c4a6b2d4f6e8a0c2e4a6b8d0f" \
    -o /app/firmwares/rp2040_demo.elf || echo "[warn] rp2040 firmware not downloaded"

# STM32F103 (Blue Pill) — Zephyr hello_world (UART sur usart1)
RUN curl -fsSL \
    "https://dl.antmicro.com/projects/renode/stm32f103re_nucleo--zephyr-hello_world.elf-s_458432-02f5c7b19b4a7c4c6a1e6f1d8c7f2e91a3b5d4e6" \
    -o /app/firmwares/stm32f103_demo.elf || echo "[warn] stm32f103 firmware not downloaded"

# Dépendances Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Code applicatif
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

EXPOSE 5000

# gevent worker : indispensable pour SSE (connexions longues) sans bloquer les autres requêtes
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --worker-class gevent --worker-connections 100 --timeout 300 app:app"]
