/**
 * 영수증 OCR - 백엔드 Gemini AI 호출
 * 현금 결제 영수증 = analyze-receipt 엔드포인트로 통합
 * (하단 영수증 탭 기능과 동일하므로 통합됨)
 */
import { analyzeReceipt } from "./api";

export type ReceiptData = {
  merchantName: string;
  amount: number;
  currency: string;
  date: string;
  category?: string;
  confidence: number;
  items: Array<{ name: string; quantity: number; price: number }>;
  amountKrw: number;
  exchangeRate: number;
};

/**
 * 영수증 이미지 URI → Base64 변환
 */
export async function imageUriToBase64(imageUri: string): Promise<string> {
  const response = await fetch(imageUri);
  const blob = await response.blob();

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.includes(",") ? result.split(",")[1] : result;
      resolve(base64);
    };
    reader.onerror = () => reject(new Error("이미지 변환 실패"));
    reader.readAsDataURL(blob);
  });
}

/**
 * 영수증 이미지 분석 (백엔드 Gemini AI 사용)
 * 현금 결제 영수증도 동일하게 처리
 */
export async function analyzeReceiptImage(
  imageUri: string,
  userId: string,
  currency = "USD"
): Promise<ReceiptData> {
  const base64 = await imageUriToBase64(imageUri);
  const result = await analyzeReceipt(base64, userId, currency) as any;

  if (!result.success) {
    throw new Error(result.error || "영수증 분석 실패");
  }

  const tx = result.transaction;
  return {
    merchantName: tx.merchant_name,
    amount: tx.amount_local,
    currency: tx.currency,
    date: tx.transaction_date,
    category: tx.category,
    confidence: tx.category_confidence,
    items: tx.items || [],
    amountKrw: tx.amount_krw,
    exchangeRate: tx.exchange_rate,
  };
}
