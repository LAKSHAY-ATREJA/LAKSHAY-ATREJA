FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
CMD ["uvicorn","streamforge.api:app","--host","0.0.0.0","--port","8000"]
