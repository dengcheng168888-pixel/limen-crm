FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && groupadd -g 10001 crm && useradd -u 10001 -g crm -M crm && mkdir /app/data && chown crm:crm /app/data
COPY app.py index.html ./
USER crm
ENV CRM_DATA=/app/data PYTHONDONTWRITEBYTECODE=1
EXPOSE 8780
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port \"${PORT:-8780}\" --workers 1"]
