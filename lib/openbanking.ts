/**
 * 오픈뱅킹 API 연동
 * 한국 주요 은행의 거래내역 자동 조회
 * 
 * 지원 은행:
 * - KB국민은행 (004)
 * - 우리은행 (020)
 * - 신한은행 (088)
 * - 하나은행 (081)
 * - 농협 (011)
 * - 기업은행 (003)
 */

export type BankCode = '004' | '020' | '088' | '081' | '011' | '003';

export type OpenBankingTransaction = {
  transactionDate: string; // YYYYMMDD
  transactionTime?: string; // HHMMSS
  transactionAmount: number;
  transactionType: 'DEBIT' | 'CREDIT'; // 출금/입금
  transactionName: string; // 거래처명
  transactionMemo?: string;
  balance?: number;
  transactionUniqueId: string;
};

export type BankAccount = {
  bankCode: BankCode;
  bankName: string;
  accountNumber: string;
  accountHolder: string;
  accountType: string;
  currency: string;
  balance: number;
};

/**
 * 오픈뱅킹 인증 토큰 획득
 * 실제 구현: OAuth 2.0 기반 사용자 인증
 */
export async function getOpenBankingToken(
  clientId: string,
  clientSecret: string,
  redirectUri: string,
  authCode: string
): Promise<string> {
  try {
    const response = await fetch('https://openapi.openbanking.or.kr/oauth/2.0/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: authCode,
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirectUri,
      }).toString(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get token: ${response.statusText}`);
    }

    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error('Failed to get OpenBanking token:', error);
    throw error;
  }
}

/**
 * 사용자 계좌 목록 조회
 */
export async function getAccounts(accessToken: string): Promise<BankAccount[]> {
  try {
    const response = await fetch('https://openapi.openbanking.or.kr/v2.0/user/account', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get accounts: ${response.statusText}`);
    }

    const data = await response.json();
    return data.res_list.map((account: any) => ({
      bankCode: account.bank_code as BankCode,
      bankName: account.bank_name,
      accountNumber: account.account_num_masked,
      accountHolder: account.account_holder_name,
      accountType: account.account_type,
      currency: account.currency_code,
      balance: parseFloat(account.account_balance),
    }));
  } catch (error) {
    console.error('Failed to get accounts:', error);
    throw error;
  }
}

/**
 * 거래내역 조회
 * @param accessToken - 오픈뱅킹 액세스 토큰
 * @param bankCode - 은행 코드
 * @param accountNumber - 계좌번호 (마스킹된 번호)
 * @param startDate - 조회 시작일 (YYYYMMDD)
 * @param endDate - 조회 종료일 (YYYYMMDD)
 */
export async function getTransactions(
  accessToken: string,
  bankCode: BankCode,
  accountNumber: string,
  startDate: string,
  endDate: string
): Promise<OpenBankingTransaction[]> {
  try {
    const response = await fetch('https://openapi.openbanking.or.kr/v2.0/account/transaction/list', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get transactions: ${response.statusText}`);
    }

    const data = await response.json();
    return data.res_list.map((tx: any) => ({
      transactionDate: tx.tran_date,
      transactionTime: tx.tran_time,
      transactionAmount: parseFloat(tx.tran_amt),
      transactionType: tx.tran_type as 'DEBIT' | 'CREDIT',
      transactionName: tx.merch_name || tx.tran_memo,
      transactionMemo: tx.tran_memo,
      balance: parseFloat(tx.balance_amt),
      transactionUniqueId: tx.tran_id,
    }));
  } catch (error) {
    console.error('Failed to get transactions:', error);
    throw error;
  }
}

/**
 * 오픈뱅킹 인증 URL 생성
 */
export function generateAuthUrl(
  clientId: string,
  redirectUri: string,
  scope: string = 'login account_balance transfer_history'
): string {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: redirectUri,
    scope,
    state: Math.random().toString(36).substring(7),
  });

  return `https://openapi.openbanking.or.kr/oauth/2.0/authorize?${params.toString()}`;
}

/**
 * 모의 오픈뱅킹 거래내역 (개발/테스트용)
 */
export function getMockTransactions(): OpenBankingTransaction[] {
  const today = new Date();
  return [
    {
      transactionDate: today.toISOString().slice(0, 10).replace(/-/g, ''),
      transactionTime: '14:30:00',
      transactionAmount: 5400,
      transactionType: 'DEBIT',
      transactionName: 'STARBUCKS LONDON',
      transactionMemo: 'Coffee',
      balance: 1500000,
      transactionUniqueId: 'TXN001',
    },
    {
      transactionDate: today.toISOString().slice(0, 10).replace(/-/g, ''),
      transactionTime: '10:15:00',
      transactionAmount: 45000,
      transactionType: 'DEBIT',
      transactionName: 'TESCO SUPERMARKET',
      transactionMemo: 'Groceries',
      balance: 1505400,
      transactionUniqueId: 'TXN002',
    },
    {
      transactionDate: (today.getTime() - 86400000).toString().slice(0, 10).replace(/-/g, ''),
      transactionTime: '18:45:00',
      transactionAmount: 120000,
      transactionType: 'DEBIT',
      transactionName: 'UNIVERSITY OF LONDON',
      transactionMemo: 'Tuition Fee',
      balance: 1550400,
      transactionUniqueId: 'TXN003',
    },
  ];
}
