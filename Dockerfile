FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY versionghost ./versionghost
COPY sample_app ./sample_app
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["sh", "-c", "uvicorn versionghost.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
