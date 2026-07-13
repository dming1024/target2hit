FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    libxrender1 \
    libxext6 \
    fpocket \
    && rm -rf /var/lib/apt/lists/*

# Install RDKit
RUN pip install rdkit-pypi

# Install AutoDock Vina
RUN wget https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 -O /usr/local/bin/vina \
    && chmod +x /usr/local/bin/vina

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
