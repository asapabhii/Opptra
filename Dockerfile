# Stage 1: Build Next.js frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --no-fund --no-audit
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim
WORKDIR /app
COPY backend/ ./backend/
WORKDIR /app/backend
RUN python -m pip install --no-cache-dir --upgrade pip && \
	python -m pip install --no-cache-dir \
	fastapi==0.115.0 \
	uvicorn[standard]==0.30.6 \
	aiosqlite==0.20.0 \
	pydantic==2.8.2 \
	httpx==0.27.0 \
	anthropic==0.34.2 \
	openai==1.51.2 \
	google-generativeai==0.7.2 \
	python-dotenv==1.0.1
COPY --from=frontend-builder /app/frontend/out ./static
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
