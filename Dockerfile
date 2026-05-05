FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MODEL_PROVIDER=mock
ENV APP_MODE=streamlit
ENV APP_PORT=8080
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"api\" ]; then uvicorn api:app --host 0.0.0.0 --port ${APP_PORT:-8080}; else streamlit run app.py --server.port=${APP_PORT:-8080} --server.address=0.0.0.0 --server.headless=true; fi"]
