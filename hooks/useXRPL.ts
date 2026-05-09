import { useState } from "react";
import { XRPLTransactionResult } from "@/types";

export function useXRPL() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [txHash, setTxHash] = useState<string | null>(null);

  const recordTransaction = async (
    expenseData: Record<string, any>,
    walletSeed: string,
    backendUrl: string
  ): Promise<XRPLTransactionResult> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${backendUrl}/api/expenses/record`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          expense_data: expenseData,
          wallet_seed: walletSeed,
        }),
      });

      if (!response.ok) {
        throw new Error("XRPL 기록 실패");
      }

      const data = await response.json();
      const result = data.data as XRPLTransactionResult;

      if (result.success && result.tx_hash) {
        setTxHash(result.tx_hash);
      }

      setIsLoading(false);
      return result;
    } catch (err) {
      const errorMsg = "XRPL 기록 오류: " + String(err);
      setError(errorMsg);
      setIsLoading(false);
      throw err;
    }
  };

  const getTransactionInfo = async (
    txHash: string,
    backendUrl: string
  ): Promise<XRPLTransactionResult> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${backendUrl}/api/expenses/transaction-info`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tx_hash: txHash,
        }),
      });

      if (!response.ok) {
        throw new Error("트랜잭션 조회 실패");
      }

      const data = await response.json();
      const result = data.data as XRPLTransactionResult;

      setIsLoading(false);
      return result;
    } catch (err) {
      const errorMsg = "조회 오류: " + String(err);
      setError(errorMsg);
      setIsLoading(false);
      throw err;
    }
  };

  const clearError = () => {
    setError(null);
  };

  return {
    isLoading,
    error,
    txHash,
    recordTransaction,
    getTransactionInfo,
    clearError,
  };
}
