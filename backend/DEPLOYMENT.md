# 배포 가이드

FastAPI 백엔드 서버 배포 방법

## 🐳 Docker 배포

### 1. 로컬 Docker 빌드 및 실행

```bash
# 이미지 빌드
docker build -t finance-compass-backend .

# 컨테이너 실행
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@host:5432/finance_compass" \
  -e GEMINI_API_KEY="your_key" \
  -e XRPL_WALLET_SEED="your_seed" \
  -e XRPL_ACCOUNT_ADDRESS="your_address" \
  finance-compass-backend
```

### 2. Docker Compose 사용

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 서비스 중지
docker-compose down
```

## ☁️ Heroku 배포

### 1. Heroku 설정

```bash
# Heroku CLI 설치
# https://devcenter.heroku.com/articles/heroku-cli

# 로그인
heroku login

# 앱 생성
heroku create finance-compass-backend

# PostgreSQL 추가
heroku addons:create heroku-postgresql:hobby-dev

# 환경 변수 설정
heroku config:set GEMINI_API_KEY="your_key"
heroku config:set XRPL_WALLET_SEED="your_seed"
heroku config:set XRPL_ACCOUNT_ADDRESS="your_address"
heroku config:set DEBUG="False"
```

### 2. Procfile 생성

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. 배포

```bash
# Git 커밋
git add .
git commit -m "Deploy to Heroku"

# 배포
git push heroku main

# 로그 확인
heroku logs --tail

# 앱 열기
heroku open
```

## 🚀 AWS EC2 배포

### 1. EC2 인스턴스 생성

```bash
# Ubuntu 22.04 LTS 선택
# t2.micro 또는 t2.small 권장
```

### 2. 서버 설정

```bash
# SSH 연결
ssh -i your-key.pem ubuntu@your-instance-ip

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 설치
sudo apt install -y python3.11 python3-pip

# PostgreSQL 설치
sudo apt install -y postgresql postgresql-contrib

# Git 설치
sudo apt install -y git

# 저장소 클론
git clone https://github.com/your-repo/finance-compass.git
cd finance-compass/backend

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
nano .env
```

### 3. Systemd 서비스 생성

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/finance-compass.service
```

```ini
[Unit]
Description=Finance Compass Backend
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/finance-compass/backend
Environment="PATH=/home/ubuntu/venv/bin"
ExecStart=/home/ubuntu/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable finance-compass
sudo systemctl start finance-compass

# 상태 확인
sudo systemctl status finance-compass
```

### 4. Nginx 리버스 프록시 설정

```bash
# Nginx 설치
sudo apt install -y nginx

# 설정 파일 생성
sudo nano /etc/nginx/sites-available/finance-compass
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/finance-compass /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL 인증서 설정 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 설정
sudo systemctl enable certbot.timer
```

## 🔐 프로덕션 보안 설정

### 1. 환경 변수 보안

```bash
# 환경 변수 파일 권한 설정
chmod 600 .env

# 시스템 환경 변수 사용 (권장)
export DATABASE_URL="..."
export GEMINI_API_KEY="..."
```

### 2. 데이터베이스 보안

```sql
-- PostgreSQL 사용자 생성
CREATE USER finance_user WITH PASSWORD 'strong_password';
CREATE DATABASE finance_compass OWNER finance_user;

-- 권한 설정
GRANT CONNECT ON DATABASE finance_compass TO finance_user;
GRANT USAGE ON SCHEMA public TO finance_user;
GRANT CREATE ON SCHEMA public TO finance_user;
```

### 3. 방화벽 설정

```bash
# UFW 활성화
sudo ufw enable

# 포트 허용
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 상태 확인
sudo ufw status
```

## 📊 모니터링

### 1. 로그 모니터링

```bash
# 실시간 로그 확인
sudo journalctl -u finance-compass -f

# 오류 로그 확인
sudo journalctl -u finance-compass -p err
```

### 2. 헬스 체크

```bash
# 정기적인 헬스 체크 (cron)
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart finance-compass
```

### 3. 성능 모니터링

```bash
# 서버 리소스 사용량
top

# 디스크 사용량
df -h

# 메모리 사용량
free -h
```

## 🔄 CI/CD 파이프라인

### GitHub Actions 예시

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t finance-compass-backend .
      
      - name: Push to Docker Hub
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag finance-compass-backend ${{ secrets.DOCKER_USERNAME }}/finance-compass-backend:latest
          docker push ${{ secrets.DOCKER_USERNAME }}/finance-compass-backend:latest
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            docker pull ${{ secrets.DOCKER_USERNAME }}/finance-compass-backend:latest
            docker-compose down
            docker-compose up -d
```

## 🆘 문제 해결

### 데이터베이스 연결 오류

```
psycopg2.OperationalError: could not connect to server
```

**해결책:**
```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 데이터베이스 연결 테스트
psql -U finance_user -d finance_compass -h localhost
```

### 메모리 부족

```bash
# 메모리 사용량 확인
free -h

# 스왑 메모리 추가
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### API 응답 느림

```bash
# 데이터베이스 쿼리 최적화
# - 인덱스 추가
# - 쿼리 최적화
# - 캐싱 구현

# 서버 리소스 증설
# - CPU 업그레이드
# - 메모리 증설
# - 로드 밸런싱 구현
```

## 📈 확장성

### 1. 로드 밸런싱

```nginx
upstream backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://backend;
    }
}
```

### 2. 캐싱

```python
# Redis 캐싱 추가
from redis import Redis

redis_client = Redis(host='localhost', port=6379, db=0)

@app.get("/transactions")
async def get_transactions(skip: int = 0, limit: int = 20):
    cache_key = f"transactions:{skip}:{limit}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # 데이터베이스 쿼리
    result = ...
    
    # 캐시 저장 (1시간)
    redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return result
```

### 3. 데이터베이스 복제

```bash
# PostgreSQL 복제 설정
# - Primary 서버 설정
# - Replica 서버 설정
# - 자동 페일오버 구성
```

## 📞 지원

배포 관련 문제는 GitHub Issues에 보고해주세요.
