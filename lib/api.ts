/**
 * Finance Compass API 클라이언트
 * 백엔드 URL은 .env 파일의 EXPO_PUBLIC_API_URL에서 읽음
 * ngrok 실행 시 터미널에 출력된 URL을 사용하세요
 */

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "요청 실패" }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ── 영수증 분석 ──────────────────────────────────────
export async function analyzeReceipt(
  imageBase64: string,
  userId: string,
  currency = "USD"
) {
  return apiCall("/api/transactions/analyze-receipt", {
    method: "POST",
    body: JSON.stringify({
      image_base64: imageBase64,
      currency,
      user_id: userId,
    }),
  });
}

// ── 은행 알림 분석 ───────────────────────────────────
export async function analyzeBankNotification(
  notificationText: string,
  userId: string,
  currency = "KRW"
) {
  return apiCall("/api/transactions/analyze-bank-notification", {
    method: "POST",
    body: JSON.stringify({
      notification_text: notificationText,
      currency,
      user_id: userId,
    }),
  });
}

// ── 거래 목록 조회 ───────────────────────────────────
export async function getTransactions(
  userId: string,
  options?: {
    category?: string;
    startDate?: string;
    endDate?: string;
    limit?: number;
  }
) {
  const params = new URLSearchParams({ user_id: userId });
  if (options?.category) params.append("category", options.category);
  if (options?.startDate) params.append("start_date", options.startDate);
  if (options?.endDate) params.append("end_date", options.endDate);
  if (options?.limit) params.append("limit", String(options.limit));

  return apiCall(`/api/transactions/list?${params}`);
}

// ── 거래 수정 ────────────────────────────────────────
export async function updateTransaction(
  transactionId: string,
  updates: { category?: string; merchant_name?: string; description?: string }
) {
  return apiCall(`/api/transactions/${transactionId}`, {
    method: "PUT",
    body: JSON.stringify(updates),
  });
}

// ── XRPL 기록 ────────────────────────────────────────
export async function recordToXrpl(transactionId: string, walletSeed: string) {
  return apiCall(
    `/api/transactions/${transactionId}/record-xrpl?wallet_seed=${encodeURIComponent(walletSeed)}`,
    { method: "POST" }
  );
}

// ── PDF 보고서 ───────────────────────────────────────
export async function generateReport(
  userId: string,
  startDate: string,
  endDate: string
) {
  const url = `${API_BASE}/api/transactions/generate-report`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, start_date: startDate, end_date: endDate }),
  });

  if (!response.ok) throw new Error("PDF 생성 실패");
  return response.blob();
}

// ── 메뉴판 분석 ──────────────────────────────────────
export async function analyzeMenu(
  imageBase64: string | null,
  text: string | null,
  currency = "USD"
) {
  return apiCall("/api/menu/analyze", {
    method: "POST",
    body: JSON.stringify({ image_base64: imageBase64, text, currency }),
  });
}

// ── 환율 조회 ────────────────────────────────────────
export async function getExchangeRates() {
  return apiCall("/api/rates/");
}

export async function getExchangeRate(currency: string) {
  return apiCall(`/api/rates/${currency}`);
}

// ── 지갑 ────────────────────────────────────────────
export async function connectWallet(
  userId: string,
  walletSeed: string,
  walletName = "My Wallet"
) {
  return apiCall("/api/wallets/connect", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      wallet_seed: walletSeed,
      wallet_name: walletName,
    }),
  });
}

export async function getWallets(userId: string) {
  return apiCall(`/api/wallets/list?user_id=${userId}`);
}

export async function getWalletBalance(walletId: string) {
  return apiCall(`/api/wallets/${walletId}/balance`);
}

// ── 사용자 설정 ──────────────────────────────────────
export async function getUserSettings(userId: string) {
  return apiCall(`/api/users/${userId}/settings`);
}

export async function updateUserSettings(
  userId: string,
  settings: {
    default_currency?: string;
    preferred_country?: string;
    monthly_budget?: number;
    category_budgets?: Record<string, number>;
  }
) {
  return apiCall(`/api/users/${userId}/settings`, {
    method: "PUT",
    body: JSON.stringify(settings),
  });
}

export async function createUser(
  email: string,
  name?: string,
  currency = "USD"
) {
  return apiCall("/api/users/create", {
    method: "POST",
    body: JSON.stringify({ email, name, default_currency: currency }),
  });
}
