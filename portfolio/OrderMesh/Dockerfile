FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml .
COPY ordermesh ./ordermesh
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY ordermesh ./ordermesh
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["uvicorn", "ordermesh.api:app", "--host", "0.0.0.0", "--port", "8000"]
