import { FlatList, Text, TouchableOpacity, View } from 'react-native';
import { Link } from 'expo-router';

import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { analyzeExchangeTiming, convertToKrw, exchangeSeries, getCategory, summarizeByCategory } from '@/lib/finance';
import { useFinance } from '@/lib/finance-context';

export default function HomeScreen() {
  const { transactions } = useFinance();
  const recommendation = analyzeExchangeTiming(exchangeSeries, 1000);
  const monthlySpend = transactions.reduce((sum, item) => sum + convertToKrw(item.amount, item.currency), 0);
  const topCategories = summarizeByCategory(transactions).slice(0, 3);

  return (
    <ScreenContainer className="px-5 pt-2">
      <FlatList
        data={transactions.slice(0, 4)}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <View className="gap-5 pb-4">
            <View className="gap-1">
              <Text className="text-3xl font-bold text-foreground leading-10">유학생 금융 나침반</Text>
              <Text className="text-sm text-muted leading-5">결제 알림을 정리하고 환율 타이밍을 한 화면에서 확인하세요.</Text>
            </View>

            <View className="rounded-[28px] bg-primary p-5 gap-4">
              <View className="flex-row items-center justify-between">
                <Text className="text-white/80 text-sm font-semibold">이번 달 추정 지출</Text>
                <IconSymbol name="wallet.pass.fill" color="#FFFFFF" size={26} />
              </View>
              <Text className="text-white text-4xl font-bold leading-[46px]">₩{Math.round(monthlySpend).toLocaleString('ko-KR')}</Text>
              <Text className="text-white/80 text-sm leading-5">{transactions.length}건의 거래가 자동 분류되었습니다. 장학금·비자 제출용 리포트에 바로 반영됩니다.</Text>
            </View>

            <View className="flex-row gap-3">
              <Link href="/records" asChild>
                <TouchableOpacity className="flex-1 rounded-3xl bg-surface border border-border p-4 active:opacity-80">
                  <IconSymbol name="bell.badge.fill" color="#2563EB" size={26} />
                  <Text className="mt-3 text-base font-bold text-foreground">알림 인식</Text>
                  <Text className="mt-1 text-xs text-muted leading-4">결제 문구 붙여넣기</Text>
                </TouchableOpacity>
              </Link>
              <Link href="/report" asChild>
                <TouchableOpacity className="flex-1 rounded-3xl bg-surface border border-border p-4 active:opacity-80">
                  <IconSymbol name="doc.text.fill" color="#16A34A" size={26} />
                  <Text className="mt-3 text-base font-bold text-foreground">증빙 준비</Text>
                  <Text className="mt-1 text-xs text-muted leading-4">카테고리별 자동 합계</Text>
                </TouchableOpacity>
              </Link>
            </View>

            <Link href="/rates" asChild>
              <TouchableOpacity className="rounded-3xl bg-surface border border-border p-5 active:opacity-80">
                <View className="flex-row items-center justify-between">
                  <View className="flex-1 pr-4">
                    <Text className="text-sm font-semibold text-muted">AI 환율 타이밍</Text>
                    <Text className="mt-1 text-2xl font-bold text-foreground leading-8">{recommendation.title}</Text>
                    <Text className="mt-2 text-sm text-muted leading-5">{recommendation.headline}</Text>
                  </View>
                  <View className="h-14 w-14 rounded-full bg-blue-100 items-center justify-center">
                    <IconSymbol name="paperplane.fill" color="#2563EB" size={28} />
                  </View>
                </View>
              </TouchableOpacity>
            </Link>

            <View className="rounded-3xl bg-surface border border-border p-5">
              <Text className="text-lg font-bold text-foreground">주요 지출 카테고리</Text>
              <View className="mt-4 gap-3">
                {topCategories.map((row) => (
                  <View key={row.category.id} className="flex-row items-center justify-between">
                    <View className="flex-row items-center gap-3">
                      <View style={{ backgroundColor: row.category.tone }} className="h-3 w-3 rounded-full" />
                      <Text className="text-sm font-semibold text-foreground">{row.category.label}</Text>
                    </View>
                    <Text className="text-sm text-muted">₩{Math.round(row.amount).toLocaleString('ko-KR')}</Text>
                  </View>
                ))}
              </View>
            </View>

            <Text className="text-lg font-bold text-foreground">최근 거래</Text>
          </View>
        }
        renderItem={({ item }) => {
          const category = getCategory(item.category);
          return (
            <View className="mb-3 rounded-2xl bg-surface border border-border p-4 flex-row items-center justify-between">
              <View className="flex-1 pr-3">
                <Text className="text-base font-bold text-foreground" numberOfLines={1}>{item.merchant}</Text>
                <Text className="mt-1 text-xs text-muted">{category.label} · 신뢰도 {Math.round(item.confidence * 100)}%</Text>
              </View>
              <Text className="text-base font-bold text-foreground">{item.currency} {item.amount.toLocaleString()}</Text>
            </View>
          );
        }}
        ListFooterComponent={<View className="h-8" />}
      />
    </ScreenContainer>
  );
}
