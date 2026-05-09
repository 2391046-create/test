import { FlatList, Text, View } from 'react-native';

<<<<<<< HEAD
import { CategoryTotalsSection } from '@/components/category-totals-section';
import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useSettings } from '@/hooks/useSettings';
import { convertToKrw } from '@/lib/finance';
import { useFinance } from '@/lib/finance-context';
import { COUNTRY_CONFIGS } from '@/types';

export default function ReportScreen() {
  const { settings } = useSettings();
  const isEn = settings.language === 'en';
  const { transactions } = useFinance();
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth();
  const currentMonthTransactions = transactions.filter((item) => {
    const parsed = new Date(item.date);
    if (Number.isNaN(parsed.getTime())) return false;
    return parsed.getFullYear() === currentYear && parsed.getMonth() === currentMonth;
  });
  const total = currentMonthTransactions.reduce((sum, item) => sum + convertToKrw(item.amount, item.currency), 0);
  const verified = currentMonthTransactions.filter((item) => item.confidence >= 0.9).length;
  const locale = isEn ? 'en-US' : 'ko-KR';
  const targetRate = settings.selectedCurrency === 'KRW' ? 1 : (COUNTRY_CONFIGS[settings.selectedCurrency]?.exchangeRate ?? 1);
  const totalInSelectedCurrency = total / targetRate;
  const monthLabel = isEn
    ? `Submission summary for ${now.toLocaleString('en-US', { month: 'long', year: 'numeric' })}`
    : `${currentYear}년 ${currentMonth + 1}월 제출용 요약`;
=======
import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { convertToKrw, summarizeByCategory } from '@/lib/finance';
import { useFinance } from '@/lib/finance-context';

export default function ReportScreen() {
  const { transactions } = useFinance();
  const rows = summarizeByCategory(transactions);
  const total = transactions.reduce((sum, item) => sum + convertToKrw(item.amount, item.currency), 0);
  const verified = transactions.filter((item) => item.confidence >= 0.9).length;
>>>>>>> main

  return (
    <ScreenContainer className="px-5 pt-2">
      <FlatList
<<<<<<< HEAD
        data={[{ key: 'category-totals' }]}
        keyExtractor={(item) => item.key}
=======
        data={rows}
        keyExtractor={(item) => item.category.id}
>>>>>>> main
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <View className="gap-4 pb-4">
            <View>
<<<<<<< HEAD
              <Text className="text-3xl font-bold text-foreground leading-10">{isEn ? 'Evidence Report' : '증빙 리포트'}</Text>
              <Text className="text-sm text-muted leading-5">
                {isEn
                  ? 'Prepares categorized expense summaries for scholarships, visa submissions, and parent reporting.'
                  : '장학금, 비자, 부모님 보고에 필요한 지출 요약을 카테고리별로 준비합니다.'}
              </Text>
=======
              <Text className="text-3xl font-bold text-foreground leading-10">증빙 리포트</Text>
              <Text className="text-sm text-muted leading-5">장학금, 비자, 부모님 보고에 필요한 지출 요약을 카테고리별로 준비합니다.</Text>
>>>>>>> main
            </View>

            <View className="rounded-[28px] bg-surface border border-border p-5 gap-4">
              <View className="flex-row items-center justify-between">
<<<<<<< HEAD
                <Text className="text-sm font-semibold text-muted">{monthLabel}</Text>
                <IconSymbol name="checkmark.seal.fill" color="#16A34A" size={28} />
              </View>
              <Text className="text-4xl font-bold text-foreground leading-[46px]">
                {Math.round(totalInSelectedCurrency).toLocaleString(locale)} {settings.selectedCurrency}
              </Text>
              <Text className="text-sm text-muted leading-5">
                {isEn
                  ? `${verified} of ${currentMonthTransactions.length} transactions were classified with high confidence this month. Each transaction includes hash-style trace data for verification.`
                  : `이번 달 거래 총 ${currentMonthTransactions.length}건 중 ${verified}건이 높은 신뢰도로 분류되었습니다. 각 거래에는 검증용 해시 형식의 추적 정보가 포함됩니다.`}
              </Text>
            </View>

            <View className="rounded-3xl bg-blue-50 border border-blue-100 p-4">
              <Text className="text-base font-bold text-blue-900">{isEn ? 'Submission readiness' : '제출 준비 상태'}</Text>
              <Text className="mt-2 text-sm text-blue-800 leading-5">
                {isEn
                  ? 'This draft report reduces manual prep by showing category totals, period, and transaction hashes together. Real on-chain proof can be linked in a future XRPL wallet integration step.'
                  : '카테고리 합계, 기간, 거래 해시를 함께 보여주어 수작업 정리 시간을 줄이는 리포트 초안입니다. 실제 온체인 증빙은 향후 XRPL 지갑 연동 단계에서 연결할 수 있습니다.'}
              </Text>
            </View>
          </View>
        }
        renderItem={() => <CategoryTotalsSection transactions={currentMonthTransactions} isEn={isEn} currency={settings.selectedCurrency} />}
        ListFooterComponent={
          <View className="rounded-3xl bg-surface border border-border p-4 mb-8">
            <Text className="text-base font-bold text-foreground">{isEn ? 'Verification QR mock' : '검증 QR 모형'}</Text>
            <View className="mt-3 h-28 w-28 self-center rounded-2xl bg-background border border-border items-center justify-center">
              <Text className="text-center text-xs text-muted leading-4">XRPL\nProof\nQR</Text>
            </View>
            <Text className="mt-3 text-xs text-muted text-center leading-4">
              {isEn
                ? 'Current version is for report UX demo. Real QR verification will be enabled when connected to on-chain storage features.'
                : '현재 버전은 리포트 UX 시연용이며, 실제 QR 검증은 온체인 저장 기능과 연결될 때 활성화됩니다.'}
            </Text>
=======
                <Text className="text-sm font-semibold text-muted">2026년 5월 제출용 요약</Text>
                <IconSymbol name="checkmark.seal.fill" color="#16A34A" size={28} />
              </View>
              <Text className="text-4xl font-bold text-foreground leading-[46px]">₩{Math.round(total).toLocaleString('ko-KR')}</Text>
              <Text className="text-sm text-muted leading-5">총 {transactions.length}건 중 {verified}건이 높은 신뢰도로 분류되었습니다. 각 거래에는 검증용 해시 형식의 추적 정보가 포함됩니다.</Text>
            </View>

            <View className="rounded-3xl bg-blue-50 border border-blue-100 p-4">
              <Text className="text-base font-bold text-blue-900">제출 준비 상태</Text>
              <Text className="mt-2 text-sm text-blue-800 leading-5">카테고리 합계, 기간, 거래 해시를 함께 보여주어 수작업 정리 시간을 줄이는 리포트 초안입니다. 실제 온체인 증빙은 향후 XRPL 지갑 연동 단계에서 연결할 수 있습니다.</Text>
            </View>

            <Text className="text-lg font-bold text-foreground">카테고리별 합계</Text>
          </View>
        }
        renderItem={({ item }) => {
          const percent = total > 0 ? Math.round((item.amount / total) * 100) : 0;
          return (
            <View className="mb-3 rounded-2xl bg-surface border border-border p-4">
              <View className="flex-row items-center justify-between">
                <View className="flex-row items-center gap-3">
                  <View style={{ backgroundColor: item.category.tone }} className="h-4 w-4 rounded-full" />
                  <View>
                    <Text className="text-base font-bold text-foreground">{item.category.label}</Text>
                    <Text className="text-xs text-muted">{item.count}건 · 전체 {percent}%</Text>
                  </View>
                </View>
                <Text className="text-base font-bold text-foreground">₩{Math.round(item.amount).toLocaleString('ko-KR')}</Text>
              </View>
              <View className="mt-3 h-2 overflow-hidden rounded-full bg-background">
                <View style={{ width: `${Math.min(percent, 100)}%`, backgroundColor: item.category.tone }} className="h-2 rounded-full" />
              </View>
            </View>
          );
        }}
        ListFooterComponent={
          <View className="rounded-3xl bg-surface border border-border p-4 mb-8">
            <Text className="text-base font-bold text-foreground">검증 QR 모형</Text>
            <View className="mt-3 h-28 w-28 self-center rounded-2xl bg-background border border-border items-center justify-center">
              <Text className="text-center text-xs text-muted leading-4">XRPL\nProof\nQR</Text>
            </View>
            <Text className="mt-3 text-xs text-muted text-center leading-4">현재 버전은 리포트 UX 시연용이며, 실제 QR 검증은 온체인 저장 기능과 연결될 때 활성화됩니다.</Text>
>>>>>>> main
          </View>
        }
      />
    </ScreenContainer>
  );
}
