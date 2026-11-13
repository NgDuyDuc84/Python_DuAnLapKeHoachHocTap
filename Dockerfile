FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput --settings=config.assets
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["python", "-m", "deploy.serve"]
