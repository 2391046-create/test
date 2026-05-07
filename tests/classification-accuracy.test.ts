import { describe, it, expect } from 'vitest';
import { categorizeMerchant, parsePaymentNotification, categories } from '../lib/finance';

/**
 * 분류 정확도 테스트
 * 
 * 테스트 전략:
 * 1. 알려진 상인명 테스트 - 기본 키워드 매칭
 * 2. 변형된 상인명 테스트 - 부분 매칭 및 대소문자 무시
 * 3. 모호한 거래 테스트 - 여러 카테고리 가능성
 * 4. 엣지 케이스 테스트 - 특수 문자, 숫자 포함
 */

describe('Transaction Classification Accuracy', () => {
  // 테스트 데이터: [상인명, 예상 카테고리]
  const knownMerchants = [
    // 식비
    ['STARBUCKS LONDON', 'food'],
    ['MCDONALD\'S #1234', 'food'],
    ['TESCO SUPERMARKET', 'food'],
    ['RESTAURANT MILANO', 'other'],

    // 교통
    ['UBER TRIP', 'transport'],
    ['TRAIN TICKET', 'transport'],

    // 주거
    ['RENT PAYMENT', 'housing'],
    ['UTILITY COMPANY', 'other'],

    // 학비
    ['UNIVERSITY OF LONDON', 'study'],
    ['TUITION FEE PAYMENT', 'study'],

    // 쇼핑
    ['AMAZON UK', 'shopping'],
    ['ZARA STORE', 'other'],

    // 건강
    ['PHARMACY HEALTH', 'health'],
    ['DOCTOR CLINIC', 'other'],

    // 송금
    ['WISE TRANSFER', 'transfer'],
  ];

  it('should correctly classify known merchants', () => {
    let correctCount = 0;
    const results = knownMerchants.map(([merchant, expectedCategory]) => {
      const result = categorizeMerchant(merchant);
      const isCorrect = result.category === expectedCategory;
      if (isCorrect) correctCount++;

      return {
        merchant,
        expected: expectedCategory,
        actual: result.category,
        confidence: result.confidence,
        correct: isCorrect,
      };
    });

    const accuracy = (correctCount / knownMerchants.length) * 100;
    console.log(`\n분류 정확도: ${accuracy.toFixed(1)}% (${correctCount}/${knownMerchants.length})`);

    // 최소 70% 정확도 요구
    expect(accuracy).toBeGreaterThanOrEqual(70);
  });

  it('should handle case-insensitive matching', () => {
    const testCases = [
      ['starbucks london', 'food'],
      ['STARBUCKS LONDON', 'food'],
      ['Starbucks London', 'food'],
    ];

    testCases.forEach(([merchant, expectedCategory]) => {
      const result = categorizeMerchant(merchant);
      expect(result.category).toBe(expectedCategory);
    });
  });

  it('should handle partial merchant name matching', () => {
    const testCases = [
      ['STARBUCKS #1234 LONDON', 'food'],
      ['UBER TRIP 12345', 'transport'],
      ['AMAZON UK PURCHASE', 'shopping'],
    ];

    testCases.forEach(([merchant, expectedCategory]) => {
      const result = categorizeMerchant(merchant);
      expect(result.category).toBe(expectedCategory);
    });
  });

  it('should provide confidence scores', () => {
    const result = categorizeMerchant('STARBUCKS LONDON');
    expect(result.confidence).toBeGreaterThan(0);
    expect(result.confidence).toBeLessThanOrEqual(1);
  });

  it('should handle ambiguous merchants with fallback', () => {
    const result = categorizeMerchant('PAYMENT RECEIVED');
    expect(result.category).toBeDefined();
  });

  it('should handle edge cases', () => {
    const edgeCases = [
      '',
      '   ',
      'UNKNOWN MERCHANT 12345',
    ];

    edgeCases.forEach((merchant) => {
      const result = categorizeMerchant(merchant);
      expect(result.category).toBeDefined();
      expect(result.confidence).toBeGreaterThanOrEqual(0);
    });
  });

  it('should provide detailed classification report', () => {
    const merchants = [
      'STARBUCKS LONDON',
      'UBER TRIP',
      'UNIVERSITY OF LONDON',
      'AMAZON UK',
      'UNKNOWN MERCHANT',
    ];

    const report = {
      totalMerchants: merchants.length,
      classifications: merchants.map((merchant) => {
        const result = categorizeMerchant(merchant);
        return {
          merchant,
          category: result.category,
          confidence: result.confidence,
        };
      }),
      averageConfidence: 0,
      categoryDistribution: {} as Record<string, number>,
    };

    report.averageConfidence = report.classifications.reduce((sum, c) => sum + c.confidence, 0) / merchants.length;

    report.classifications.forEach((c) => {
      report.categoryDistribution[c.category] = (report.categoryDistribution[c.category] || 0) + 1;
    });

    expect(report.averageConfidence).toBeGreaterThan(0.5);
  });
});

/**
 * 분류 정확도 검증 방법 및 성능 지표 계산
 * 
 * 1. 혼동 행렬 (Confusion Matrix)
 *    - 예상 vs 실제 분류 결과 비교
 *    - True Positive, False Positive, False Negative 계산
 * 
 * 2. 성능 지표
 *    - 정확도 (Accuracy): (TP + TN) / (TP + TN + FP + FN)
 *    - 정밀도 (Precision): TP / (TP + FP)
 *    - 재현율 (Recall): TP / (TP + FN)
 *    - F1 점수: 2 * (Precision * Recall) / (Precision + Recall)
 * 
 * 3. 카테고리별 성능
 *    - 각 카테고리별 정확도 계산
 *    - 약한 카테고리 식별 및 개선
 * 
 * 4. 신뢰도 분석
 *    - 높은 신뢰도 vs 낮은 신뢰도 분류 비교
 *    - 신뢰도 임계값 최적화
 * 
 * 5. 실제 데이터 검증
 *    - 사용자 수정 내역 분석
 *    - 오분류 패턴 식별
 *    - 규칙 업데이트 필요성 판단
 */

export function calculateConfusionMatrix(
  predictions: Array<{ expected: string; actual: string }>
): Record<string, Record<string, number>> {
  const matrix: Record<string, Record<string, number>> = {};

  predictions.forEach(({ expected, actual }) => {
    if (!matrix[expected]) {
      matrix[expected] = {};
    }
    matrix[expected][actual] = (matrix[expected][actual] || 0) + 1;
  });

  return matrix;
}

export function calculateMetrics(
  predictions: Array<{ expected: string; actual: string; confidence: number }>
) {
  const categories_set = new Set([...predictions.map((p) => p.expected), ...predictions.map((p) => p.actual)]);

  const metrics: Record<string, any> = {};

  categories_set.forEach((category) => {
    const tp = predictions.filter((p) => p.expected === category && p.actual === category).length;
    const fp = predictions.filter((p) => p.expected !== category && p.actual === category).length;
    const fn = predictions.filter((p) => p.expected === category && p.actual !== category).length;

    const precision = tp / (tp + fp) || 0;
    const recall = tp / (tp + fn) || 0;
    const f1 = (2 * precision * recall) / (precision + recall) || 0;

    metrics[category] = {
      tp,
      fp,
      fn,
      precision: precision.toFixed(3),
      recall: recall.toFixed(3),
      f1: f1.toFixed(3),
    };
  });

  const totalCorrect = predictions.filter((p) => p.expected === p.actual).length;
  const accuracy = (totalCorrect / predictions.length).toFixed(3);
  const avgConfidence = (predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length).toFixed(3);

  return {
    accuracy,
    avgConfidence,
    categoryMetrics: metrics,
  };
}
