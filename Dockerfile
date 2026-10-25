FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY --chown=app:app creditsoft ./creditsoft
COPY --chown=app:app core ./core
COPY --chown=app:app manage.py ./
COPY --chown=app:app tools/container_start.py ./tools/container_start.py
RUN mkdir -p /app/staticfiles && chown app:app /app/staticfiles
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=3)"
CMD ["python", "tools/container_start.py"]
