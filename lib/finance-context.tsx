import { ReactNode, createContext, useContext, useMemo, useState } from 'react';

import { CategoryId, Transaction, createTransaction, sampleTransactions } from '@/lib/finance';

type FinanceContextValue = {
  transactions: Transaction[];
  addNotification: (text: string) => Transaction;
  updateCategory: (id: string, category: CategoryId) => void;
};

const FinanceContext = createContext<FinanceContextValue | null>(null);

export function FinanceProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<Transaction[]>(sampleTransactions);

  const value = useMemo<FinanceContextValue>(() => ({
    transactions,
    addNotification: (text: string) => {
      const transaction = createTransaction(text, 'notification');
      setTransactions((current) => [transaction, ...current]);
      return transaction;
    },
    updateCategory: (id: string, category: CategoryId) => {
      setTransactions((current) => current.map((item) => item.id === id ? { ...item, category, confidence: 1 } : item));
    },
  }), [transactions]);

  return <FinanceContext.Provider value={value}>{children}</FinanceContext.Provider>;
}

export function useFinance() {
  const context = useContext(FinanceContext);
  if (!context) {
    throw new Error('useFinance must be used within FinanceProvider');
  }
  return context;
}
