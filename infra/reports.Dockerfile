FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
ENV HOME=/tmp
ENTRYPOINT ["libreoffice", "--headless", "-env:UserInstallation=file:///tmp/creditsoft-lo", "--convert-to", "pdf", "--outdir", "/reports"]
