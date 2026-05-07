// 국가 및 통화 설정
export type Currency = "USD" | "JPY" | "GBP" | "EUR" | "CNY" | "THB" | "SGD" | "AUD" | "CAD" | "HKD";

export interface CountryConfig {
  code: string;
  name: string;
  currency: Currency;
  exchangeRate: number;
  flag: string;
}

export const COUNTRY_CONFIGS: Record<Currency, CountryConfig> = {
  USD: {
    code: "US",
    name: "미국",
    currency: "USD",
    exchangeRate: 1300,
    flag: "🇺🇸",
  },
  JPY: {
    code: "JP",
    name: "일본",
    currency: "JPY",
    exchangeRate: 9.5,
    flag: "🇯🇵",
  },
  GBP: {
    code: "GB",
    name: "영국",
    currency: "GBP",
    exchangeRate: 1650,
    flag: "🇬🇧",
  },
  EUR: {
    code: "EU",
    name: "유럽",
    currency: "EUR",
    exchangeRate: 1400,
    flag: "🇪🇺",
  },
  CNY: {
    code: "CN",
    name: "중국",
    currency: "CNY",
    exchangeRate: 180,
    flag: "🇨🇳",
  },
  THB: {
    code: "TH",
    name: "태국",
    currency: "THB",
    exchangeRate: 37,
    flag: "🇹🇭",
  },
  SGD: {
    code: "SG",
    name: "싱가포르",
    currency: "SGD",
    exchangeRate: 970,
    flag: "🇸🇬",
  },
  AUD: {
    code: "AU",
    name: "호주",
    currency: "AUD",
    exchangeRate: 850,
    flag: "🇦🇺",
  },
  CAD: {
    code: "CA",
    name: "캐나다",
    currency: "CAD",
    exchangeRate: 950,
    flag: "🇨🇦",
  },
  HKD: {
    code: "HK",
    name: "홍콩",
    currency: "HKD",
    exchangeRate: 166,
    flag: "🇭🇰",
  },
};

// 영수증 분석 결과
export interface ReceiptItem {
  name: string;
  quantity: number;
  price: number;
}

export interface DutchPayInfo {
  num_people: number;
  per_person_krw: number;
  per_person_local: number;
}

export interface ReceiptAnalysisResult {
  merchant_name: string;
  items: ReceiptItem[];
  subtotal_local: number;
  tax_local: number;
  total_local: number;
  currency: Currency;
  total_krw: number;
  exchange_rate: number;
  dutch_pay: DutchPayInfo;
  date?: string;
  time?: string;
  error?: string;
}

// 메뉴판 분석 결과
export interface MenuItem {
  name: string;
  price_local: number;
  price_krw: number;
  currency: Currency;
  description: string;
  average_price_local?: number;
  price_comparison: string;
}

export interface MenuAnalysisResult {
  restaurant_name: string;
  menu_items: MenuItem[];
  currency: Currency;
  exchange_rate: number;
  error?: string;
}

// 더치페이 정산 결과
export interface DutchPayMember {
  name: string;
  amount_paid: number;
  should_pay: number;
  settlement: number; // 음수면 받을 금액, 양수면 낼 금액
}

export interface DutchPaySettlement {
  total_amount: number;
  num_people: number;
  per_person: number;
  members: DutchPayMember[];
  settlements: Array<{
    from: string;
    to: string;
    amount: number;
  }>;
}

// XRPL 트랜잭션 결과
export interface XRPLTransactionResult {
  success: boolean;
  tx_hash?: string;
  ledger_index?: number;
  timestamp?: string;
  memo_data?: Record<string, any>;
  account?: string;
  error?: string;
}

// 앱 설정
export interface AppSettings {
  selectedCurrency: Currency;
  selectedCountry: string;
  xrplWalletSeed?: string;
  xrplAccountAddress?: string;
  backendUrl: string;
  autoSaveToXRPL: boolean;
}
