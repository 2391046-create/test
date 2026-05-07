import { useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { ReceiptAnalysisResult, MenuAnalysisResult } from "@/types";

export interface SavedTransaction {
  id: string;
  type: "receipt" | "menu" | "dutch_pay";
  data: ReceiptAnalysisResult | MenuAnalysisResult | any;
  xrplTxHash?: string;
  savedAt: string;
  notes?: string;
}

const STORAGE_KEY = "saved_transactions";

export function useTransactionStorage() {
  const [transactions, setTransactions] = useState<SavedTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 저장된 거래 내역 로드
  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        setTransactions(JSON.parse(stored));
      }
      setIsLoading(false);
    } catch (error) {
      console.error("거래 내역 로드 실패:", error);
      setIsLoading(false);
    }
  };

  const saveTransaction = async (
    type: "receipt" | "menu" | "dutch_pay",
    data: any,
    notes?: string
  ): Promise<SavedTransaction> => {
    try {
      const newTransaction: SavedTransaction = {
        id: `${type}_${Date.now()}`,
        type,
        data,
        savedAt: new Date().toISOString(),
        notes,
      };

      const updated = [newTransaction, ...transactions];
      setTransactions(updated);
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));

      return newTransaction;
    } catch (error) {
      console.error("거래 내역 저장 실패:", error);
      throw error;
    }
  };

  const updateTransactionXRPL = async (
    transactionId: string,
    xrplTxHash: string
  ) => {
    try {
      const updated = transactions.map((tx) =>
        tx.id === transactionId ? { ...tx, xrplTxHash } : tx
      );
      setTransactions(updated);
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error("XRPL 해시 업데이트 실패:", error);
      throw error;
    }
  };

  const deleteTransaction = async (transactionId: string) => {
    try {
      const updated = transactions.filter((tx) => tx.id !== transactionId);
      setTransactions(updated);
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error("거래 내역 삭제 실패:", error);
      throw error;
    }
  };

  const getTransactionsByType = (type: "receipt" | "menu" | "dutch_pay") => {
    return transactions.filter((tx) => tx.type === type);
  };

  const getTransactionById = (id: string) => {
    return transactions.find((tx) => tx.id === id);
  };

  const clearAllTransactions = async () => {
    try {
      setTransactions([]);
      await AsyncStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error("거래 내역 초기화 실패:", error);
      throw error;
    }
  };

  return {
    transactions,
    isLoading,
    saveTransaction,
    updateTransactionXRPL,
    deleteTransaction,
    getTransactionsByType,
    getTransactionById,
    clearAllTransactions,
  };
}
