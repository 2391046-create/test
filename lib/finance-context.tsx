import { ReactNode, createContext, useContext, useMemo, useState } from 'react';

import { CategoryId, Transaction, createTransaction, sampleTransactions, CategorizationRule } from '@/lib/finance';
import { useRules } from '@/lib/rules-context';

type FinanceContextValue = {
  transactions: Transaction[];
  addNotification: (text: string) => Transaction;
  updateCategory: (id: string, category: CategoryId) => void;
};

const FinanceContext = createContext<FinanceContextValue | null>(null);

export function FinanceProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<Transaction[]>(sampleTransactions);
  const { rules } = useRules();

  const value = useMemo<FinanceContextValue>(() => ({
    transactions,
    addNotification: (text: string) => {
      // 사용자 정의 규칙을 적용하여 거래 생성
      const transaction = createTransaction(text, 'notification', new Date().toISOString().slice(0, 10), rules);
      setTransactions((current) => [transaction, ...current]);
      return transaction;
    },
    updateCategory: (id: string, category: CategoryId) => {
      setTransactions((current) => current.map((item) => item.id === id ? { ...item, category, confidence: 1 } : item));
    },
  }), [transactions, rules]);

  return <FinanceContext.Provider value={value}>{children}</FinanceContext.Provider>;
}

export function useFinance() {
  const context = useContext(FinanceContext);
  if (!context) {
    throw new Error('useFinance must be used within FinanceProvider');
  }
  return context;
}
