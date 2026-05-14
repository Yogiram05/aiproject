# Installation & Deployment Guide

## 📦 Installation Options

### Option 1: Quick Install (Recommended for Development)

```bash
# 1. Navigate to project directory
cd healthcare-ocr-system

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux

# 5. Run the application
python main.py
```

### Option 2: Install with Specific OCR Engine

```bash
# For PaddleOCR (Best for handwriting)
pip install paddleocr paddlepaddle

# For Tesseract
pip install pytesseract
# Also install Tesseract OCR:
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Mac: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# For EasyOCR
pip install easyocr
```

### Option 3: Development Install (For Contributors)

```bash
# Install in editable mode with dev dependencies
pip install -e .
pip install pytest pytest-cov black flake8 mypy
```

---

## 🐳 Docker Deployment (Production)

### Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs logs models

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run Docker Container

```bash
# Build image
docker build -t healthcare-ocr-system .

# Run container
docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads healthcare-ocr-system

# Or with docker-compose (create docker-compose.yml first)
docker-compose up
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    environment:
      - DEBUG=False
      - ENVIRONMENT=production
    restart: unless-stopped
```

---

## ☁️ Cloud Deployment

### Deploy to Heroku

```bash
# 1. Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# 2. Login to Heroku
heroku login

# 3. Create new app
heroku create healthcare-ocr-app

# 4. Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port $PORT" > Procfile

# 5. Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# 6. Open app
heroku open
```

### Deploy to AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 20.04)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx

# 4. Clone your repository
git clone your-repo-url
cd healthcare-ocr-system

# 5. Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Configure Nginx (create /etc/nginx/sites-available/healthcare-ocr)
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 7. Enable site
sudo ln -s /etc/nginx/sites-available/healthcare-ocr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. Run with systemd (create /etc/systemd/system/healthcare-ocr.service)
[Unit]
Description=Healthcare OCR System
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/healthcare-ocr-system
Environment="PATH=/home/ubuntu/healthcare-ocr-system/venv/bin"
ExecStart=/home/ubuntu/healthcare-ocr-system/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target

# 9. Start service
sudo systemctl daemon-reload
sudo systemctl start healthcare-ocr
sudo systemctl enable healthcare-ocr
```

### Deploy to Azure App Service

```bash
# 1. Install Azure CLI
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# 2. Login to Azure
az login

# 3. Create resource group
az group create --name HealthcareOCR-RG --location eastus

# 4. Create App Service plan
az appservice plan create \
    --name HealthcareOCR-Plan \
    --resource-group HealthcareOCR-RG \
    --sku B1 \
    --is-linux

# 5. Create web app
az webapp create \
    --name healthcare-ocr-app \
    --resource-group HealthcareOCR-RG \
    --plan HealthcareOCR-Plan \
    --runtime "PYTHON|3.9"

# 6. Configure deployment
az webapp config set \
    --name healthcare-ocr-app \
    --resource-group HealthcareOCR-RG \
    --startup-file "uvicorn main:app --host 0.0.0.0 --port 8000"

# 7. Deploy from local git
az webapp deployment source config-local-git \
    --name healthcare-ocr-app \
    --resource-group HealthcareOCR-RG

# 8. Push code
git remote add azure <deployment-url>
git push azure main
```

### Deploy to Google Cloud Platform

```bash
# 1. Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# 2. Initialize gcloud
gcloud init

# 3. Create app.yaml
runtime: python39
entrypoint: uvicorn main:app --host 0.0.0.0 --port $PORT

# 4. Deploy
gcloud app deploy

# 5. View app
gcloud app browse
```

---

## 🔒 Production Configuration

### Environment Variables (.env for production)

```bash
# Application
APP_NAME=Healthcare OCR System
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production

# Server
HOST=0.0.0.0
PORT=8000

# Security
ENCRYPTION_KEY=your-super-secret-encryption-key-here-change-this
SECRET_KEY=your-jwt-secret-key-here

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost:5432/healthcare_ocr

# Redis
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# File Upload
MAX_UPLOAD_SIZE=20971520  # 20MB
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,tiff

# OCR
OCR_ENGINE=paddleocr
OCR_CONFIDENCE_THRESHOLD=0.7

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/healthcare-ocr/app.log

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Security Checklist

- [ ] Change all default passwords and secrets
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Set up rate limiting
- [ ] Enable authentication
- [ ] Configure CORS properly
- [ ] Regular security updates
- [ ] Backup strategy
- [ ] Monitoring and alerts
- [ ] Log rotation

---

## 📊 Monitoring & Logging

### Setup Logging

```python
# In production, use cloud logging
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10000000,  # 10MB
    backupCount=5
)

logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Monitoring with Prometheus

```python
# Add to requirements.txt
prometheus-fastapi-instrumentator==5.9.1

# In main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

---

## 🧪 Testing in Production

```bash
# Health check
curl https://your-domain.com/api/v1/health

# Upload test
curl -X POST https://your-domain.com/api/v1/upload \
  -F "file=@test.jpg" \
  -F "document_type=prescription"

# Load testing with Apache Bench
ab -n 1000 -c 10 https://your-domain.com/api/v1/health
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions (.github/workflows/deploy.yml)

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      - name: Run tests
        run: pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          # Your deployment script here
```

---

## 💾 Database Setup (Optional)

### PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE healthcare_ocr;
CREATE USER healthcare_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE healthcare_ocr TO healthcare_user;

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://healthcare_user:your_password@localhost:5432/healthcare_ocr
```

---

## 🚀 Performance Optimization

### Enable Caching

```python
# Install Redis
pip install redis

# In your code
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)
```

### Use GPU for OCR (if available)

```python
# Install CUDA-enabled PaddlePaddle
pip install paddlepaddle-gpu

# In config
OCR_USE_GPU=True
```

---

## 📱 Mobile/Progressive Web App

### Add to frontend/index.html

```html
<!-- Add to <head> -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#667eea">
<link rel="manifest" href="/manifest.json">

<!-- Create manifest.json -->
{
  "name": "Healthcare OCR System",
  "short_name": "Health OCR",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#667eea",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

---

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <pid> /F
   
   # Linux/Mac
   lsof -ti:8000 | xargs kill -9
   ```

2. **Module not found**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Permission denied**
   ```bash
   chmod +x main.py
   sudo chown -R $USER:$USER .
   ```

---

## 📞 Support

For deployment help:
- Check logs: `tail -f logs/app.log`
- Review docs: README.md
- Test locally first
- Contact: [Your support email]

---

**🎉 You're Ready to Deploy! 🎉**

Choose your deployment method and follow the steps above. The system is production-ready!
