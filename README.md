# Finance Compass

유학생 재정 관리 + XRPL 블록체인 기반 생활비 송금/환전 앱

---

## 프로젝트 구조

```
XRPL_Project2/
├── app/                  # React Native (Expo) 앱 화면
├── server/               # tRPC 서버 (앱 자체 기능)
├── backend/              # FastAPI 서버 (XRPL 지갑/환전)
│   ├── app/              # 라우터, 모델, 서비스
│   ├── requirements.txt
│   └── .env.example
├── scripts/              # XRPL 초기 설정 스크립트
├── docker-compose.yml    # PostgreSQL DB
└── lib/
    └── livingFundApi.ts  # 앱 → FastAPI 연결 클라이언트
```

---

## 실행 전 준비

### 필수 설치

| 도구 | 버전 | 설치 |
|------|------|------|
| Node.js | 18+ | https://nodejs.org |
| Python | 3.11+ | https://python.org |
| Docker Desktop | 최신 | https://docker.com |
| pnpm | 9.x | `corepack enable pnpm` |
| Expo Go (폰) | 최신 | App Store / Play Store |

---

## 서버 실행 순서

서버가 **3개** 있어. 전부 따로 터미널 열어서 실행해야 해.

---

### 1. PostgreSQL DB (Docker)

```bash
docker-compose up -d
```

- DB가 **15432** 포트로 뜸
- 처음 한 번만 실행하면 컨테이너가 재시작 시 자동으로 켜짐
- 확인: `docker ps` → `postgres` 컨테이너가 `Up` 상태인지 확인

---

### 2. FastAPI 서버 (XRPL 지갑/환전)

#### 처음 한 번만: 환경 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
```

#### `.env` 파일 수정

```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:15432/livingfund
XRPL_TESTNET_URL=https://s.altnet.rippletest.net:51234
ENCRYPTION_KEY=<아래 명령어로 생성>
XRPL_ISSUER_ADDRESS=<팀원에게 받기>
XRPL_ISSUER_SEED=<팀원에게 받기>
```

> ENCRYPTION_KEY 생성 방법:
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

> XRPL_ISSUER_ADDRESS / XRPL_ISSUER_SEED 는 팀원 지희에게 받거나, `scripts/setup_issuer.py` 직접 실행해서 생성 가능

#### 서버 실행

```bash
# backend 폴더에서 (가상환경 활성화된 상태)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- `--host 0.0.0.0` 옵션을 붙여야 **폰에서도 접근 가능**
- 브라우저에서 확인: http://localhost:8000/docs (Swagger UI)

---

### 3. tRPC 서버 + Expo 앱

```bash
# 프로젝트 루트에서
pnpm install       # 처음 한 번만

# 터미널 두 개로 나눠서 실행
pnpm dev:server    # tRPC 서버 (포트 3000 또는 3001)
pnpm dev:metro     # Expo Metro 번들러 (포트 8081)
```

> **또는** `pnpm dev` 한 번에 둘 다 실행 (Windows에서 안 되면 위처럼 따로 실행)

- 브라우저에서 확인: http://localhost:8081
- 폰에서 확인: Expo Go 앱으로 터미널에 뜨는 QR 코드 스캔

---

## 폰(Expo Go)으로 테스트할 때

폰과 PC가 **같은 Wi-Fi**에 연결되어 있어야 함.

앱 실행 후 **설정 탭 → 백엔드 설정**에서 URL을 PC의 로컬 IP로 변경:

```
http://192.168.x.x:8000
```

> PC IP 확인 방법:
> - Windows: `ipconfig` → IPv4 주소
> - Mac/Linux: `ifconfig` → inet 주소

---

## XRPL 초기 설정 (처음 한 번만 — 이미 완료됐으면 스킵)

이미 `XRPL_ISSUER_ADDRESS`와 `XRPL_ISSUER_SEED`를 팀원에게 받았다면 스킵해도 됨.

직접 설정하려면:

```bash
# 가상환경 활성화 상태에서
cd scripts

# 1. 이슈어(발행자) 지갑 생성
python setup_issuer.py
# → 출력된 ISSUER_ADDRESS, ISSUER_SEED를 backend/.env에 입력

# 2. 유동성 공급 (DEX 환전용 오더북 세팅)
python add_liquidity.py
```

---

## 전체 실행 요약

| 터미널 | 명령어 | 포트 |
|--------|--------|------|
| 1 | `docker-compose up -d` | 15432 |
| 2 | `cd backend && uvicorn app.main:app --reload --host 0.0.0.0` | 8000 |
| 3 | `pnpm dev:server` | 3000/3001 |
| 4 | `pnpm dev:metro` | 8081 |
