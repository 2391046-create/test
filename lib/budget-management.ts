import { CategoryId, Transaction } from './finance';

/**
 * 예산 및 지출 목표 관리
 * 월별 카테고리별 예산 설정, 초과 알림, 목표 달성도 추적
 */

export type BudgetEntry = {
  id: string;
  categoryId: CategoryId;
  monthYear: string; // YYYY-MM
  budgetAmount: number;
  currency: string;
  createdAt: string;
  updatedAt: string;
};

export type SpendingGoal = {
  id: string;
  categoryId: CategoryId;
  goalType: 'reduction' | 'limit'; // 감소 목표 또는 한도 설정
  targetAmount: number;
  currentAmount: number;
  targetDate: string; // YYYY-MM-DD
  progressPercentage: number;
  status: 'active' | 'completed' | 'failed';
  createdAt: string;
};

export type BudgetStatus = {
  categoryId: CategoryId;
  categoryLabel: string;
  budgetAmount: number;
  spentAmount: number;
  remainingAmount: number;
  percentageUsed: number;
  status: 'under' | 'warning' | 'exceeded'; // 정상, 경고(80% 이상), 초과
};

export type MonthlyTrend = {
  month: string; // YYYY-MM
  categoryId: CategoryId;
  totalSpent: number;
  transactionCount: number;
  averageTransaction: number;
};

/**
 * 예산 설정
 */
export function setBudget(
  categoryId: CategoryId,
  monthYear: string,
  budgetAmount: number,
  currency: string = 'KRW'
): BudgetEntry {
  return {
    id: `budget_${categoryId}_${monthYear}_${Date.now()}`,
    categoryId,
    monthYear,
    budgetAmount,
    currency,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

/**
 * 카테고리별 예산 상태 조회
 */
export function getBudgetStatus(
  budget: BudgetEntry,
  transactions: Transaction[],
  categoryLabel: string
): BudgetStatus {
  // 해당 월의 거래만 필터링
  const monthTransactions = transactions.filter((tx) => {
    const txMonth = tx.date.slice(0, 7); // YYYY-MM
    return tx.category === budget.categoryId && txMonth === budget.monthYear;
  });

  const spentAmount = monthTransactions.reduce((sum, tx) => sum + tx.amount, 0);
  const remainingAmount = budget.budgetAmount - spentAmount;
  const percentageUsed = (spentAmount / budget.budgetAmount) * 100;

  let status: 'under' | 'warning' | 'exceeded';
  if (percentageUsed > 100) {
    status = 'exceeded';
  } else if (percentageUsed >= 80) {
    status = 'warning';
  } else {
    status = 'under';
  }

  return {
    categoryId: budget.categoryId,
    categoryLabel,
    budgetAmount: budget.budgetAmount,
    spentAmount,
    remainingAmount: Math.max(remainingAmount, 0),
    percentageUsed: Math.min(percentageUsed, 100),
    status,
  };
}

/**
 * 모든 카테고리 예산 상태 조회
 */
export function getAllBudgetStatuses(
  budgets: BudgetEntry[],
  transactions: Transaction[],
  categoryLabels: Record<CategoryId, string>
): BudgetStatus[] {
  return budgets.map((budget) =>
    getBudgetStatus(budget, transactions, categoryLabels[budget.categoryId] || 'Unknown')
  );
}

/**
 * 예산 초과 알림 생성
 */
export function generateBudgetAlerts(budgetStatuses: BudgetStatus[]): Array<{
  categoryLabel: string;
  message: string;
  severity: 'warning' | 'critical';
  percentageUsed: number;
}> {
  return budgetStatuses
    .filter((status) => status.status !== 'under')
    .map((status) => ({
      categoryLabel: status.categoryLabel,
      message:
        status.status === 'exceeded'
          ? `${status.categoryLabel} 예산을 ${(status.percentageUsed - 100).toFixed(0)}% 초과했습니다.`
          : `${status.categoryLabel} 예산의 ${status.percentageUsed.toFixed(0)}%를 사용했습니다.`,
      severity: status.status === 'exceeded' ? 'critical' : 'warning',
      percentageUsed: status.percentageUsed,
    }));
}

/**
 * 지출 목표 생성
 */
export function createSpendingGoal(
  categoryId: CategoryId,
  goalType: 'reduction' | 'limit',
  targetAmount: number,
  targetDate: string
): SpendingGoal {
  return {
    id: `goal_${categoryId}_${Date.now()}`,
    categoryId,
    goalType,
    targetAmount,
    currentAmount: 0,
    targetDate,
    progressPercentage: 0,
    status: 'active',
    createdAt: new Date().toISOString(),
  };
}

/**
 * 지출 목표 진행률 업데이트
 */
export function updateGoalProgress(
  goal: SpendingGoal,
  transactions: Transaction[]
): SpendingGoal {
  const goalDate = new Date(goal.targetDate);
  const goalMonth = goal.targetDate.slice(0, 7);

  // 목표 기간 내의 거래 필터링
  const relevantTransactions = transactions.filter((tx) => {
    const txDate = new Date(tx.date);
    const txMonth = tx.date.slice(0, 7);

    if (goal.goalType === 'reduction') {
      // 감소 목표: 이전 월부터 목표 월까지
      return tx.category === goal.categoryId && txMonth <= goalMonth;
    } else {
      // 한도 목표: 목표 월만
      return tx.category === goal.categoryId && txMonth === goalMonth;
    }
  });

  const currentAmount = relevantTransactions.reduce((sum, tx) => sum + tx.amount, 0);
  const progressPercentage =
    goal.goalType === 'reduction'
      ? Math.max(0, ((goal.targetAmount - currentAmount) / goal.targetAmount) * 100)
      : (currentAmount / goal.targetAmount) * 100;

  const now = new Date();
  let status: 'active' | 'completed' | 'failed' = 'active';
  if (now > goalDate) {
    status = progressPercentage >= 100 ? 'completed' : 'failed';
  }

  return {
    ...goal,
    currentAmount,
    progressPercentage: Math.min(progressPercentage, 100),
    status,
  };
}

/**
 * 월별 지출 트렌드 계산
 */
export function calculateMonthlyTrends(
  transactions: Transaction[],
  categoryId?: CategoryId
): MonthlyTrend[] {
  const trends = new Map<string, MonthlyTrend>();

  transactions.forEach((tx) => {
    if (categoryId && tx.category !== categoryId) return;

    const month = tx.date.slice(0, 7);
    const key = `${month}_${tx.category}`;

    if (!trends.has(key)) {
      trends.set(key, {
        month,
        categoryId: tx.category,
        totalSpent: 0,
        transactionCount: 0,
        averageTransaction: 0,
      });
    }

    const trend = trends.get(key)!;
    trend.totalSpent += tx.amount;
    trend.transactionCount += 1;
    trend.averageTransaction = trend.totalSpent / trend.transactionCount;
  });

  return Array.from(trends.values()).sort((a, b) => a.month.localeCompare(b.month));
}

/**
 * 카테고리별 월별 비교 데이터
 */
export function getCategoryMonthlyComparison(
  transactions: Transaction[],
  categoryId: CategoryId,
  months: number = 6
): Array<{
  month: string;
  amount: number;
  count: number;
}> {
  const today = new Date();
  const monthData: Record<string, { amount: number; count: number }> = {};

  // 최근 N개월 초기화
  for (let i = months - 1; i >= 0; i--) {
    const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
    const monthStr = date.toISOString().slice(0, 7);
    monthData[monthStr] = { amount: 0, count: 0 };
  }

  // 거래 데이터 집계
  transactions.forEach((tx) => {
    if (tx.category !== categoryId) return;
    const month = tx.date.slice(0, 7);
    if (month in monthData) {
      monthData[month].amount += tx.amount;
      monthData[month].count += 1;
    }
  });

  return Object.entries(monthData).map(([month, data]) => ({
    month,
    amount: data.amount,
    count: data.count,
  }));
}

/**
 * 예산 대비 실제 지출 비교
 */
export function compareBudgetVsActual(
  budgets: BudgetEntry[],
  transactions: Transaction[],
  monthYear: string
): Array<{
  categoryId: CategoryId;
  categoryLabel: string;
  budgeted: number;
  actual: number;
  variance: number; // 음수면 초과, 양수면 절감
  variancePercentage: number;
}> {
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

  const monthBudgets = budgets.filter((b) => b.monthYear === monthYear);
  const monthTransactions = transactions.filter((tx) => tx.date.slice(0, 7) === monthYear);

  const comparison = monthBudgets.map((budget) => {
    const actual = monthTransactions
      .filter((tx) => tx.category === budget.categoryId)
      .reduce((sum, tx) => sum + tx.amount, 0);

    const variance = budget.budgetAmount - actual;
    const variancePercentage = (variance / budget.budgetAmount) * 100;

    return {
      categoryId: budget.categoryId,
      categoryLabel: categoryLabels[budget.categoryId] || 'Unknown',
      budgeted: budget.budgetAmount,
      actual,
      variance,
      variancePercentage,
    };
  });

  return comparison.sort((a, b) => a.variance - b.variance);
}

/**
 * 예산 효율성 점수 (0-100)
 * 100에 가까울수록 예산을 잘 지킴
 */
export function calculateBudgetEfficiencyScore(budgetStatuses: BudgetStatus[]): number {
  if (budgetStatuses.length === 0) return 0;

  const scores = budgetStatuses.map((status) => {
    if (status.status === 'under') {
      return 100 - status.percentageUsed * 0.5; // 50% 사용했으면 75점
    } else if (status.status === 'warning') {
      return 100 - (status.percentageUsed - 80) * 2; // 80% 이상이면 감점 가중
    } else {
      return Math.max(0, 100 - (status.percentageUsed - 100) * 2); // 초과분 가중 감점
    }
  });

  return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
}
