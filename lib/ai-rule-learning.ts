import { CategorizationRule, CategoryId } from './finance';

/**
 * AI 기반 규칙 자동 학습
 * 사용자가 카테고리를 수정할 때마다 패턴을 학습하여 새 규칙을 자동 추천
 */

export type LearningEntry = {
  merchantName: string;
  originalCategory: CategoryId;
  correctedCategory: CategoryId;
  timestamp: number;
  confidence: number; // 학습 신뢰도 (0-1)
};

export type RuleRecommendation = {
  rule: CategorizationRule;
  confidence: number; // 추천 신뢰도 (0-1)
  supportingExamples: LearningEntry[];
  reason: string;
};

/**
 * 사용자 수정 내역 기록
 */
export function recordCategoryCorrection(
  merchantName: string,
  originalCategory: CategoryId,
  correctedCategory: CategoryId
): LearningEntry {
  return {
    merchantName,
    originalCategory,
    correctedCategory,
    timestamp: Date.now(),
    confidence: 0.9, // 사용자 직접 수정이므로 높은 신뢰도
  };
}

/**
 * 학습 데이터로부터 새 규칙 추천
 * 패턴 분석을 통해 자동으로 적용할 규칙 생성
 */
export function recommendRulesFromLearning(learningEntries: LearningEntry[]): RuleRecommendation[] {
  if (learningEntries.length === 0) {
    return [];
  }

  // 상인명별로 수정 내역 그룹화
  const merchantPatterns = new Map<string, LearningEntry[]>();
  learningEntries.forEach((entry) => {
    const key = entry.merchantName.toLowerCase();
    if (!merchantPatterns.has(key)) {
      merchantPatterns.set(key, []);
    }
    merchantPatterns.get(key)!.push(entry);
  });

  const recommendations: RuleRecommendation[] = [];

  // 각 상인명에 대해 규칙 생성
  merchantPatterns.forEach((entries, merchantName) => {
    // 가장 많이 수정된 카테고리 찾기
    const categoryCount = new Map<CategoryId, number>();
    entries.forEach((entry) => {
      const count = categoryCount.get(entry.correctedCategory) || 0;
      categoryCount.set(entry.correctedCategory, count + 1);
    });

    const [mostCommonCategory, count] = Array.from(categoryCount.entries()).reduce((a, b) =>
      b[1] > a[1] ? b : a
    );

    // 신뢰도 계산 (일관성 기반)
    const consistency = count / entries.length;
    const avgConfidence = entries.reduce((sum, e) => sum + e.confidence, 0) / entries.length;
    const overallConfidence = Math.min(consistency * avgConfidence, 0.95);

    // 규칙 생성
    if (overallConfidence > 0.6) {
      const rule: CategorizationRule = {
        id: `learned_${merchantName}_${Date.now()}`,
        name: `자동학습: ${merchantName}`,
        category: mostCommonCategory,
        matchType: 'keyword',
        pattern: merchantName,
        enabled: true,
        priority: Math.round(overallConfidence * 10), // 1-10 범위
        createdAt: new Date().toISOString(),
      };

      recommendations.push({
        rule,
        confidence: overallConfidence,
        supportingExamples: entries,
        reason: `${merchantName}은(는) ${count}회 ${getCategoryLabel(mostCommonCategory)}로 분류되었습니다.`,
      });
    }
  });

  // 신뢰도 기준 정렬
  return recommendations.sort((a, b) => b.confidence - a.confidence);
}

/**
 * 키워드 기반 규칙 추천
 * 여러 상인명에서 공통 키워드 추출
 */
export function recommendKeywordRules(learningEntries: LearningEntry[]): RuleRecommendation[] {
  if (learningEntries.length < 3) {
    return [];
  }

  // 카테고리별 상인명 그룹화
  const categoryMerchants = new Map<CategoryId, string[]>();
  learningEntries.forEach((entry) => {
    if (!categoryMerchants.has(entry.correctedCategory)) {
      categoryMerchants.set(entry.correctedCategory, []);
    }
    categoryMerchants.get(entry.correctedCategory)!.push(entry.merchantName);
  });

  const recommendations: RuleRecommendation[] = [];

  categoryMerchants.forEach((merchants, category) => {
    if (merchants.length >= 2) {
      // 공통 키워드 추출
      const keywords = extractCommonKeywords(merchants);

      if (keywords.length > 0) {
        const rule: CategorizationRule = {
          id: `keyword_${category}_${Date.now()}`,
          name: `자동학습: ${keywords.join(' 또는 ')}`,
          category,
          matchType: 'keyword',
          pattern: keywords.join('|'),
          enabled: false, // 사용자 승인 필요
          priority: Math.min(merchants.length, 8),
          createdAt: new Date().toISOString(),
        };

        const supportingExamples = learningEntries.filter((e) => e.correctedCategory === category);
        recommendations.push({
          rule,
          confidence: Math.min(merchants.length / 10, 0.8),
          supportingExamples,
          reason: `${keywords.join(', ')} 키워드는 ${merchants.length}개 상인에서 ${getCategoryLabel(category)}로 분류되었습니다.`,
        });
      }
    }
  });

  return recommendations;
}

/**
 * 공통 키워드 추출
 */
function extractCommonKeywords(merchants: string[]): string[] {
  if (merchants.length === 0) return [];

  const words = merchants.map((m) => m.toLowerCase().split(/\s+/));
  const commonWords = words[0].filter((word) =>
    words.every((w) => w.some((word2) => word2.includes(word) || word.includes(word2)))
  );

  // 너무 짧은 단어 제외
  return commonWords.filter((w) => w.length > 3).slice(0, 3);
}

/**
 * 카테고리 라벨 조회
 */
function getCategoryLabel(categoryId: CategoryId): string {
  const labels: Record<CategoryId, string> = {
    food: '식비',
    transport: '교통',
    housing: '주거',
    study: '학비',
    shopping: '쇼핑',
    health: '건강',
    transfer: '송금',
    other: '기타',
  };
  return labels[categoryId] || '기타';
}

/**
 * 학습 데이터 저장 및 관리
 */
export class RuleLearningManager {
  private learningEntries: LearningEntry[] = [];
  private maxEntries = 1000;

  addEntry(entry: LearningEntry): void {
    this.learningEntries.push(entry);
    // 최대 개수 초과 시 오래된 항목 제거
    if (this.learningEntries.length > this.maxEntries) {
      this.learningEntries = this.learningEntries.slice(-this.maxEntries);
    }
  }

  getRecommendations(): RuleRecommendation[] {
    const merchantRules = recommendRulesFromLearning(this.learningEntries);
    const keywordRules = recommendKeywordRules(this.learningEntries);
    return [...merchantRules, ...keywordRules].sort((a, b) => b.confidence - a.confidence);
  }

  getEntries(): LearningEntry[] {
    return [...this.learningEntries];
  }

  clearEntries(): void {
    this.learningEntries = [];
  }

  getStatistics() {
    return {
      totalEntries: this.learningEntries.length,
      uniqueMerchants: new Set(this.learningEntries.map((e) => e.merchantName)).size,
      averageConfidence:
        this.learningEntries.reduce((sum, e) => sum + e.confidence, 0) / Math.max(this.learningEntries.length, 1),
    };
  }
}
