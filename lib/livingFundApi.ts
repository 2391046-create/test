/**
 * LivingFund FastAPI 클라이언트 (TypeScript)
 *
 * 사용법: const api = livingFundApi(settings.backendUrl)
 * settings.tsx의 backendUrl이 우리 FastAPI 주소를 가리켜야 합니다.
 */

// ── 응답 타입 ─────────────────────────────────────────────────────────────

export type WalletBalance = {
  currency: string;
  amount: string;
  issuer: string | null;
};

export type WalletInfo = {
  id: string;
  user_id: string;
  xrpl_address: string;
  created_at: string;
  balances: WalletBalance[];
};

export type TxRecord = {
  id: string;
  wallet_id: string;
  tx_type: string;
  xrpl_tx_hash: string;
  status: string;
  amount: string;
  currency: string;
  memo: string | null;
  created_at: string;
};

export type ExchangeResult = {
  transaction: TxRecord;
  exchanged_amount: string;
  rate: string | null;
};

export type UserInfo = {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  created_at: string;
};

// ── 내부 fetch 헬퍼 ───────────────────────────────────────────────────────

async function req<T>(baseUrl: string, path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail ?? '요청 실패');
  return data as T;
}

// ── API 함수 묶음 ─────────────────────────────────────────────────────────

export const livingFundApi = (baseUrl: string) => ({

  /** 유저 생성 */
  createUser: (name: string, email: string, phone?: string) =>
    req<UserInfo>(baseUrl, '/api/users/', {
      method: 'POST',
      body: JSON.stringify({ name, email, phone }),
    }),

  /** XRPL 지갑 생성 (faucet + USD/EUR/KRW TrustLine, 15~30초 소요) */
  createWallet: (userId: string) =>
    req<WalletInfo>(baseUrl, '/api/wallets/', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, currencies: ['USD', 'EUR', 'KRW'] }),
    }),

  /** 지갑 조회 (XRPL 잔액 실시간 동기화) */
  getWallet: (walletId: string) =>
    req<WalletInfo>(baseUrl, `/api/wallets/${walletId}`),

  /** F02: 생활비 충전 (부모 Seed → 학생 지갑 Payment) */
  charge: (params: {
    recipientWalletId: string;
    senderSeed: string;
    amount: string;
    currency: string;
  }) =>
    req<TxRecord>(baseUrl, '/api/transactions/charge', {
      method: 'POST',
      body: JSON.stringify({
        recipient_wallet_id: params.recipientWalletId,
        sender_seed: params.senderSeed,
        amount: params.amount,
        currency: params.currency,
      }),
    }),

  /** F03: DEX 자동 환전 (to_amount=null → 오더북 환율 자동 계산) */
  exchange: (params: {
    walletId: string;
    fromCurrency: string;
    toCurrency: string;
    fromMax: string;
    slippagePct?: number;
  }) =>
    req<ExchangeResult>(baseUrl, '/api/transactions/exchange', {
      method: 'POST',
      body: JSON.stringify({
        wallet_id: params.walletId,
        from_currency: params.fromCurrency,
        to_currency: params.toCurrency,
        from_max: params.fromMax,
        to_amount: null,
        slippage_pct: params.slippagePct ?? 1,
      }),
    }),

  /** 트랜잭션 내역 조회 */
  getTransactions: (walletId: string) =>
    req<TxRecord[]>(baseUrl, `/api/transactions/wallet/${walletId}`),
});
