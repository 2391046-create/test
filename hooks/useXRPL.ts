/**
 * XRPL 지갑 훅 - 백엔드 API 연동
 */
import { useState } from "react";
import { connectWallet, getWallets, getWalletBalance, recordToXrpl } from "@/lib/api";

export function useXRPL(userId: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = async (seed: string, name?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await connectWallet(userId, seed, name) as any;
      return result;
    } catch (err) {
      setError(String(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const list = async () => {
    return getWallets(userId);
  };

  const balance = async (walletId: string) => {
    return getWalletBalance(walletId);
  };

  const recordTransaction = async (transactionId: string, walletSeed: string) => {
    setIsLoading(true);
    try {
      const result = await recordToXrpl(transactionId, walletSeed);
      return result;
    } catch (err) {
      setError(String(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, error, connect, list, balance, recordTransaction };
}
