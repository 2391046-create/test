import { useEffect, useMemo, useState } from 'react';
import { Text, TouchableOpacity, View } from 'react-native';

import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { ExchangePoint, analyzeExchangeTiming, exchangeSeries } from '@/lib/finance';
import { useSettings } from '@/hooks/useSettings';

type FrankfurterRate = {
  date: string;
  base: string;
  quote: string;
  rate: number;
};

function formatApiDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function formatChartDate(date: string) {
  const [, month, day] = date.split('-');
  return `${month}/${day}`;
}

export default function RatesScreen() {
  const { settings } = useSettings();
  const selectedCurrency = settings.selectedCurrency;
  const isEn = settings.language === 'en';
  const [series, setSeries] = useState<ExchangePoint[]>(exchangeSeries);
  const [sourceLabel, setSourceLabel] = useState(isEn ? 'Sample series' : '샘플 시계열');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (selectedCurrency === 'KRW') {
      setSeries(exchangeSeries);
      setSourceLabel(isEn ? 'Sample series for KRW mode' : 'KRW 선택 시 샘플 시계열');
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const to = new Date();
    const from = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000);

    setLoading(true);
    fetch(`https://api.frankfurter.dev/v2/rates?from=${formatApiDate(from)}&to=${formatApiDate(to)}&base=${selectedCurrency}&quotes=KRW`, {
      signal: controller.signal,
    })
      .then((response) => response.json())
      .then((data: FrankfurterRate[]) => {
        const nextSeries = data
          .filter((item) => Number.isFinite(item.rate))
          .slice(-7)
          .map((item) => ({ date: formatChartDate(item.date), rate: item.rate }));
        if (nextSeries.length >= 3) {
          setSeries(nextSeries);
          setSourceLabel(`Frankfurter API (${selectedCurrency}/KRW)`);
        }
      })
      .catch(() => {
        setSourceLabel(isEn ? 'Fallback series (network)' : '네트워크 fallback 시계열');
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, [selectedCurrency, isEn]);

  const recommendation = useMemo(() => analyzeExchangeTiming(series, 1000), [series]);
  const max = Math.max(...series.map((point) => point.rate));
  const min = Math.min(...series.map((point) => point.rate));
  const recommendationTitle = isEn
    ? recommendation.action === 'send_now'
      ? 'Send now'
      : `Wait ${recommendation.waitDays} days`
    : recommendation.title;
  const recommendationReason = isEn
    ? recommendation.action === 'send_now'
      ? 'Current rate trend is favorable compared to recent average.'
      : 'Short-term trend is not favorable enough yet. Monitor a little longer.'
    : recommendation.reason;

  return (
    <ScreenContainer className="px-5 pt-2">
      <View className="flex-1 gap-5">
        <View>
          <Text className="text-3xl font-bold text-foreground leading-10">{isEn ? 'Exchange Timing' : '환율 타이밍'}</Text>
          <Text className="text-sm text-muted leading-5">
            {isEn
              ? `Get a clear action based on 7-day trends when sending living costs from KRW to ${selectedCurrency}.`
              : `KRW에서 ${selectedCurrency}로 생활비를 보낼 때, 7일 추세 기반으로 명확한 액션을 제시합니다.`}
          </Text>
        </View>

        <View className={`rounded-[28px] p-5 gap-4 ${recommendation.action === 'send_now' ? 'bg-green-600' : 'bg-amber-500'}`}>
          <View className="flex-row items-center justify-between">
            <Text className="text-white/85 text-sm font-semibold">{isEn ? 'AI Recommendation' : 'AI 추천 액션'}</Text>
            <IconSymbol name="paperplane.fill" color="#FFFFFF" size={30} />
          </View>
          <Text className="text-white text-4xl font-bold leading-[46px]">{recommendationTitle}</Text>
          <Text className="text-white/90 text-sm leading-5">{recommendationReason}</Text>
        </View>

        <View className="rounded-3xl bg-surface border border-border p-5 gap-4">
          <View className="flex-row justify-between">
            <View>
              <Text className="text-xs text-muted">{isEn ? `Current ${selectedCurrency}` : `현재 ${selectedCurrency} 기준`}</Text>
              <Text className="mt-1 text-2xl font-bold text-foreground">₩{recommendation.currentRate.toLocaleString('ko-KR')}</Text>
            </View>
            <View className="items-end">
              <Text className="text-xs text-muted">{isEn ? '7-day avg' : '7일 평균'}</Text>
              <Text className="mt-1 text-2xl font-bold text-foreground">₩{Math.round(recommendation.movingAverage).toLocaleString('ko-KR')}</Text>
            </View>
          </View>

          <View className="h-40 flex-row items-end justify-between rounded-2xl bg-background px-3 py-4">
            {series.map((point) => {
              const height = 28 + ((point.rate - min) / Math.max(max - min, 1)) * 88;
              const active = point.date === series[series.length - 1].date;
              return (
                <View key={point.date} className="items-center gap-2">
                  <View style={{ height }} className={`w-6 rounded-full ${active ? 'bg-primary' : 'bg-blue-200'}`} />
                  <Text className="text-[10px] text-muted">{point.date.slice(3)}</Text>
                </View>
              );
            })}
          </View>
          <Text className="text-xs text-muted text-center">{loading ? (isEn ? 'Fetching latest rates' : '최신 환율 확인 중') : `${sourceLabel} ${isEn ? 'source' : '기준'}`}</Text>
        </View>

        <View className="flex-row gap-3">
          <View className="flex-1 rounded-3xl bg-surface border border-border p-4">
            <Text className="text-xs text-muted">{isEn ? 'Expected Saving' : '예상 절감'}</Text>
            <Text className="mt-2 text-xl font-bold text-foreground">₩{recommendation.expectedSavingKrw.toLocaleString('ko-KR')}</Text>
          </View>
          <View className="flex-1 rounded-3xl bg-surface border border-border p-4">
            <Text className="text-xs text-muted">{isEn ? 'Recommendation Score' : '추천 점수'}</Text>
            <Text className="mt-2 text-xl font-bold text-foreground">{recommendation.score}</Text>
          </View>
        </View>

        <TouchableOpacity className="rounded-2xl bg-primary py-4 items-center active:opacity-80">
          <Text className="text-white font-bold">{isEn ? 'Schedule transfer alert' : '송금 알림 예약하기'}</Text>
        </TouchableOpacity>
        <Text className="text-xs text-muted leading-4 text-center">
          {isEn
            ? 'This button is for MVP demo. Real scheduling will be enabled once push notifications and user settings are integrated.'
            : '현재 버튼은 MVP 시연용입니다. 실제 알림 예약은 운영 단계에서 푸시 알림과 사용자 설정이 연결될 때 활성화됩니다.'}
        </Text>
      </View>
    </ScreenContainer>
  );
}
