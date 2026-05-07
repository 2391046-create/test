from pathlib import Path

ROOT = Path('/home/ubuntu/student-finance-compass')

def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + '\n', encoding='utf-8')

write('lib/finance.ts', r'''
export type CategoryId = 'food' | 'transport' | 'housing' | 'study' | 'shopping' | 'health' | 'transfer' | 'other';

export type Category = {
  id: CategoryId;
  label: string;
  tone: string;
  keywords: string[];
};

export type Transaction = {
  id: string;
  merchant: string;
  amount: number;
  currency: string;
  category: CategoryId;
  confidence: number;
  date: string;
  source: 'notification' | 'manual' | 'sample';
  rawText: string;
  hash: string;
};

export type ExchangePoint = {
  date: string;
  rate: number;
};

export type ExchangeRecommendation = {
  action: 'send_now' | 'wait';
  title: string;
  headline: string;
  reason: string;
  waitDays: number;
  score: number;
  currentRate: number;
  movingAverage: number;
  expectedSavingKrw: number;
};

export const categories: Category[] = [
  { id: 'food', label: '식비', tone: '#16A34A', keywords: ['starbucks', '스타벅스', 'cafe', 'coffee', 'restaurant', 'mcdonald', 'burger', '식당', '카페', '마트', 'grocery', 'tesco', 'whole foods'] },
  { id: 'transport', label: '교통', tone: '#2563EB', keywords: ['uber', 'lyft', 'metro', 'train', 'bus', 'transport', 'tube', '교통', '택시', '지하철'] },
  { id: 'housing', label: '주거', tone: '#7C3AED', keywords: ['rent', '월세', 'housing', 'dorm', '기숙사', 'airbnb', 'utility', 'electric'] },
  { id: 'study', label: '학업', tone: '#0891B2', keywords: ['university', 'campus', 'book', 'library', 'tuition', 'school', '학교', '서점', '교재'] },
  { id: 'shopping', label: '쇼핑', tone: '#DB2777', keywords: ['amazon', 'zara', 'uniqlo', 'target', 'shopping', 'store', '쇼핑', '쿠팡'] },
  { id: 'health', label: '의료', tone: '#DC2626', keywords: ['pharmacy', 'clinic', 'hospital', 'drug', '약국', '병원', '의료'] },
  { id: 'transfer', label: '송금', tone: '#F59E0B', keywords: ['transfer', 'remit', 'wire', '송금', 'exchange', '환전', 'xrpl'] },
  { id: 'other', label: '기타', tone: '#64748B', keywords: [] },
];

export const sampleTransactions: Transaction[] = [
  createTransaction('STARBUCKS LONDON 승인 GBP 5.40', 'sample', '2026-05-06'),
  createTransaction('UBER TRIP 결제 USD 18.20', 'sample', '2026-05-05'),
  createTransaction('UNIVERSITY BOOKSTORE EUR 42.00 paid', 'sample', '2026-05-03'),
  createTransaction('RENT DORMITORY transfer EUR 640.00', 'sample', '2026-05-01'),
];

export const exchangeSeries: ExchangePoint[] = [
  { date: '04/30', rate: 1378.2 },
  { date: '05/01', rate: 1381.4 },
  { date: '05/02', rate: 1374.6 },
  { date: '05/03', rate: 1368.1 },
  { date: '05/04', rate: 1362.8 },
  { date: '05/05', rate: 1359.3 },
  { date: '05/06', rate: 1354.7 },
];

export function getCategory(id: CategoryId) {
  return categories.find((category) => category.id === id) ?? categories[categories.length - 1];
}

export function categorizeMerchant(text: string): { category: CategoryId; confidence: number; matchedKeyword?: string } {
  const normalized = text.toLowerCase();
  for (const category of categories) {
    if (category.id === 'other') continue;
    const matchedKeyword = category.keywords.find((keyword) => normalized.includes(keyword.toLowerCase()));
    if (matchedKeyword) {
      return { category: category.id, confidence: 0.92, matchedKeyword };
    }
  }
  return { category: 'other', confidence: 0.48 };
}

export function parsePaymentNotification(rawText: string): Omit<Transaction, 'id' | 'date' | 'source' | 'hash'> {
  const text = rawText.replace(/\s+/g, ' ').trim();
  const amountMatch = text.match(/(?:KRW|USD|EUR|GBP|JPY|CAD|AUD|₩|\$|€|£)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(KRW|USD|EUR|GBP|JPY|CAD|AUD|원|달러|유로|파운드)?/i);
  const currencySymbol = text.includes('€') ? 'EUR' : text.includes('£') ? 'GBP' : text.includes('$') ? 'USD' : undefined;
  const currency = normalizeCurrency(amountMatch?.[2] ?? currencySymbol ?? inferCurrency(text));
  const amount = Number((amountMatch?.[1] ?? '0').replace(/,/g, ''));
  const merchant = extractMerchant(text);
  const { category, confidence } = categorizeMerchant(`${merchant} ${text}`);

  return {
    merchant,
    amount,
    currency,
    category,
    confidence,
    rawText: rawText.trim(),
  };
}

export function createTransaction(rawText: string, source: Transaction['source'] = 'notification', date = new Date().toISOString().slice(0, 10)): Transaction {
  const parsed = parsePaymentNotification(rawText);
  const seed = `${parsed.merchant}-${parsed.amount}-${parsed.currency}-${date}-${rawText}`;
  return {
    ...parsed,
    id: hashSeed(seed).slice(0, 12),
    date,
    source,
    hash: `XRPL-${hashSeed(seed).toUpperCase().slice(0, 18)}`,
  };
}

export function summarizeByCategory(transactions: Transaction[]) {
  return categories
    .filter((category) => category.id !== 'other' || transactions.some((item) => item.category === 'other'))
    .map((category) => {
      const items = transactions.filter((item) => item.category === category.id);
      const amount = items.reduce((sum, item) => sum + convertToKrw(item.amount, item.currency), 0);
      return { category, amount, count: items.length };
    })
    .filter((row) => row.count > 0);
}

export function analyzeExchangeTiming(series: ExchangePoint[], sendAmountForeign = 1000): ExchangeRecommendation {
  const currentRate = series[series.length - 1]?.rate ?? 0;
  const previousRate = series[series.length - 2]?.rate ?? currentRate;
  const movingAverage = series.reduce((sum, point) => sum + point.rate, 0) / Math.max(series.length, 1);
  const shortTermDrop = previousRate - currentRate;
  const belowAverage = movingAverage - currentRate;
  const score = Math.round((belowAverage + shortTermDrop * 1.5) * 10) / 10;

  if (score >= 8) {
    return {
      action: 'send_now',
      title: '지금 보내세요',
      headline: '현재 환율이 7일 평균보다 유리합니다.',
      reason: `현재 ${currentRate.toLocaleString('ko-KR')}원은 7일 평균 ${Math.round(movingAverage).toLocaleString('ko-KR')}원보다 낮고, 전일 대비 ${shortTermDrop.toFixed(1)}원 하락했습니다.`,
      waitDays: 0,
      score,
      currentRate,
      movingAverage,
      expectedSavingKrw: Math.max(0, Math.round(belowAverage * sendAmountForeign)),
    };
  }

  const waitDays = score < 0 ? 3 : 2;
  return {
    action: 'wait',
    title: `${waitDays}일 대기 권장`,
    headline: '단기 추세가 아직 충분히 유리하지 않습니다.',
    reason: `현재 ${currentRate.toLocaleString('ko-KR')}원은 7일 평균 ${Math.round(movingAverage).toLocaleString('ko-KR')}원과의 차이가 작아 추가 관찰이 필요합니다.`,
    waitDays,
    score,
    currentRate,
    movingAverage,
    expectedSavingKrw: Math.max(0, Math.round(Math.abs(score) * sendAmountForeign * 0.2)),
  };
}

export function convertToKrw(amount: number, currency: string) {
  const rates: Record<string, number> = { KRW: 1, USD: 1355, EUR: 1460, GBP: 1710, JPY: 9.1, CAD: 990, AUD: 890 };
  return amount * (rates[currency] ?? 1);
}

function normalizeCurrency(input?: string) {
  const value = (input ?? '').toUpperCase();
  if (value === '원') return 'KRW';
  if (value === '달러') return 'USD';
  if (value === '유로') return 'EUR';
  if (value === '파운드') return 'GBP';
  if (['KRW', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD'].includes(value)) return value;
  return 'USD';
}

function inferCurrency(text: string) {
  if (/\bEUR\b|유로|€/.test(text)) return 'EUR';
  if (/\bGBP\b|파운드|£/.test(text)) return 'GBP';
  if (/\bKRW\b|원|₩/.test(text)) return 'KRW';
  return 'USD';
}

function extractMerchant(text: string) {
  const cleaned = text
    .replace(/\[[^\]]+\]/g, '')
    .replace(/승인|결제|paid|payment|card|카드|체크|신용|사용|알림/gi, '')
    .replace(/(?:KRW|USD|EUR|GBP|JPY|CAD|AUD|₩|\$|€|£)?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?\s*(?:KRW|USD|EUR|GBP|JPY|CAD|AUD|원|달러|유로|파운드)?/gi, '')
    .replace(/\s+/g, ' ')
    .trim();
  const words = cleaned.split(' ').filter(Boolean);
  return words.slice(0, 3).join(' ') || 'Unknown Merchant';
}

function hashSeed(seed: string) {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(8, '0');
}
''')

write('lib/finance-context.tsx', r'''
import { ReactNode, createContext, useContext, useMemo, useState } from 'react';

import { CategoryId, Transaction, createTransaction, sampleTransactions } from '@/lib/finance';

type FinanceContextValue = {
  transactions: Transaction[];
  addNotification: (text: string) => Transaction;
  updateCategory: (id: string, category: CategoryId) => void;
};

const FinanceContext = createContext<FinanceContextValue | null>(null);

export function FinanceProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<Transaction[]>(sampleTransactions);

  const value = useMemo<FinanceContextValue>(() => ({
    transactions,
    addNotification: (text: string) => {
      const transaction = createTransaction(text, 'notification');
      setTransactions((current) => [transaction, ...current]);
      return transaction;
    },
    updateCategory: (id: string, category: CategoryId) => {
      setTransactions((current) => current.map((item) => item.id === id ? { ...item, category, confidence: 1 } : item));
    },
  }), [transactions]);

  return <FinanceContext.Provider value={value}>{children}</FinanceContext.Provider>;
}

export function useFinance() {
  const context = useContext(FinanceContext);
  if (!context) {
    throw new Error('useFinance must be used within FinanceProvider');
  }
  return context;
}
''')

write('theme.config.js', r'''
/** @type {const} */
const themeColors = {
  primary: { light: '#2563EB', dark: '#60A5FA' },
  background: { light: '#F8FAFC', dark: '#0B1120' },
  surface: { light: '#FFFFFF', dark: '#111827' },
  foreground: { light: '#0F172A', dark: '#F8FAFC' },
  muted: { light: '#64748B', dark: '#94A3B8' },
  border: { light: '#E2E8F0', dark: '#263244' },
  success: { light: '#16A34A', dark: '#4ADE80' },
  warning: { light: '#F59E0B', dark: '#FBBF24' },
  error: { light: '#DC2626', dark: '#F87171' },
};

module.exports = { themeColors };
''')

write('components/ui/icon-symbol.tsx', r'''
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { SymbolWeight, SymbolViewProps } from 'expo-symbols';
import { ComponentProps } from 'react';
import { OpaqueColorValue, type StyleProp, type TextStyle } from 'react-native';

type IconMapping = Record<SymbolViewProps['name'], ComponentProps<typeof MaterialIcons>['name']>;
type IconSymbolName = keyof typeof MAPPING;

const MAPPING = {
  'house.fill': 'home',
  'list.bullet.rectangle.fill': 'receipt-long',
  'chart.pie.fill': 'pie-chart',
  'chart.line.uptrend.xyaxis': 'show-chart',
  'gearshape.fill': 'settings',
  'paperplane.fill': 'send',
  'chevron.right': 'chevron-right',
  'checkmark.seal.fill': 'verified',
  'bell.badge.fill': 'notifications',
  'wallet.pass.fill': 'account-balance-wallet',
  'doc.text.fill': 'description',
} as IconMapping;

export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>;
  weight?: SymbolWeight;
}) {
  return <MaterialIcons color={color} size={size} name={MAPPING[name]} style={style} />;
}
''')

write('app/(tabs)/_layout.tsx', r'''
import { Tabs } from 'expo-router';
import { Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useColors } from '@/hooks/use-colors';

export default function TabLayout() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const bottomPadding = Platform.OS === 'web' ? 12 : Math.max(insets.bottom, 8);
  const tabBarHeight = 58 + bottomPadding;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.tint,
        tabBarInactiveTintColor: colors.muted,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
        tabBarStyle: {
          paddingTop: 8,
          paddingBottom: bottomPadding,
          height: tabBarHeight,
          backgroundColor: colors.background,
          borderTopColor: colors.border,
          borderTopWidth: 0.5,
        },
      }}
    >
      <Tabs.Screen name="index" options={{ title: '홈', tabBarIcon: ({ color }) => <IconSymbol size={26} name="house.fill" color={color} /> }} />
      <Tabs.Screen name="records" options={{ title: '기록', tabBarIcon: ({ color }) => <IconSymbol size={26} name="list.bullet.rectangle.fill" color={color} /> }} />
      <Tabs.Screen name="report" options={{ title: '리포트', tabBarIcon: ({ color }) => <IconSymbol size={26} name="chart.pie.fill" color={color} /> }} />
      <Tabs.Screen name="rates" options={{ title: '환율', tabBarIcon: ({ color }) => <IconSymbol size={26} name="chart.line.uptrend.xyaxis" color={color} /> }} />
      <Tabs.Screen name="settings" options={{ title: '설정', tabBarIcon: ({ color }) => <IconSymbol size={26} name="gearshape.fill" color={color} /> }} />
    </Tabs>
  );
}
''')

write('app/(tabs)/index.tsx', r'''
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
''')

write('app/(tabs)/records.tsx', r'''
import { useState } from 'react';
import { FlatList, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { ScreenContainer } from '@/components/screen-container';
import { CategoryId, categories, getCategory } from '@/lib/finance';
import { useFinance } from '@/lib/finance-context';

const EXAMPLE = 'STARBUCKS NEW YORK 카드 승인 USD 7.25';

export default function RecordsScreen() {
  const { transactions, addNotification, updateCategory } = useFinance();
  const [text, setText] = useState(EXAMPLE);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = transactions.find((item) => item.id === selectedId) ?? transactions[0];

  return (
    <ScreenContainer className="px-5 pt-2">
      <FlatList
        data={transactions}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <View className="gap-4 pb-4">
            <View>
              <Text className="text-3xl font-bold text-foreground leading-10">결제 알림 인식</Text>
              <Text className="text-sm text-muted leading-5">카드·은행 알림 문구를 붙여넣으면 가맹점, 금액, 통화를 추출하고 카테고리를 추천합니다.</Text>
            </View>

            <View className="rounded-3xl bg-surface border border-border p-4 gap-3">
              <Text className="text-sm font-bold text-foreground">알림 텍스트</Text>
              <TextInput
                value={text}
                onChangeText={setText}
                multiline
                returnKeyType="done"
                placeholder="예: STARBUCKS LONDON 승인 GBP 5.40"
                placeholderTextColor="#94A3B8"
                className="min-h-24 rounded-2xl bg-background border border-border px-4 py-3 text-foreground leading-5"
                textAlignVertical="top"
              />
              <TouchableOpacity
                className="rounded-2xl bg-primary py-4 items-center active:opacity-80"
                onPress={() => {
                  if (!text.trim()) return;
                  const created = addNotification(text);
                  setSelectedId(created.id);
                  setText('');
                }}
              >
                <Text className="text-white font-bold">결제내역 자동 분류</Text>
              </TouchableOpacity>
            </View>

            {selected ? (
              <View className="rounded-3xl bg-surface border border-border p-4 gap-3">
                <Text className="text-sm font-bold text-foreground">선택 거래 카테고리 수정</Text>
                <Text className="text-xs text-muted leading-4">자동 분류가 맞지 않으면 카테고리를 직접 바꿀 수 있습니다. 수정된 거래는 신뢰도 100%로 표시됩니다.</Text>
                <View className="flex-row flex-wrap gap-2">
                  {categories.map((category) => (
                    <TouchableOpacity
                      key={category.id}
                      onPress={() => updateCategory(selected.id, category.id as CategoryId)}
                      className={`rounded-full px-3 py-2 border ${selected.category === category.id ? 'bg-primary border-primary' : 'bg-background border-border'}`}
                    >
                      <Text className={`text-xs font-bold ${selected.category === category.id ? 'text-white' : 'text-foreground'}`}>{category.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            ) : null}

            <Text className="text-lg font-bold text-foreground">거래 기록</Text>
          </View>
        }
        renderItem={({ item }) => {
          const category = getCategory(item.category);
          return (
            <TouchableOpacity onPress={() => setSelectedId(item.id)} className="mb-3 rounded-2xl bg-surface border border-border p-4 active:opacity-80">
              <View className="flex-row items-start justify-between gap-3">
                <View className="flex-1">
                  <Text className="text-base font-bold text-foreground" numberOfLines={1}>{item.merchant}</Text>
                  <Text className="mt-1 text-xs text-muted">{item.date} · {item.hash}</Text>
                  <View className="mt-3 flex-row items-center gap-2">
                    <View style={{ backgroundColor: category.tone }} className="rounded-full px-3 py-1">
                      <Text className="text-white text-xs font-bold">{category.label}</Text>
                    </View>
                    <Text className="text-xs text-muted">신뢰도 {Math.round(item.confidence * 100)}%</Text>
                  </View>
                </View>
                <Text className="text-base font-bold text-foreground">{item.currency} {item.amount.toLocaleString()}</Text>
              </View>
            </TouchableOpacity>
          );
        }}
        ListFooterComponent={<View className="h-8" />}
      />
    </ScreenContainer>
  );
}
''')

write('app/(tabs)/report.tsx', r'''
import { FlatList, Text, View } from 'react-native';

import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { convertToKrw, summarizeByCategory } from '@/lib/finance';
import { useFinance } from '@/lib/finance-context';

export default function ReportScreen() {
  const { transactions } = useFinance();
  const rows = summarizeByCategory(transactions);
  const total = transactions.reduce((sum, item) => sum + convertToKrw(item.amount, item.currency), 0);
  const verified = transactions.filter((item) => item.confidence >= 0.9).length;

  return (
    <ScreenContainer className="px-5 pt-2">
      <FlatList
        data={rows}
        keyExtractor={(item) => item.category.id}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <View className="gap-4 pb-4">
            <View>
              <Text className="text-3xl font-bold text-foreground leading-10">증빙 리포트</Text>
              <Text className="text-sm text-muted leading-5">장학금, 비자, 부모님 보고에 필요한 지출 요약을 카테고리별로 준비합니다.</Text>
            </View>

            <View className="rounded-[28px] bg-surface border border-border p-5 gap-4">
              <View className="flex-row items-center justify-between">
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
          </View>
        }
      />
    </ScreenContainer>
  );
}
''')

write('app/(tabs)/rates.tsx', r'''
import { Text, TouchableOpacity, View } from 'react-native';

import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { analyzeExchangeTiming, exchangeSeries } from '@/lib/finance';

export default function RatesScreen() {
  const recommendation = analyzeExchangeTiming(exchangeSeries, 1000);
  const max = Math.max(...exchangeSeries.map((point) => point.rate));
  const min = Math.min(...exchangeSeries.map((point) => point.rate));

  return (
    <ScreenContainer className="px-5 pt-2">
      <View className="flex-1 gap-5">
        <View>
          <Text className="text-3xl font-bold text-foreground leading-10">환율 타이밍</Text>
          <Text className="text-sm text-muted leading-5">KRW에서 외화로 생활비를 보낼 때, 7일 추세 기반으로 명확한 액션을 제시합니다.</Text>
        </View>

        <View className={`rounded-[28px] p-5 gap-4 ${recommendation.action === 'send_now' ? 'bg-green-600' : 'bg-amber-500'}`}>
          <View className="flex-row items-center justify-between">
            <Text className="text-white/85 text-sm font-semibold">AI 추천 액션</Text>
            <IconSymbol name="paperplane.fill" color="#FFFFFF" size={30} />
          </View>
          <Text className="text-white text-4xl font-bold leading-[46px]">{recommendation.title}</Text>
          <Text className="text-white/90 text-sm leading-5">{recommendation.reason}</Text>
        </View>

        <View className="rounded-3xl bg-surface border border-border p-5 gap-4">
          <View className="flex-row justify-between">
            <View>
              <Text className="text-xs text-muted">현재 USD 기준</Text>
              <Text className="mt-1 text-2xl font-bold text-foreground">₩{recommendation.currentRate.toLocaleString('ko-KR')}</Text>
            </View>
            <View className="items-end">
              <Text className="text-xs text-muted">7일 평균</Text>
              <Text className="mt-1 text-2xl font-bold text-foreground">₩{Math.round(recommendation.movingAverage).toLocaleString('ko-KR')}</Text>
            </View>
          </View>

          <View className="h-40 flex-row items-end justify-between rounded-2xl bg-background px-3 py-4">
            {exchangeSeries.map((point) => {
              const height = 28 + ((point.rate - min) / Math.max(max - min, 1)) * 88;
              const active = point.date === exchangeSeries[exchangeSeries.length - 1].date;
              return (
                <View key={point.date} className="items-center gap-2">
                  <View style={{ height }} className={`w-6 rounded-full ${active ? 'bg-primary' : 'bg-blue-200'}`} />
                  <Text className="text-[10px] text-muted">{point.date.slice(3)}</Text>
                </View>
              );
            })}
          </View>
        </View>

        <View className="flex-row gap-3">
          <View className="flex-1 rounded-3xl bg-surface border border-border p-4">
            <Text className="text-xs text-muted">예상 절감</Text>
            <Text className="mt-2 text-xl font-bold text-foreground">₩{recommendation.expectedSavingKrw.toLocaleString('ko-KR')}</Text>
          </View>
          <View className="flex-1 rounded-3xl bg-surface border border-border p-4">
            <Text className="text-xs text-muted">추천 점수</Text>
            <Text className="mt-2 text-xl font-bold text-foreground">{recommendation.score}</Text>
          </View>
        </View>

        <TouchableOpacity className="rounded-2xl bg-primary py-4 items-center active:opacity-80">
          <Text className="text-white font-bold">송금 알림 예약하기</Text>
        </TouchableOpacity>
        <Text className="text-xs text-muted leading-4 text-center">현재 버튼은 MVP 시연용입니다. 실제 알림 예약은 운영 단계에서 푸시 알림과 환율 API가 연결될 때 활성화됩니다.</Text>
      </View>
    </ScreenContainer>
  );
}
''')

write('app/(tabs)/settings.tsx', r'''
import { FlatList, Text, View } from 'react-native';

import { ScreenContainer } from '@/components/screen-container';
import { categories } from '@/lib/finance';

export default function SettingsScreen() {
  return (
    <ScreenContainer className="px-5 pt-2">
      <FlatList
        data={categories}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <View className="gap-4 pb-4">
            <View>
              <Text className="text-3xl font-bold text-foreground leading-10">설정</Text>
              <Text className="text-sm text-muted leading-5">자동 분류 규칙과 서비스 범위를 확인합니다.</Text>
            </View>
            <View className="rounded-3xl bg-surface border border-border p-5 gap-2">
              <Text className="text-base font-bold text-foreground">MVP 운영 방식</Text>
              <Text className="text-sm text-muted leading-5">이 버전은 개인정보 보호와 플랫폼 제약을 고려해 실제 알림 권한을 읽지 않고, 사용자가 붙여넣은 결제 문구를 분석합니다. 향후 금융 API, OS 권한, XRPL 지갑이 연결되면 자동화 범위를 확장할 수 있습니다.</Text>
            </View>
            <Text className="text-lg font-bold text-foreground">카테고리 키워드</Text>
          </View>
        }
        renderItem={({ item }) => (
          <View className="mb-3 rounded-2xl bg-surface border border-border p-4">
            <View className="flex-row items-center gap-3">
              <View style={{ backgroundColor: item.tone }} className="h-4 w-4 rounded-full" />
              <Text className="text-base font-bold text-foreground">{item.label}</Text>
            </View>
            <Text className="mt-2 text-xs text-muted leading-4">{item.keywords.length ? item.keywords.slice(0, 8).join(', ') : '분류 규칙에 매칭되지 않은 거래'}</Text>
          </View>
        )}
        ListFooterComponent={
          <View className="rounded-3xl bg-surface border border-border p-4 mb-8">
            <Text className="text-base font-bold text-foreground">장기 확장 방향</Text>
            <Text className="mt-2 text-sm text-muted leading-5">첨부 기획의 XRPL 기반 다국 통화 지갑, DEX 환전, 온체인 Memo 태깅, 해시·QR 검증 리포트는 장기 로드맵으로 유지했습니다. 현재 앱은 투자 없이 핵심 UX를 검증할 수 있는 프로토타입입니다.</Text>
          </View>
        }
      />
    </ScreenContainer>
  );
}
''')

write('tests/finance.test.ts', r'''
import { describe, expect, it } from 'vitest';

import { analyzeExchangeTiming, createTransaction, exchangeSeries, parsePaymentNotification } from '@/lib/finance';

describe('finance helpers', () => {
  it('parses merchant, amount and food category from Starbucks payment text', () => {
    const parsed = parsePaymentNotification('STARBUCKS LONDON 카드 승인 GBP 5.40');
    expect(parsed.merchant).toContain('STARBUCKS');
    expect(parsed.amount).toBe(5.4);
    expect(parsed.currency).toBe('GBP');
    expect(parsed.category).toBe('food');
  });

  it('creates deterministic proof-like hash for a transaction', () => {
    const transaction = createTransaction('UBER TRIP 결제 USD 18.20', 'notification', '2026-05-06');
    expect(transaction.category).toBe('transport');
    expect(transaction.hash.startsWith('XRPL-')).toBe(true);
  });

  it('returns a clear exchange action recommendation', () => {
    const recommendation = analyzeExchangeTiming(exchangeSeries, 1000);
    expect(['send_now', 'wait']).toContain(recommendation.action);
    expect(recommendation.title.length).toBeGreaterThan(0);
  });
});
''')
