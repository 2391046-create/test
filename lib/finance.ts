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
