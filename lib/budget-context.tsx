import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  BudgetEntry,
  SpendingGoal,
  setBudget,
  createSpendingGoal,
  updateGoalProgress,
  getBudgetStatus,
  getAllBudgetStatuses,
  generateBudgetAlerts,
  calculateMonthlyTrends,
  calculateBudgetEfficiencyScore,
} from './budget-management';
import { CategoryId, Transaction } from './finance';

interface BudgetContextType {
  budgets: BudgetEntry[];
  goals: SpendingGoal[];
  addBudget: (categoryId: CategoryId, monthYear: string, amount: number, currency?: string) => void;
  updateBudget: (budgetId: string, amount: number) => void;
  deleteBudget: (budgetId: string) => void;
  addGoal: (categoryId: CategoryId, goalType: 'reduction' | 'limit', targetAmount: number, targetDate: string) => void;
  deleteGoal: (goalId: string) => void;
  getBudgetStatuses: (transactions: Transaction[]) => any[];
  getBudgetAlerts: (transactions: Transaction[]) => any[];
  getEfficiencyScore: (transactions: Transaction[]) => number;
  getMonthlyTrends: (categoryId?: CategoryId) => any[];
}

const BudgetContext = createContext<BudgetContextType | undefined>(undefined);

export function BudgetProvider({ children }: { children: React.ReactNode }) {
  const [budgets, setBudgets] = useState<BudgetEntry[]>([]);
  const [goals, setGoals] = useState<SpendingGoal[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 저장된 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      try {
        const [budgetsData, goalsData] = await Promise.all([
          AsyncStorage.getItem('budgets'),
          AsyncStorage.getItem('goals'),
        ]);

        if (budgetsData) setBudgets(JSON.parse(budgetsData));
        if (goalsData) setGoals(JSON.parse(goalsData));
      } catch (error) {
        console.error('Failed to load budget data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // 데이터 저장
  const saveBudgets = async (newBudgets: BudgetEntry[]) => {
    try {
      await AsyncStorage.setItem('budgets', JSON.stringify(newBudgets));
      setBudgets(newBudgets);
    } catch (error) {
      console.error('Failed to save budgets:', error);
    }
  };

  const saveGoals = async (newGoals: SpendingGoal[]) => {
    try {
      await AsyncStorage.setItem('goals', JSON.stringify(newGoals));
      setGoals(newGoals);
    } catch (error) {
      console.error('Failed to save goals:', error);
    }
  };

  const addBudget = (categoryId: CategoryId, monthYear: string, amount: number, currency = 'KRW') => {
    const newBudget = setBudget(categoryId, monthYear, amount, currency);
    saveBudgets([...budgets, newBudget]);
  };

  const updateBudget = (budgetId: string, amount: number) => {
    const updated = budgets.map((b) => (b.id === budgetId ? { ...b, budgetAmount: amount, updatedAt: new Date().toISOString() } : b));
    saveBudgets(updated);
  };

  const deleteBudget = (budgetId: string) => {
    saveBudgets(budgets.filter((b) => b.id !== budgetId));
  };

  const addGoal = (categoryId: CategoryId, goalType: 'reduction' | 'limit', targetAmount: number, targetDate: string) => {
    const newGoal = createSpendingGoal(categoryId, goalType, targetAmount, targetDate);
    saveGoals([...goals, newGoal]);
  };

  const deleteGoal = (goalId: string) => {
    saveGoals(goals.filter((g) => g.id !== goalId));
  };

  const getBudgetStatuses = (transactions: Transaction[]) => {
    const categoryLabels: Record<CategoryId, string> = {
      food: '식비',
      transport: '교통',
      housing: '주거',
      study: '학업',
      shopping: '쇼핑',
      health: '의료',
      transfer: '송금',
      other: '기타',
    };

    return getAllBudgetStatuses(budgets, transactions, categoryLabels);
  };

  const getBudgetAlerts = (transactions: Transaction[]) => {
    const categoryLabels: Record<CategoryId, string> = {
      food: '식비',
      transport: '교통',
      housing: '주거',
      study: '학업',
      shopping: '쇼핑',
      health: '의료',
      transfer: '송금',
      other: '기타',
    };

    const statuses = getAllBudgetStatuses(budgets, transactions, categoryLabels);
    return generateBudgetAlerts(statuses);
  };

  const getEfficiencyScore = (transactions: Transaction[]) => {
    const categoryLabels: Record<CategoryId, string> = {
      food: '식비',
      transport: '교통',
      housing: '주거',
      study: '학업',
      shopping: '쇼핑',
      health: '의료',
      transfer: '송금',
      other: '기타',
    };

    const statuses = getAllBudgetStatuses(budgets, transactions, categoryLabels);
    return calculateBudgetEfficiencyScore(statuses);
  };

  const getMonthlyTrends = (categoryId?: CategoryId) => {
    // 실제 거래 데이터가 필요하므로, 이 함수는 트랜잭션을 받아야 함
    // 현재는 빈 배열 반환
    return [];
  };

  const value: BudgetContextType = {
    budgets,
    goals,
    addBudget,
    updateBudget,
    deleteBudget,
    addGoal,
    deleteGoal,
    getBudgetStatuses,
    getBudgetAlerts,
    getEfficiencyScore,
    getMonthlyTrends,
  };

  return <BudgetContext.Provider value={value}>{children}</BudgetContext.Provider>;
}

export function useBudget() {
  const context = useContext(BudgetContext);
  if (context === undefined) {
    throw new Error('useBudget must be used within a BudgetProvider');
  }
  return context;
}
