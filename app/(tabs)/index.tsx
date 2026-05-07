import { ScrollView, Text, View, TouchableOpacity, Pressable, FlatList } from 'react-native';
import { router } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';

import { ScreenContainer } from '@/components/screen-container';
import { useFinance } from '@/lib/finance-context';
import { useRules } from '@/lib/rules-context';
import { categories, summarizeByCategory, Transaction } from '@/lib/finance';
import { setupNotificationListener, requestNotificationPermissions } from '@/lib/notification-handler';

export default function HomeScreen() {
  const { transactions, addNotification } = useFinance();
  const { rules } = useRules();
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState(summarizeByCategory(transactions));
  const [notificationPermission, setNotificationPermission] = useState(false);

  // 알림 권한 요청 및 리스너 설정
  useEffect(() => {
    const initNotifications = async () => {
      const granted = await requestNotificationPermissions();
      setNotificationPermission(granted);

      if (granted) {
        const unsubscribe = setupNotificationListener(
          (transaction) => {
            addNotification(transaction.rawText);
          },
          rules
        );
        return unsubscribe;
      }
    };

    initNotifications();
  }, [rules, addNotification]);

  // 최근 거래 업데이트
  useEffect(() => {
    setRecentTransactions(transactions.slice(0, 5));
    setSummary(summarizeByCategory(transactions));
  }, [transactions]);

  const totalAmount = summary.reduce((sum, item) => sum + item.amount, 0);
  const topCategory = summary.length > 0 ? summary.reduce((max, item) => (item.amount > max.amount ? item : max)) : null;

  const handleAddNotification = useCallback(() => {
    router.push('/(tabs)/records');
  }, []);

  const handleViewRules = useCallback(() => {
    router.push('/(tabs)/rules');
  }, []);

  const handleScanReceipt = useCallback(() => {
    router.push('/(tabs)/receipt-scanner');
  }, []);

  const handleAnalyzePrice = useCallback(() => {
    router.push('/(tabs)/menu-scanner');
  }, []);

  const handleDutchPay = useCallback(() => {
    router.push('/(tabs)/dutch-pay');
  }, []);

  return (
    <ScreenContainer className="px-5 pt-4">
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 80 }}>
        {/* 헤더 */}
        <View className="mb-6">
          <Text className="text-3xl font-bold text-foreground leading-10">Finance Compass</Text>
          <Text className="text-sm text-muted mt-1">유학생 금융 관리, 투명하고 편리하게</Text>
        </View>

        {/* 주요 통계 카드 */}
        <View className="mb-6 gap-3">
          {/* 총 지출 */}
          <View className="rounded-3xl bg-gradient-to-br from-primary to-primary/80 p-6 shadow-lg">
            <Text className="text-sm text-white/80 font-medium mb-1">총 지출</Text>
            <Text className="text-4xl font-bold text-white">{totalAmount.toLocaleString('ko-KR')}</Text>
            <Text className="text-xs text-white/70 mt-2">₩ KRW 기준</Text>
          </View>

          {/* 상위 카테고리 */}
          {topCategory && (
            <View className="rounded-3xl bg-surface border border-border p-6">
              <View className="flex-row items-center justify-between">
                <View className="flex-1">
                  <Text className="text-sm text-muted font-medium mb-1">가장 많은 지출</Text>
                  <Text className="text-2xl font-bold text-foreground">{topCategory.category.label}</Text>
                  <Text className="text-xs text-muted mt-1">{topCategory.count}건 · {topCategory.amount.toLocaleString('ko-KR')}원</Text>
                </View>
                <View className="w-12 h-12 rounded-2xl items-center justify-center" style={{ backgroundColor: topCategory.category.tone + '20' }}>
                  <Text className="text-2xl">{getCategoryEmoji(topCategory.category.id)}</Text>
                </View>
              </View>
            </View>
          )}
        </View>

        {/* 빠른 작업 버튼 */}
        <View className="mb-6 gap-2">
          <TouchableOpacity onPress={handleScanReceipt} className="rounded-2xl bg-primary/10 border border-primary/30 py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">📄</Text>
              <View>
                <Text className="text-sm font-bold text-primary">영수증 스캔</Text>
                <Text className="text-xs text-muted">다국 영수증 자동 분석</Text>
              </View>
            </View>
            <Text className="text-primary text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleAnalyzePrice} className="rounded-2xl bg-primary/10 border border-primary/30 py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">🍽️</Text>
              <View>
                <Text className="text-sm font-bold text-primary">가격 분석</Text>
                <Text className="text-xs text-muted">메뉴판 스캔 및 평균가 비교</Text>
              </View>
            </View>
            <Text className="text-primary text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleDutchPay} className="rounded-2xl bg-primary/10 border border-primary/30 py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">👥</Text>
              <View>
                <Text className="text-sm font-bold text-primary">더치페이</Text>
                <Text className="text-xs text-muted">자동 정산 계산</Text>
              </View>
            </View>
            <Text className="text-primary text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleAddNotification} className="rounded-2xl bg-surface border border-border py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">📝</Text>
              <View>
                <Text className="text-sm font-bold text-foreground">거래 추가</Text>
                <Text className="text-xs text-muted">알림 텍스트 붙여넣기</Text>
              </View>
            </View>
            <Text className="text-muted text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleViewRules} className="rounded-2xl bg-surface border border-border py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">⚙️</Text>
              <View>
                <Text className="text-sm font-bold text-foreground">분류 규칙</Text>
                <Text className="text-xs text-muted">자동 분류 커스터마이징</Text>
              </View>
            </View>
            <Text className="text-muted text-lg">→</Text>
          </TouchableOpacity>
        </View>

        {/* 카테고리별 지출 현황 */}
        <View className="mb-6">
          <Text className="text-lg font-bold text-foreground mb-3">카테고리별 지출</Text>
          <FlatList
            data={summary}
            keyExtractor={(item) => item.category.id}
            scrollEnabled={false}
            renderItem={({ item }) => {
              const percentage = totalAmount > 0 ? (item.amount / totalAmount) * 100 : 0;
              return (
                <View className="mb-3 gap-2">
                  <View className="flex-row items-center justify-between">
                    <View className="flex-row items-center gap-2 flex-1">
                      <Text className="text-lg">{getCategoryEmoji(item.category.id)}</Text>
                      <Text className="text-sm font-medium text-foreground flex-1">{item.category.label}</Text>
                    </View>
                    <Text className="text-sm font-bold text-foreground">{item.amount.toLocaleString('ko-KR')}원</Text>
                  </View>
                  <View className="h-2 bg-border rounded-full overflow-hidden">
                    <View className="h-full rounded-full" style={{ width: `${percentage}%`, backgroundColor: item.category.tone }} />
                  </View>
                </View>
              );
            }}
          />
        </View>

        {/* 최근 거래 */}
        <View>
          <View className="flex-row items-center justify-between mb-3">
            <Text className="text-lg font-bold text-foreground">최근 거래</Text>
            <Pressable onPress={() => router.push('/(tabs)/records')} style={({ pressed }) => [{ opacity: pressed ? 0.6 : 1 }]}>
              <Text className="text-sm text-primary font-semibold">모두 보기 →</Text>
            </Pressable>
          </View>
          <FlatList
            data={recentTransactions}
            keyExtractor={(item) => item.id}
            scrollEnabled={false}
            renderItem={({ item }) => {
              const category = categories.find((c) => c.id === item.category);
              return (
                <Pressable
                  onPress={() => router.push(`/(tabs)/records?id=${item.id}`)}
                  style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                  className="mb-2 rounded-2xl bg-surface border border-border p-4 flex-row items-center justify-between"
                >
                  <View className="flex-row items-center gap-3 flex-1">
                    <View className="w-12 h-12 rounded-2xl items-center justify-center" style={{ backgroundColor: category?.tone + '20' }}>
                      <Text className="text-xl">{getCategoryEmoji(item.category)}</Text>
                    </View>
                    <View className="flex-1">
                      <Text className="text-sm font-semibold text-foreground">{item.merchant}</Text>
                      <Text className="text-xs text-muted">{item.date}</Text>
                    </View>
                  </View>
                  <Text className="text-sm font-bold text-foreground">{item.amount} {item.currency}</Text>
                </Pressable>
              );
            }}
          />
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

function getCategoryEmoji(categoryId: string): string {
  const emojiMap: Record<string, string> = {
    food: '🍽️',
    transport: '🚗',
    housing: '🏠',
    study: '📚',
    shopping: '🛍️',
    health: '🏥',
    transfer: '💸',
    other: '📌',
  };
  return emojiMap[categoryId] || '📌';
}
