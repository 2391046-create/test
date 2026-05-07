import { CategoryId, createTransaction, Transaction } from './finance';

/**
 * 영수증 OCR 인식 및 거래 정보 추출
 * 현금 결제 영수증 사진 업로드 시 자동 분석
 */

export type ReceiptData = {
  merchantName: string;
  amount: number;
  currency: string;
  date: string;
  category?: CategoryId;
  confidence: number;
  rawText: string;
};

/**
 * 영수증 이미지에서 텍스트 추출 (OCR)
 * 실제 구현을 위해서는 google-vision, tesseract 등 필요
 * 현재는 모의 구현
 */
export async function extractReceiptText(imageUri: string): Promise<string> {
  try {
    // 실제 구현: Google Vision API 또는 Tesseract.js 사용
    // const response = await fetch('https://vision.googleapis.com/v1/images:annotate', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     requests: [{
    //       image: { content: base64Image },
    //       features: [{ type: 'TEXT_DETECTION' }],
    //     }],
    //   }),
    // });
    // const data = await response.json();
    // return data.responses[0].fullTextAnnotation.text;

    console.log('OCR processing for:', imageUri);
    return 'STARBUCKS COFFEE 15.50 USD';
  } catch (error) {
    console.error('Failed to extract receipt text:', error);
    throw error;
  }
}

/**
 * 영수증 텍스트에서 거래 정보 파싱
 */
export function parseReceiptText(text: string): ReceiptData {
  const lines = text.split('\n').filter((line) => line.trim());

  // 상인명 추출 (첫 번째 또는 두 번째 줄)
  const merchantName = lines[0]?.trim() || 'Unknown Merchant';

  // 금액 추출
  const amountMatch = text.match(/(?:USD|EUR|GBP|JPY|₩|\$|€|£)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)/);
  const amount = amountMatch ? parseFloat(amountMatch[1].replace(/,/g, '')) : 0;

  // 통화 추출
  const currencyMatch = text.match(/USD|EUR|GBP|JPY|KRW|₩|\$|€|£/i);
  const currencyMap: Record<string, string> = {
    $: 'USD',
    '€': 'EUR',
    '£': 'GBP',
    '₩': 'KRW',
  };
  const currency = currencyMap[currencyMatch?.[0] || ''] || currencyMatch?.[0]?.toUpperCase() || 'USD';

  // 날짜 추출
  const dateMatch = text.match(/(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})/);
  const today = new Date().toISOString().slice(0, 10);
  const date = dateMatch ? `${dateMatch[3]}-${dateMatch[1].padStart(2, '0')}-${dateMatch[2].padStart(2, '0')}` : today;

  return {
    merchantName,
    amount,
    currency,
    date,
    confidence: 0.85,
    rawText: text,
  };
}

/**
 * 영수증 데이터를 거래 객체로 변환
 */
export function receiptToTransaction(receiptData: ReceiptData): Transaction {
  const rawText = `${receiptData.merchantName} ${receiptData.amount} ${receiptData.currency}`;
  const transaction = createTransaction(rawText, 'manual', receiptData.date);
  return {
    ...transaction,
    confidence: receiptData.confidence,
  };
}

/**
 * 영수증 이미지 업로드 및 자동 분석 (엔드-투-엔드)
 */
export async function processReceiptImage(imageUri: string): Promise<ReceiptData> {
  try {
    const text = await extractReceiptText(imageUri);
    const receiptData = parseReceiptText(text);
    return receiptData;
  } catch (error) {
    console.error('Failed to process receipt image:', error);
    throw error;
  }
}
