"""
Finance Compass Backend 시작 스크립트
.env 파일에 GEMINI_API_KEY, NGROK_TOKEN만 있으면 바로 실행됩니다.

실행: python start.py
"""
import os
import sys
import subprocess

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NGROK_TOKEN = os.getenv("NGROK_TOKEN", "")
PORT = int(os.getenv("PORT", "8000"))


def check_env():
    """환경 변수 확인"""
    print("=" * 50)
    print("  Finance Compass Backend")
    print("=" * 50)

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY가 .env 파일에 없습니다!")
        print("   https://aistudio.google.com/app/apikey 에서 발급 후")
        print("   .env 파일에 GEMINI_API_KEY=your_key 추가하세요")
        sys.exit(1)
    else:
        print(f"✅ GEMINI_API_KEY: {GEMINI_API_KEY[:8]}...")

    if not NGROK_TOKEN:
        print("⚠️  NGROK_TOKEN 없음 - ngrok 터널 없이 로컬 전용으로 실행")
    else:
        print(f"✅ NGROK_TOKEN: {NGROK_TOKEN[:8]}...")

    print(f"🌐 포트: {PORT}")
    print("=" * 50)


def start_ngrok():
    """ngrok 터널 시작"""
    if not NGROK_TOKEN:
        return None

    try:
        from pyngrok import ngrok, conf

        # ngrok 설정
        conf.get_default().auth_token = NGROK_TOKEN

        # HTTP 터널 시작
        tunnel = ngrok.connect(PORT, "http")
        print(f"\n🌍 ngrok 공개 URL: {tunnel.public_url}")
        print(f"   프론트엔드에서 이 URL을 API 주소로 사용하세요")
        print(f"   예: EXPO_PUBLIC_API_URL={tunnel.public_url}")
        return tunnel
    except Exception as e:
        print(f"⚠️ ngrok 시작 실패: {e}")
        return None


def start_server():
    """uvicorn 서버 시작"""
    import uvicorn
    print(f"\n🚀 서버 시작: http://localhost:{PORT}")
    print(f"📚 API 문서: http://localhost:{PORT}/docs")
    print(f"   Ctrl+C로 종료\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        reload_dirs=["app"],
    )


if __name__ == "__main__":
    check_env()
    tunnel = start_ngrok()

    try:
        start_server()
    except KeyboardInterrupt:
        print("\n👋 서버 종료")
        if tunnel:
            from pyngrok import ngrok
            ngrok.kill()
