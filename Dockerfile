# ── Stage 1: Build React frontend ──────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python / FastAPI backend ──────────────────────
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# React build output → ./static (FastAPI がここから配信)
COPY --from=frontend-builder /app/frontend/dist ./static

RUN mkdir -p uploads

EXPOSE 7860

ENV DATABASE_URL=sqlite:///./memorial.db \
    SECRET_KEY=hf-demo-secret-key-change-me \
    BASE_URL=https://mystic-oracle-digital-memorial.hf.space \
    CORS_ORIGINS=*

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
