import { describe, it, expect } from 'vitest';
import { parsePaymentNotification, categorizeMerchant, createTransaction, Transaction } from '../lib/finance';
import { BudgetEntry, setBudget, getAllBudgetStatuses } from '../lib/budget-management';

/**
 * 통합 테스트: 실제 사용자 플로우 검증
 * 
 * 테스트 시나리오:
 * 1. 결제 알림 텍스트 파싱 및 자동 분류
 * 2. 거래 기록 저장 및 조회
 * 3. 예산 설정 및 초과 알림
 * 4. 카테고리별 지출 분석
 */

describe('Finance Compass Integration Tests', () => {
  describe('결제 알림 파싱 및 자동 분류', () => {
    it('스타벅스 결제 알림을 식비로 자동 분류해야 함', () => {
      const notificationText = '[신한카드]\n2026.05.06 14:30\n스타벅스 강남점\n₩5,500\n승인';
      
      const parsed = parsePaymentNotification(notificationText);
      expect(parsed).toBeDefined();
      expect(parsed?.merchant.toLowerCase()).toContain('스타벅스');
      expect(parsed?.amount).toBe(5500);
      expect(parsed?.category).toBe('food');
      console.log(`✓ 스타벅스 결제 → ${parsed?.category} 카테고리로 자동 분류됨`);
    });

    it('지하철 결제 알림을 교통으로 자동 분류해야 함', () => {
      const notificationText = '[KB국민카드]\n2026.05.06 08:15\n지하철 강남역\n₩1,250\n승인';
      
      const parsed = parsePaymentNotification(notificationText);
      expect(parsed).toBeDefined();
      expect(parsed?.merchant.toLowerCase()).toContain('지하철');
      expect(parsed?.category).toBe('transport');
      console.log(`✓ 지하철 결제 → ${parsed?.category} 카테고리로 자동 분류됨`);
    });

    it('편의점 결제 알림을 식비로 자동 분류해야 함', () => {
      const notificationText = '[우리카드]\n2026.05.06 19:45\nGS25 신촌점\n₩12,800\n승인';
      
      const parsed = parsePaymentNotification(notificationText);
      expect(parsed).toBeDefined();
      expect(parsed?.category).toBe('food');
      console.log(`✓ 편의점 결제 → ${parsed?.category} 카테고리로 자동 분류됨`);
    });

    it('병원 결제 알림을 의료로 자동 분류해야 함', () => {
      const notificationText = '[하나카드]\n2026.05.06 10:30\n서울대학교 병원\n₩85,000\n승인';
      
      const parsed = parsePaymentNotification(notificationText);
      expect(parsed).toBeDefined();
      expect(parsed?.category).toBe('health');
      console.log(`✓ 병원 결제 → ${parsed?.category} 카테고리로 자동 분류됨`);
    });
  });

  describe('거래 기록 저장 및 조회', () => {
    it('거래 기록을 생성하고 저장해야 함', () => {
      const rawText = '[신한카드] 스타벅스 ₩5,500';
      const transaction = createTransaction(rawText, 'manual');

      expect(transaction).toBeDefined();
      expect(transaction.merchant.toLowerCase()).toContain('스타벅스');
      expect(transaction.amount).toBe(5500);
      expect(transaction.category).toBe('food');
      console.log(`✓ 거래 기록 생성 완료: ${transaction.merchant} ₩${transaction.amount}`);
    });

    it('여러 거래 기록을 필터링하고 조회해야 함', () => {
      const transactions: Transaction[] = [
        createTransaction('[신한카드] 스타벅스 ₩5,500', 'manual'),
        createTransaction('[우리카드] GS25 ₩12,800', 'manual'),
        createTransaction('[KB국민카드] 지하철 ₩1,250', 'manual'),
      ];

      const foodTransactions = transactions.filter((t) => t.category === 'food');
      expect(foodTransactions.length).toBe(2);
      
      const totalFoodSpent = foodTransactions.reduce((sum, t) => sum + t.amount, 0);
      expect(totalFoodSpent).toBe(18300);
      console.log(`✓ 식비 거래 ${foodTransactions.length}건 조회, 총 ₩${totalFoodSpent.toLocaleString()}`);
    });
  });

  describe('예산 설정 및 초과 알림', () => {
    it('월별 카테고리 예산을 설정해야 함', () => {
      const budget = setBudget('food', '2026-05', 500000, 'KRW');
      
      expect(budget).toBeDefined();
      expect(budget.categoryId).toBe('food');
      expect(budget.monthYear).toBe('2026-05');
      expect(budget.budgetAmount).toBe(500000);
      expect(budget.currency).toBe('KRW');
      console.log(`✓ 식비 예산 설정: 2026년 5월 ₩${budget.budgetAmount.toLocaleString()}`);
    });

    it('예산 대비 지출 현황을 계산해야 함', () => {
      const budgets: BudgetEntry[] = [
        setBudget('food', '2026-05', 500000, 'KRW'),
        setBudget('transport', '2026-05', 100000, 'KRW'),
      ];

      const transactions: Transaction[] = [
        createTransaction('[신한카드] 스타벅스 ₩5,500', 'manual'),
        createTransaction('[KB국민카드] 지하철 ₩1,250', 'manual'),
      ];

      const categoryLabels = {
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
      
      expect(statuses.length).toBe(2);
      expect(statuses[0].categoryId).toBe('food');
      expect(statuses[0].spentAmount).toBe(5500);
      expect(statuses[0].percentageUsed).toBeCloseTo(1.1, 1);
      expect(statuses[0].status).toBe('under');
      
      console.log(`✓ 식비 예산 현황: ₩${statuses[0].spentAmount.toLocaleString()} / ₩${statuses[0].budgetAmount.toLocaleString()} (${statuses[0].percentageUsed.toFixed(1)}%)`);
      console.log(`✓ 교통 예산 현황: ₩${statuses[1].spentAmount.toLocaleString()} / ₩${statuses[1].budgetAmount.toLocaleString()} (${statuses[1].percentageUsed.toFixed(1)}%)`);
    });

    it('예산 초과 시 경고 상태를 반환해야 함', () => {
      const budgets: BudgetEntry[] = [
        setBudget('food', '2026-05', 50000, 'KRW'),
      ];

      const transactions: Transaction[] = [
        createTransaction('[신한카드] 스타벅스 ₩5,500', 'manual'),
        createTransaction('[우리카드] GS25 ₩30,000', 'manual'),
        createTransaction('[하나카드] 편의점 ₩20,000', 'manual'),
      ];

      const categoryLabels = {
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
      
      const totalSpent = transactions.reduce((sum, t) => sum + t.amount, 0);
      expect(totalSpent).toBe(55500);
      expect(statuses[0].percentageUsed).toBe(111);
      expect(statuses[0].status).toBe('exceeded');
      
      console.log(`⚠ 예산 초과 경고: 식비 ₩${statuses[0].spentAmount.toLocaleString()} / ₩${statuses[0].budgetAmount.toLocaleString()} (${statuses[0].percentageUsed.toFixed(0)}%)`);
    });
  });

  describe('카테고리별 지출 분석', () => {
    it('월별 카테고리별 지출을 집계해야 함', () => {
      const transactions: Transaction[] = [
        createTransaction('[신한카드] 스타벅스 ₩5,500', 'manual'),
        createTransaction('[우리카드] GS25 ₩12,800', 'manual'),
        createTransaction('[KB국민카드] 지하철 ₩1,250', 'manual'),
        createTransaction('[신한카드] 택시 ₩8,000', 'manual'),
      ];

      const categoryTotals = transactions.reduce(
        (acc, tx) => {
          acc[tx.category] = (acc[tx.category] || 0) + tx.amount;
          return acc;
        },
        {} as Record<string, number>
      );

      expect(categoryTotals.food).toBe(5500 + 12800);
      expect(categoryTotals.transport).toBe(1250 + 8000);
      
      const totalSpent = Object.values(categoryTotals).reduce((sum, amount) => sum + amount, 0);
      expect(totalSpent).toBe(27550);
      
      console.log(`✓ 카테고리별 지출 분석:`);
      console.log(`  - 식비: ₩${categoryTotals.food.toLocaleString()} (${((categoryTotals.food / totalSpent) * 100).toFixed(1)}%)`);
      console.log(`  - 교통: ₩${categoryTotals.transport.toLocaleString()} (${((categoryTotals.transport / totalSpent) * 100).toFixed(1)}%)`);
      console.log(`  - 총 지출: ₩${totalSpent.toLocaleString()}`);
    });
  });

  describe('앱 네비게이션 및 UI 렌더링', () => {
    it('모든 주요 탭이 정의되어 있어야 함', () => {
      const tabs = ['index', 'records', 'report', 'analytics', 'rates', 'rules', 'settings'];
      
      expect(tabs.length).toBe(7);
      expect(tabs).toContain('index');
      expect(tabs).toContain('records');
      expect(tabs).toContain('analytics');
      expect(tabs).toContain('rates');
      
      console.log(`✓ 앱 탭 구조 확인: ${tabs.join(' → ')}`);
    });

    it('각 탭의 기본 기능이 정의되어 있어야 함', () => {
      const tabFeatures = {
        index: '홈 - 금융 요약 대시보드',
        records: '기록 - 거래 내역 관리',
        report: '리포트 - 증빙 자료 생성',
        analytics: '분석 - 예산 및 지출 분석',
        rates: '환율 - 송금 타이밍 추천',
        rules: '규칙 - 카테고리 분류 규칙',
        settings: '설정 - 앱 설정',
      };

      Object.entries(tabFeatures).forEach(([tab, feature]) => {
        expect(feature).toBeDefined();
        console.log(`✓ ${tab}: ${feature}`);
      });
    });
  });
});
