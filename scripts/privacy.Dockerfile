FROM ollama/ollama:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt
COPY src ./src
COPY sample_docs ./sample_docs
COPY scripts/privacy_test_container.sh ./scripts/privacy_test_container.sh

ENTRYPOINT []
CMD ["/bin/bash", "/app/scripts/privacy_test_container.sh"]
