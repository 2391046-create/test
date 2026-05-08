import { ScrollView, Text, View, TouchableOpacity, Pressable, FlatList } from 'react-native';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ScreenContainer } from '@/components/screen-container';
import { useFinance } from '@/lib/finance-context';
import { useRules } from '@/lib/rules-context';
import { categories, Transaction } from '@/lib/finance';
import { setupNotificationListener, requestNotificationPermissions } from '@/lib/notification-handler';
import { useSettings } from '@/hooks/useSettings';
import { COUNTRY_CONFIGS } from '@/types';

export default function HomeScreen() {
  const { transactions, addNotification } = useFinance();
  const { rules } = useRules();
  const { settings } = useSettings();
  const isEn = settings.language === 'en';
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [notificationPermission, setNotificationPermission] = useState(false);

  const exchangeRatesByCurrency = useMemo(
    () => ({
      KRW: 1,
      ...Object.fromEntries(Object.entries(COUNTRY_CONFIGS).map(([currency, config]) => [currency, config.exchangeRate])),
    }),
    [],
  );

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
  }, [transactions]);

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

  const convertAmount = useCallback(
    (amount: number, fromCurrency: string, toCurrency: string) => {
      const fromRate = exchangeRatesByCurrency[fromCurrency as keyof typeof exchangeRatesByCurrency] ?? 1300;
      const toRate = exchangeRatesByCurrency[toCurrency as keyof typeof exchangeRatesByCurrency] ?? 1300;
      const amountInKrw = amount * fromRate;
      return amountInKrw / toRate;
    },
    [exchangeRatesByCurrency],
  );

  const formatCurrencyAmount = useCallback((amount: number, currency: string) => {
    const useFraction = !['KRW', 'JPY'].includes(currency);
    return amount.toLocaleString('en-US', {
      minimumFractionDigits: useFraction ? 2 : 0,
      maximumFractionDigits: useFraction ? 2 : 0,
    });
  }, []);

  const getCategoryLabel = useCallback(
    (id: string, fallback: string) => {
      if (!isEn) return fallback;
      const map: Record<string, string> = {
        food: 'Food',
        transport: 'Transport',
        housing: 'Housing',
        study: 'Study',
        shopping: 'Shopping',
        health: 'Health',
        transfer: 'Transfer',
        other: 'Other',
      };
      return map[id] ?? fallback;
    },
    [isEn],
  );

  const summary = useMemo(
    () =>
      categories
        .map((category) => {
          const items = transactions.filter((tx) => {
            if (tx.category !== category.id) return false;
            const parsed = new Date(tx.date);
            if (Number.isNaN(parsed.getTime())) return false;
            const now = new Date();
            return parsed.getFullYear() === now.getFullYear() && parsed.getMonth() === now.getMonth();
          });
          const amount = items.reduce(
            (sum, tx) => sum + convertAmount(tx.amount, tx.currency, settings.selectedCurrency),
            0,
          );
          return { category, amount, count: items.length };
        })
        .filter((row) => row.count > 0),
    [transactions, convertAmount, settings.selectedCurrency],
  );

  const totalAmount = summary.reduce((sum, item) => sum + item.amount, 0);
  const topCategory = summary.length > 0 ? summary.reduce((max, item) => (item.amount > max.amount ? item : max)) : null;

  return (
    <ScreenContainer className="px-5 pt-4">
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 80 }}>
        {/* 헤더 */}
        <View className="mb-6">
          <Text className="text-3xl font-bold text-foreground leading-10">Finance Compass</Text>
          <Text className="text-sm text-muted mt-1">{isEn ? 'Student finance, transparent and simple' : '유학생 금융 관리, 투명하고 편리하게'}</Text>
        </View>

        {/* 주요 통계 카드 */}
        <View className="mb-6 gap-3">
          {/* 총 지출 */}
          <View className="rounded-3xl bg-gradient-to-br from-primary to-primary/80 p-6 shadow-lg">
            <Text className="text-sm text-white/80 font-medium mb-1">{isEn ? 'Total Spending (This Month)' : '총 지출 (이번 달)'}</Text>
            <Text className="text-4xl font-bold text-white">
              {formatCurrencyAmount(totalAmount, settings.selectedCurrency)}
            </Text>
            <Text className="text-xs text-white/70 mt-2">{settings.selectedCurrency} {isEn ? 'base' : '기준'}</Text>
          </View>

          {/* 상위 카테고리 */}
          {topCategory && (
            <View className="rounded-3xl bg-surface border border-border p-6">
              <View className="flex-row items-center justify-between">
                <View className="flex-1">
                  <Text className="text-sm text-muted font-medium mb-1">{isEn ? 'Top Spending Category' : '가장 많은 지출'}</Text>
                  <Text className="text-2xl font-bold text-foreground">{getCategoryLabel(topCategory.category.id, topCategory.category.label)}</Text>
                  <Text className="text-xs text-muted mt-1">
                    {topCategory.count}{isEn ? ' tx' : '건'} · {formatCurrencyAmount(topCategory.amount, settings.selectedCurrency)} {settings.selectedCurrency}
                  </Text>
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
                <Text className="text-sm font-bold text-primary">{isEn ? 'Receipt Scan' : '영수증 스캔'}</Text>
                <Text className="text-xs text-muted">{isEn ? 'Auto analyze multilingual receipts' : '다국 영수증 자동 분석'}</Text>
              </View>
            </View>
            <Text className="text-primary text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleAnalyzePrice} className="rounded-2xl bg-primary/10 border border-primary/30 py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">🍽️</Text>
              <View>
                <Text className="text-sm font-bold text-primary">{isEn ? 'Price Analysis' : '가격 분석'}</Text>
                <Text className="text-xs text-muted">{isEn ? 'Scan menu and compare averages' : '메뉴판 스캔 및 평균가 비교'}</Text>
              </View>
            </View>
            <Text className="text-primary text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleDutchPay} className="rounded-2xl bg-primary/10 border border-primary/30 py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">👥</Text>
              <View>
                <Text className="text-sm font-bold text-primary">{isEn ? 'Split Bill' : '더치페이'}</Text>
                <Text className="text-xs text-muted">{isEn ? 'Automatic settlement' : '자동 정산 계산'}</Text>
              </View>
            </View>
            <Text className="text-primary text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleAddNotification} className="rounded-2xl bg-surface border border-border py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">📝</Text>
              <View>
                <Text className="text-sm font-bold text-foreground">{isEn ? 'Add Transaction' : '거래 추가'}</Text>
                <Text className="text-xs text-muted">{isEn ? 'Paste notification text' : '알림 텍스트 붙여넣기'}</Text>
              </View>
            </View>
            <Text className="text-muted text-lg">→</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={handleViewRules} className="rounded-2xl bg-surface border border-border py-4 px-4 flex-row items-center justify-between active:opacity-70">
            <View className="flex-row items-center gap-3">
              <Text className="text-2xl">⚙️</Text>
              <View>
                <Text className="text-sm font-bold text-foreground">{isEn ? 'Rules' : '분류 규칙'}</Text>
                <Text className="text-xs text-muted">{isEn ? 'Customize auto-categorization' : '자동 분류 커스터마이징'}</Text>
              </View>
            </View>
            <Text className="text-muted text-lg">→</Text>
          </TouchableOpacity>
        </View>

        {/* 카테고리별 지출 현황 */}
        <View className="mb-6">
          <Text className="text-lg font-bold text-foreground mb-3">{isEn ? 'Spending by Category' : '카테고리별 지출'}</Text>
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
                      <Text className="text-sm font-medium text-foreground flex-1">{getCategoryLabel(item.category.id, item.category.label)}</Text>
                    </View>
                    <Text className="text-sm font-bold text-foreground">
                      {formatCurrencyAmount(item.amount, settings.selectedCurrency)} {settings.selectedCurrency}
                    </Text>
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
            <Text className="text-lg font-bold text-foreground">{isEn ? 'Recent Transactions' : '최근 거래'}</Text>
            <Pressable onPress={() => router.push('/(tabs)/records')} style={({ pressed }) => [{ opacity: pressed ? 0.6 : 1 }]}>
              <Text className="text-sm text-primary font-semibold">{isEn ? 'View all →' : '모두 보기 →'}</Text>
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
                  <View className="items-end">
                    <Text className="text-sm font-bold text-foreground">
                      {formatCurrencyAmount(convertAmount(item.amount, item.currency, settings.selectedCurrency), settings.selectedCurrency)}
                    </Text>
                    <Text className="text-xs text-muted mt-1">{settings.selectedCurrency}</Text>
                  </View>
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
