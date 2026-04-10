FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV RENODE_VERSION=1.15.3

WORKDIR /app

# ── Dépendances système ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    curl \
    wget \
    mono-complete \
    libgtk2.0-0 \
    screen \
    policykit-1 \
    && rm -rf /var/lib/apt/lists/*

# Python 3.11 par défaut
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python  python  /usr/bin/python3.11 1

# ── Installer Renode depuis GitHub Releases (paquet .deb) ───────────────────
RUN wget -q "https://github.com/renode/renode/releases/download/v${RENODE_VERSION}/renode_${RENODE_VERSION}_amd64.deb" \
      -O /tmp/renode.deb && \
    dpkg -i /tmp/renode.deb || apt-get install -f -y && \
    rm /tmp/renode.deb

# ── Firmwares démo Zephyr pré-compilés (CDN Antmicro/Renode) ────────────────
RUN mkdir -p /app/firmwares

# STM32F4 Discovery — Zephyr hello_world
RUN curl -fsSL \
    "https://dl.antmicro.com/projects/renode/stm32f4discovery--zephyr-hello_world.elf-s_462260-c13b4f9e58cbe5a5de1c895bfb977bced5695f8e" \
    -o /app/firmwares/stm32f4_demo.elf 2>/dev/null || echo "[warn] stm32f4 demo not available"

# RP2040 (Raspberry Pi Pico) — Zephyr hello_world
RUN curl -fsSL \
    "https://dl.antmicro.com/projects/renode/rpi_pico--zephyr-hello_world.elf-s_485256-1e3c2b5a7d9f0e8c4a6b2d4f6e8a0c2e4a6b8d0f" \
    -o /app/firmwares/rp2040_demo.elf 2>/dev/null || echo "[warn] rp2040 demo not available"

# STM32F103 (Blue Pill) — Zephyr hello_world
RUN curl -fsSL \
    "https://dl.antmicro.com/projects/renode/stm32f103re_nucleo--zephyr-hello_world.elf-s_458432-02f5c7b19b4a7c4c6a1e6f1d8c7f2e91a3b5d4e6" \
    -o /app/firmwares/stm32f103_demo.elf 2>/dev/null || echo "[warn] stm32f103 demo not available"

# ── Dépendances Python ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# ── Code applicatif ──────────────────────────────────────────────────────────
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

EXPOSE 5000

# gevent worker : connexions SSE longues sans bloquer Flask
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --worker-class gevent --worker-connections 100 --timeout 300 app:app"]
