/**
 * receipt-ocr.ts
 * records.tsx에서 processReceiptImage(uri) 형태로 호출됨
 * useReceiptScanner 훅의 analyzeReceipt 래핑
 */

export interface SimpleReceiptData {
  merchantName: string;
  amount: number;
  currency: string;
  date: string;
}

const DEFAULT_BACKEND =
  (process.env.EXPO_PUBLIC_API_URL as string) || "http://localhost:8000";

/**
 * 이미지 URI → Base64 변환
 */
export async function imageUriToBase64(imageUri: string): Promise<string> {
  const response = await fetch(imageUri);
  const blob = await response.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const r = reader.result as string;
      resolve(r.includes(",") ? r.split(",")[1] : r);
    };
    reader.onerror = () => reject(new Error("이미지 변환 실패"));
    reader.readAsDataURL(blob);
  });
}

/**
 * records.tsx에서 호출: processReceiptImage(uri)
 * 백엔드 Gemini AI로 영수증 분석
 */
export async function processReceiptImage(
  imageUri: string,
  backendUrl = DEFAULT_BACKEND
): Promise<SimpleReceiptData> {
  const base64 = await imageUriToBase64(imageUri);

  const resp = await fetch(`${backendUrl}/api/transactions/analyze-receipt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_base64: base64,
      currency: "USD",
      user_id: "default",
    }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "분석 실패" }));
    throw new Error(err.detail || "영수증 분석 실패");
  }

  const data = await resp.json();
  const tx = data.transaction;

  return {
    merchantName: tx.merchant_name ?? "Unknown",
    amount: tx.amount_local ?? 0,
    currency: tx.currency ?? "USD",
    date: tx.transaction_date?.split("T")[0] ?? new Date().toISOString().split("T")[0],
  };
}
