FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production STORAGE_BACKEND=supabase
WORKDIR /app
COPY services/api/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --create-home appuser
COPY services/api/blackfire ./blackfire
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn blackfire.main:app --host 0.0.0.0 --port ${PORT:-8000} --no-proxy-headers"]
