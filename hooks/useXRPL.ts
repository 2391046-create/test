/**
 * XRPL 훅 - receipt-scanner.tsx 시그니처에 맞춤
 * recordTransaction(expenseObj, walletSeed, backendUrl) 형태
 */
import { useState } from "react";

export interface XRPLExpenseData {
  merchant: string;
  amount: number;
  currency: string;
  category: string;
  description?: string;
  timestamp: string;
}

export interface XRPLRecordResult {
  success: boolean;
  tx_hash?: string;
  error?: string;
}

const DEFAULT_BACKEND = "http://localhost:8000";

export function useXRPL() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 지갑 연결 (seed → 주소 추출 + DB 저장)
   */
  const connectWallet = async (
    userId: string,
    walletSeed: string,
    walletName = "My Wallet",
    backendUrl = DEFAULT_BACKEND
  ) => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${backendUrl}/api/wallets/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, wallet_seed: walletSeed, wallet_name: walletName }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "지갑 연결 실패");
      return data;
    } catch (err: any) {
      setError(String(err?.message ?? err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 거래 데이터를 XRPL에 기록
   * receipt-scanner.tsx 호출: recordTransaction(expenseObj, seed, backendUrl)
   */
  const recordTransaction = async (
    expense: XRPLExpenseData,
    walletSeed: string,
    backendUrl = DEFAULT_BACKEND
  ): Promise<XRPLRecordResult> => {
    setIsLoading(true);
    setError(null);
    try {
      // 먼저 거래를 DB에 저장
      const createResp = await fetch(`${backendUrl}/api/transactions/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "default",
          merchant_name: expense.merchant,
          amount_local: expense.amount,
          currency: expense.currency,
          category: expense.category,
          source: "manual",
          description: expense.description ?? "",
          transaction_date: expense.timestamp.split("T")[0],
          record_xrpl: true,
          wallet_seed: walletSeed,
        }),
      });
      const createData = await createResp.json();
      if (!createResp.ok) throw new Error(createData.detail || "거래 생성 실패");

      const tx = createData.transaction;

      // XRPL에 기록
      const xrplResp = await fetch(
        `${backendUrl}/api/transactions/${tx.id}/record-xrpl?wallet_seed=${encodeURIComponent(walletSeed)}`,
        { method: "POST" }
      );
      const xrplData = await xrplResp.json();
      if (!xrplResp.ok) throw new Error(xrplData.detail || "XRPL 기록 실패");

      return {
        success: true,
        tx_hash: xrplData.tx_hash,
      };
    } catch (err: any) {
      const msg = String(err?.message ?? err);
      setError(msg);
      return { success: false, error: msg };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 지갑 잔액 조회
   */
  const getBalance = async (walletId: string, backendUrl = DEFAULT_BACKEND) => {
    try {
      const resp = await fetch(`${backendUrl}/api/wallets/${walletId}/balance`);
      return resp.json();
    } catch (err: any) {
      return { success: false, error: String(err?.message ?? err) };
    }
  };

  /**
   * 지갑 목록 조회
   */
  const listWallets = async (userId: string, backendUrl = DEFAULT_BACKEND) => {
    try {
      const resp = await fetch(`${backendUrl}/api/wallets/list?user_id=${userId}`);
      return resp.json();
    } catch (err: any) {
      return { success: false, error: String(err?.message ?? err) };
    }
  };

  return { isLoading, error, connectWallet, recordTransaction, getBalance, listWallets };
}
