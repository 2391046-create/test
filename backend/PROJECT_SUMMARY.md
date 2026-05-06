# Finance Compass Backend - 프로젝트 요약

## 📋 개요

**Finance Compass Backend**는 유학생의 재정 관리를 돕기 위한 FastAPI 기반의 백엔드 서버입니다. Gemini AI를 활용한 자동 분류, XRPL 블록체인 연동, PostgreSQL 데이터베이스를 통해 완벽한 지출 관리 시스템을 제공합니다.

## 🎯 핵심 기능

### 1️⃣ Gemini AI 연동
- **결제 텍스트 분석**: "[신한카드] 스타벅스 ₩5,500"과 같은 결제 알림을 자동으로 분석
- **영수증 OCR**: 영수증 이미지를 인식하여 상호명, 금액, 카테고리 자동 추출
- **신뢰도 점수**: 분류 결과의 정확도를 0-1 사이의 점수로 반환

```python
# 사용 예시
POST /classify
{
  "text": "[신한카드] 스타벅스 ₩5,500 승인"
}

응답:
{
  "merchant": "스타벅스",
  "amount": 5500,
  "currency": "KRW",
  "category": "food",
  "confidence": 0.95
}
```

### 2️⃣ XRPL 블록체인 연동
- **지출 기록**: 분류된 지출 내역을 XRPL 네트워크에 트랜잭션으로 기록
- **Memo 필드 활용**: 지출 정보를 JSON 형식으로 XRPL Memo에 저장
- **투명성 보장**: 모든 거래가 블록체인에 불변적으로 기록됨

```json
{
  "type": "expense",
  "merchant": "스타벅스",
  "amount": 5500,
  "currency": "KRW",
  "category": "food",
  "description": "아메리카노",
  "timestamp": "2026-05-06T14:30:00",
  "app": "FinanceCompass"
}
```

### 3️⃣ 데이터베이스 설계
- **사용자 관리**: 사용자 정보 및 인증
- **거래 기록**: 모든 지출 내역 저장
- **예산 관리**: 월별 카테고리별 예산 설정 및 추적
- **XRPL 연동**: 블록체인 트랜잭션 정보 저장

### 4️⃣ REST API
- **분류 API** (`/classify`): 결제 내역 자동 분류
- **기록 API** (`/record`): 거래 기록 및 XRPL 저장
- **조회 API** (`/transactions`): 거래 내역 조회
- **예산 API** (`/budgets`): 예산 설정 및 상태 조회
- **XRPL API** (`/xrpl/*`): 블록체인 트랜잭션 조회

## 📁 파일 구조

```
backend/
├── main.py                    # FastAPI 메인 애플리케이션
├── config.py                  # 환경 설정 관리
├── models.py                  # SQLAlchemy ORM 모델
├── schemas.py                 # Pydantic 스키마
├── database.py                # 데이터베이스 연결
├── gemini_service.py          # Gemini AI 연동 모듈
├── xrpl_service.py            # XRPL 블록체인 연동 모듈
├── types.py                   # 타입 정의
├── test_api.py                # API 테스트 스크립트
├── requirements.txt           # Python 의존성
├── Dockerfile                 # Docker 이미지 정의
├── docker-compose.yml         # Docker Compose 설정
├── README.md                  # 프로젝트 설명서
├── FRONTEND_INTEGRATION.md    # 프론트엔드 통합 가이드
├── DEPLOYMENT.md              # 배포 가이드
└── PROJECT_SUMMARY.md         # 이 파일
```

## 🔧 기술 스택

| 계층 | 기술 |
|------|------|
| **API Framework** | FastAPI 0.104.1 |
| **Web Server** | Uvicorn 0.24.0 |
| **ORM** | SQLAlchemy 2.0.23 |
| **Database** | PostgreSQL 15 |
| **AI/ML** | Google Gemini API |
| **Blockchain** | XRPL (xrpl-py 3.0.0) |
| **Validation** | Pydantic 2.5.0 |
| **Containerization** | Docker & Docker Compose |
| **Testing** | Pytest (선택사항) |

## 🚀 빠른 시작

### 1. 환경 설정

```bash
cd backend

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finance_compass
GEMINI_API_KEY=your_gemini_api_key
XRPL_NETWORK_URL=https://s.altnet.rippletest.net:51234
XRPL_WALLET_SEED=your_xrpl_wallet_seed
XRPL_ACCOUNT_ADDRESS=your_xrpl_account_address
DEBUG=True
EOF
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 시작
sudo systemctl start postgresql

# 데이터베이스 생성
createdb finance_compass
```

### 4. 서버 실행

```bash
python main.py
# 또는
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.

### 5. API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📊 데이터 흐름

```
┌─────────────────────┐
│  React Native App   │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ /classify    │ ◄─── 결제 텍스트/이미지
    │ /record      │
    │ /transactions│
    │ /budgets     │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────┐
    │  Gemini AI Service   │
    │  XRPL Service        │
    │  Database Service    │
    └──────┬───────────────┘
           │
           ├─────────────────────┐
           │                     │
           ▼                     ▼
    ┌────────────────┐   ┌──────────────┐
    │  PostgreSQL    │   │ XRPL Network │
    │  Database      │   │ (Blockchain) │
    └────────────────┘   └──────────────┘
```

## 🔐 보안 고려사항

### ✅ 구현된 보안 기능

1. **환경 변수 관리**
   - API 키와 지갑 시드는 환경 변수로 관리
   - 코드에 하드코딩되지 않음

2. **CORS 설정**
   - 신뢰할 수 있는 도메인만 허용
   - 프론트엔드와의 안전한 통신

3. **데이터 검증**
   - Pydantic을 통한 입력 검증
   - SQL 인젝션 방지

4. **에러 처리**
   - 민감한 정보 노출 방지
   - 적절한 HTTP 상태 코드 반환

### ⚠️ 프로덕션 체크리스트

- [ ] HTTPS 활성화
- [ ] 데이터베이스 비밀번호 강화
- [ ] Rate Limiting 구현
- [ ] 로깅 및 모니터링 설정
- [ ] 백업 및 복구 계획 수립
- [ ] 정기적인 보안 감사

## 🧪 테스트

### API 테스트 실행

```bash
python test_api.py
```

### 개별 엔드포인트 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 분류 테스트
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "[신한카드] 스타벅스 ₩5,500 승인"}'

# 거래 조회
curl http://localhost:8000/transactions
```

## 🐳 Docker 배포

### Docker Compose 사용

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 서비스 중지
docker-compose down
```

## 📈 성능 최적화

### 1. 데이터베이스 인덱싱
```sql
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
```

### 2. 캐싱 전략
- Redis를 사용한 자주 조회되는 데이터 캐싱
- 예산 상태 조회 결과 캐싱 (1시간)

### 3. 쿼리 최적화
- N+1 쿼리 문제 해결
- 배치 처리를 통한 성능 향상

## 🔄 CI/CD 파이프라인

### GitHub Actions 자동 배포

```yaml
# .github/workflows/deploy.yml
- Docker 이미지 빌드
- 테스트 실행
- Docker Hub에 푸시
- 서버에 자동 배포
```

## 📞 지원 및 문제 해결

### 일반적인 문제

| 문제 | 해결책 |
|------|--------|
| 데이터베이스 연결 오류 | PostgreSQL 상태 확인, 연결 문자열 확인 |
| Gemini API 오류 | API 키 확인, 할당량 확인 |
| XRPL 트랜잭션 실패 | 지갑 잔액 확인, 네트워크 상태 확인 |
| CORS 오류 | CORS_ORIGINS 설정 확인 |

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [Google Gemini API](https://ai.google.dev/)
- [XRPL 개발자 가이드](https://xrpl.org/docs/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)

## 📝 라이선스

MIT License

## 👥 기여

Pull Request를 환영합니다!

## 🎓 학습 자료

이 프로젝트를 통해 배울 수 있는 것:

1. **FastAPI 기초**: 빠르고 현대적인 웹 API 개발
2. **데이터베이스 설계**: 관계형 데이터베이스 모델링
3. **AI 통합**: 외부 AI 서비스 연동
4. **블록체인**: XRPL 네트워크 활용
5. **배포**: Docker, Heroku, AWS를 통한 배포
6. **보안**: API 보안 및 데이터 보호

---

**마지막 업데이트**: 2026-05-06
**버전**: 1.0.0
