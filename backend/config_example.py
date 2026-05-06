# 환경 변수 설정 예시
# 실제 사용 시 다음 환경 변수들을 설정해야 합니다:

"""
DATABASE_URL: PostgreSQL 연결 문자열
  예: postgresql://user:password@localhost:5432/finance_compass

GEMINI_API_KEY: Google Gemini AI API 키
  https://makersuite.google.com/app/apikey 에서 발급

XRPL_NETWORK_URL: XRPL 네트워크 URL
  테스트넷: https://s.altnet.rippletest.net:51234
  메인넷: https://s1.ripple.com:51234

XRPL_WALLET_SEED: XRPL 지갑 시드 (비밀키)
  XRPL 테스트넷에서 생성 가능: https://xrpl.org/xrp-testnet-faucet.html

XRPL_ACCOUNT_ADDRESS: XRPL 계정 주소
  예: rN7n7otQDd6FczFgLdlqtyMVrn3Rqq5Qx

DEBUG: 디버그 모드 (True/False)

SECRET_KEY: JWT 토큰 서명용 시크릿 키

CORS_ORIGINS: CORS 허용 오리진 (JSON 배열)
  예: ["http://localhost:3000", "http://localhost:8081"]
"""
