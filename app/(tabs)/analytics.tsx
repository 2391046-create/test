import { ScrollView, Text, View, Pressable, Modal, TextInput } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useFinance } from '@/lib/finance-context';
import { useBudget } from '@/lib/budget-context';
import { useState } from 'react';
import { categories } from '@/lib/finance';
import { useColors } from '@/hooks/use-colors';

/**
 * 분석 및 예산 관리 화면
 * - 월별/카테고리별 지출 트렌드
 * - 예산 설정 및 초과 알림
 * - 지출 목표 달성도
 * - 예산 효율성 점수
 */

export default function AnalyticsScreen() {
  const colors = useColors();
  const { transactions } = useFinance();
  const { budgets, goals, addBudget, addGoal, getBudgetStatuses, getBudgetAlerts, getEfficiencyScore } = useBudget();

  const [activeTab, setActiveTab] = useState<'budget' | 'trends' | 'goals'>('budget');
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('food');
  const [budgetAmount, setBudgetAmount] = useState('');
  const [goalAmount, setGoalAmount] = useState('');
  const [goalType, setGoalType] = useState<'reduction' | 'limit'>('limit');

  const budgetStatuses = getBudgetStatuses(transactions);
  const budgetAlerts = getBudgetAlerts(transactions);
  const efficiencyScore = getEfficiencyScore(transactions);

  const handleAddBudget = () => {
    if (budgetAmount && selectedCategory) {
      const today = new Date();
      const monthYear = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
      addBudget(selectedCategory as any, monthYear, parseFloat(budgetAmount));
      setBudgetAmount('');
      setShowBudgetModal(false);
    }
  };

  const handleAddGoal = () => {
    if (goalAmount && selectedCategory) {
      const targetDate = new Date();
      targetDate.setMonth(targetDate.getMonth() + 1);
      addGoal(selectedCategory as any, goalType, parseFloat(goalAmount), targetDate.toISOString().slice(0, 10));
      setGoalAmount('');
      setShowGoalModal(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'under':
        return '#16A34A';
      case 'warning':
        return '#F59E0B';
      case 'exceeded':
        return '#DC2626';
      default:
        return '#64748B';
    }
  };

  const getCategoryLabel = (categoryId: string) => {
    const category = categories.find((c) => c.id === categoryId);
    return category?.label || categoryId;
  };

  return (
    <ScreenContainer className="flex-1 bg-background">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} className="flex-1">
        <View className="p-4 gap-4">
          {/* 헤더 */}
          <View className="gap-2">
            <Text className="text-3xl font-bold text-foreground">분석</Text>
            <Text className="text-sm text-muted">예산 및 지출 목표 관리</Text>
          </View>

          {/* 효율성 점수 카드 */}
          <View className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-6 gap-2">
            <Text className="text-sm text-white opacity-90">예산 효율성 점수</Text>
            <View className="flex-row items-center gap-3">
              <Text className="text-5xl font-bold text-white">{efficiencyScore}</Text>
              <Text className="text-sm text-white opacity-80">/100</Text>
            </View>
            <Text className="text-xs text-white opacity-75">
              {efficiencyScore >= 80 ? '✓ 예산을 잘 지키고 있습니다' : efficiencyScore >= 60 ? '⚠ 예산 관리 개선이 필요합니다' : '✗ 예산 초과가 많습니다'}
            </Text>
          </View>

          {/* 탭 네비게이션 */}
          <View className="flex-row gap-2 bg-surface rounded-lg p-1">
            {['budget', 'trends', 'goals'].map((tab) => (
              <Pressable
                key={tab}
                onPress={() => setActiveTab(tab as any)}
                className={`flex-1 py-2 px-3 rounded-md ${activeTab === tab ? 'bg-primary' : 'bg-transparent'}`}
              >
                <Text className={`text-center text-sm font-semibold ${activeTab === tab ? 'text-white' : 'text-muted'}`}>
                  {tab === 'budget' ? '예산' : tab === 'trends' ? '트렌드' : '목표'}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* 예산 탭 */}
          {activeTab === 'budget' && (
            <View className="gap-3">
              {/* 예산 알림 */}
              {budgetAlerts.length > 0 && (
                <View className="gap-2">
                  <Text className="text-sm font-semibold text-foreground">⚠ 예산 알림</Text>
                  {budgetAlerts.map((alert, idx) => (
                    <View
                      key={idx}
                      className="bg-red-50 border border-red-200 rounded-lg p-3 gap-1"
                      style={{ borderLeftColor: alert.severity === 'critical' ? '#DC2626' : '#F59E0B', borderLeftWidth: 4 }}
                    >
                      <Text className="font-semibold text-red-900">{alert.categoryLabel}</Text>
                      <Text className="text-xs text-red-800">{alert.message}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* 예산 현황 */}
              <View className="gap-2">
                <View className="flex-row justify-between items-center">
                  <Text className="text-sm font-semibold text-foreground">월별 예산 현황</Text>
                  <Pressable
                    onPress={() => setShowBudgetModal(true)}
                    className="bg-primary px-3 py-1 rounded-full"
                  >
                    <Text className="text-white text-xs font-semibold">+ 예산 추가</Text>
                  </Pressable>
                </View>

                {budgetStatuses.length === 0 ? (
                  <View className="bg-surface rounded-lg p-4 items-center gap-2">
                    <Text className="text-muted text-sm">설정된 예산이 없습니다</Text>
                    <Pressable
                      onPress={() => setShowBudgetModal(true)}
                      className="bg-primary px-4 py-2 rounded-lg"
                    >
                      <Text className="text-white text-sm font-semibold">예산 설정하기</Text>
                    </Pressable>
                  </View>
                ) : (
                  budgetStatuses.map((status) => (
                    <View key={status.categoryId} className="bg-surface rounded-lg p-3 gap-2">
                      <View className="flex-row justify-between items-center">
                        <Text className="font-semibold text-foreground">{status.categoryLabel}</Text>
                        <View className="flex-row gap-1 items-center">
                          <Text className="text-xs font-semibold" style={{ color: getStatusColor(status.status) }}>
                            {status.percentageUsed.toFixed(0)}%
                          </Text>
                          <View
                            className="w-6 h-6 rounded-full items-center justify-center"
                            style={{ backgroundColor: getStatusColor(status.status) + '20' }}
                          >
                            <View
                              className="w-4 h-4 rounded-full"
                              style={{ backgroundColor: getStatusColor(status.status) }}
                            />
                          </View>
                        </View>
                      </View>

                      {/* 진행률 바 */}
                      <View className="bg-gray-200 rounded-full h-2 overflow-hidden">
                        <View
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(status.percentageUsed, 100)}%`,
                            backgroundColor: getStatusColor(status.status),
                          }}
                        />
                      </View>

                      <View className="flex-row justify-between">
                        <Text className="text-xs text-muted">
                          ₩{status.spentAmount.toLocaleString()} / ₩{status.budgetAmount.toLocaleString()}
                        </Text>
                        <Text className="text-xs font-semibold text-foreground">
                          남은 금액: ₩{status.remainingAmount.toLocaleString()}
                        </Text>
                      </View>
                    </View>
                  ))
                )}
              </View>
            </View>
          )}

          {/* 트렌드 탭 */}
          {activeTab === 'trends' && (
            <View className="gap-3">
              <Text className="text-sm font-semibold text-foreground">카테고리별 월간 지출</Text>
              <View className="bg-surface rounded-lg p-4">
                <Text className="text-center text-muted text-sm">
                  📊 트렌드 차트는 실제 거래 데이터를 기반으로 표시됩니다
                </Text>
              </View>

              {/* 카테고리별 요약 */}
              <View className="gap-2">
                {categories.filter((c) => c.id !== 'other').map((category) => {
                  const categoryTransactions = transactions.filter((tx) => tx.category === category.id);
                  const totalSpent = categoryTransactions.reduce((sum, tx) => sum + tx.amount, 0);
                  const count = categoryTransactions.length;

                  return (
                    <View key={category.id} className="bg-surface rounded-lg p-3 flex-row justify-between items-center">
                      <View className="flex-1 gap-1">
                        <Text className="font-semibold text-foreground">{category.label}</Text>
                        <Text className="text-xs text-muted">{count}건의 거래</Text>
                      </View>
                      <Text className="font-bold text-foreground">₩{totalSpent.toLocaleString()}</Text>
                    </View>
                  );
                })}
              </View>
            </View>
          )}

          {/* 목표 탭 */}
          {activeTab === 'goals' && (
            <View className="gap-3">
              <View className="flex-row justify-between items-center">
                <Text className="text-sm font-semibold text-foreground">지출 목표</Text>
                <Pressable
                  onPress={() => setShowGoalModal(true)}
                  className="bg-primary px-3 py-1 rounded-full"
                >
                  <Text className="text-white text-xs font-semibold">+ 목표 추가</Text>
                </Pressable>
              </View>

              {goals.length === 0 ? (
                <View className="bg-surface rounded-lg p-4 items-center gap-2">
                  <Text className="text-muted text-sm">설정된 목표가 없습니다</Text>
                  <Pressable
                    onPress={() => setShowGoalModal(true)}
                    className="bg-primary px-4 py-2 rounded-lg"
                  >
                    <Text className="text-white text-sm font-semibold">목표 설정하기</Text>
                  </Pressable>
                </View>
              ) : (
                goals.map((goal) => (
                  <View key={goal.id} className="bg-surface rounded-lg p-3 gap-2">
                    <View className="flex-row justify-between items-center">
                      <Text className="font-semibold text-foreground">{getCategoryLabel(goal.categoryId)}</Text>
                      <Text className="text-xs font-semibold text-primary">{goal.progressPercentage.toFixed(0)}%</Text>
                    </View>

                    <View className="bg-gray-200 rounded-full h-2 overflow-hidden">
                      <View
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${Math.min(goal.progressPercentage, 100)}%` }}
                      />
                    </View>

                    <View className="flex-row justify-between">
                      <Text className="text-xs text-muted">
                        {goal.goalType === 'reduction' ? '감소 목표' : '한도 설정'}
                      </Text>
                      <Text className="text-xs font-semibold text-foreground">
                        {goal.status === 'completed' ? '✓ 달성' : goal.status === 'failed' ? '✗ 실패' : '진행 중'}
                      </Text>
                    </View>
                  </View>
                ))
              )}
            </View>
          )}
        </View>
      </ScrollView>

      {/* 예산 추가 모달 */}
      <Modal visible={showBudgetModal} transparent animationType="slide">
        <View className="flex-1 bg-black/50 justify-end">
          <View className="bg-background rounded-t-2xl p-6 gap-4">
            <Text className="text-lg font-bold text-foreground">예산 추가</Text>

            {/* 카테고리 선택 */}
            <View className="gap-2">
              <Text className="text-sm font-semibold text-foreground">카테고리</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} className="gap-2">
                {categories.filter((c) => c.id !== 'other').map((category) => (
                  <Pressable
                    key={category.id}
                    onPress={() => setSelectedCategory(category.id)}
                    className={`px-4 py-2 rounded-full ${selectedCategory === category.id ? 'bg-primary' : 'bg-surface'}`}
                  >
                    <Text className={`text-sm font-semibold ${selectedCategory === category.id ? 'text-white' : 'text-foreground'}`}>
                      {category.label}
                    </Text>
                  </Pressable>
                ))}
              </ScrollView>
            </View>

            {/* 예산 금액 입력 */}
            <View className="gap-2">
              <Text className="text-sm font-semibold text-foreground">월 예산 (₩)</Text>
              <TextInput
                placeholder="예: 500000"
                value={budgetAmount}
                onChangeText={setBudgetAmount}
                keyboardType="number-pad"
                className="bg-surface border border-border rounded-lg px-4 py-3 text-foreground"
              />
            </View>

            {/* 버튼 */}
            <View className="flex-row gap-2">
              <Pressable
                onPress={() => setShowBudgetModal(false)}
                className="flex-1 bg-surface rounded-lg py-3"
              >
                <Text className="text-center font-semibold text-foreground">취소</Text>
              </Pressable>
              <Pressable
                onPress={handleAddBudget}
                className="flex-1 bg-primary rounded-lg py-3"
              >
                <Text className="text-center font-semibold text-white">추가</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      {/* 목표 추가 모달 */}
      <Modal visible={showGoalModal} transparent animationType="slide">
        <View className="flex-1 bg-black/50 justify-end">
          <View className="bg-background rounded-t-2xl p-6 gap-4">
            <Text className="text-lg font-bold text-foreground">목표 설정</Text>

            {/* 목표 유형 선택 */}
            <View className="gap-2">
              <Text className="text-sm font-semibold text-foreground">목표 유형</Text>
              <View className="flex-row gap-2">
                {['limit', 'reduction'].map((type) => (
                  <Pressable
                    key={type}
                    onPress={() => setGoalType(type as any)}
                    className={`flex-1 px-4 py-2 rounded-lg ${goalType === type ? 'bg-primary' : 'bg-surface'}`}
                  >
                    <Text className={`text-center text-sm font-semibold ${goalType === type ? 'text-white' : 'text-foreground'}`}>
                      {type === 'limit' ? '한도 설정' : '감소 목표'}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </View>

            {/* 카테고리 선택 */}
            <View className="gap-2">
              <Text className="text-sm font-semibold text-foreground">카테고리</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} className="gap-2">
                {categories.filter((c) => c.id !== 'other').map((category) => (
                  <Pressable
                    key={category.id}
                    onPress={() => setSelectedCategory(category.id)}
                    className={`px-4 py-2 rounded-full ${selectedCategory === category.id ? 'bg-primary' : 'bg-surface'}`}
                  >
                    <Text className={`text-sm font-semibold ${selectedCategory === category.id ? 'text-white' : 'text-foreground'}`}>
                      {category.label}
                    </Text>
                  </Pressable>
                ))}
              </ScrollView>
            </View>

            {/* 목표 금액 입력 */}
            <View className="gap-2">
              <Text className="text-sm font-semibold text-foreground">목표 금액 (₩)</Text>
              <TextInput
                placeholder="예: 300000"
                value={goalAmount}
                onChangeText={setGoalAmount}
                keyboardType="number-pad"
                className="bg-surface border border-border rounded-lg px-4 py-3 text-foreground"
              />
            </View>

            {/* 버튼 */}
            <View className="flex-row gap-2">
              <Pressable
                onPress={() => setShowGoalModal(false)}
                className="flex-1 bg-surface rounded-lg py-3"
              >
                <Text className="text-center font-semibold text-foreground">취소</Text>
              </Pressable>
              <Pressable
                onPress={handleAddGoal}
                className="flex-1 bg-primary rounded-lg py-3"
              >
                <Text className="text-center font-semibold text-white">설정</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </ScreenContainer>
  );
}
