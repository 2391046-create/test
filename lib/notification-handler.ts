import * as Notifications from 'expo-notifications';
import { CategorizationRule, createTransaction, Transaction } from './finance';

/**
 * 백그라운드 알림 수집 및 자동 파싱 로직
 * 은행 앱 푸시/문자 알림을 감지하고 거래 정보로 변환
 */

export type NotificationSource = 'push' | 'sms' | 'clipboard';

export async function requestNotificationPermissions(): Promise<boolean> {
  try {
    const { status } = await Notifications.requestPermissionsAsync();
    return status === 'granted';
  } catch (error) {
    console.error('Failed to request notification permissions:', error);
    return false;
  }
}

export function setupNotificationListener(onNewTransaction: (transaction: Transaction) => void, customRules?: CategorizationRule[]) {
  // 포그라운드 알림 수신
  const foregroundSubscription = Notifications.addNotificationReceivedListener((notification) => {
    const text = extractNotificationText(notification);
    if (isPaymentNotification(text)) {
      const transaction = createTransaction(text, 'notification', new Date().toISOString().slice(0, 10), customRules);
      onNewTransaction(transaction);
    }
  });

  // 백그라운드 알림 응답 처리
  const responseSubscription = Notifications.addNotificationResponseReceivedListener((response) => {
    const text = extractNotificationText(response.notification);
    if (isPaymentNotification(text)) {
      const transaction = createTransaction(text, 'notification', new Date().toISOString().slice(0, 10), customRules);
      onNewTransaction(transaction);
    }
  });

  return () => {
    foregroundSubscription.remove();
    responseSubscription.remove();
  };
}

function extractNotificationText(notification: Notifications.Notification): string {
  const title = notification.request.content.title || '';
  const body = notification.request.content.body || '';
  return `${title} ${body}`.trim();
}

/**
 * 은행/카드사 알림 패턴 인식
 * 주요 은행/카드사 알림 키워드로 결제 알림 여부 판단
 */
function isPaymentNotification(text: string): boolean {
  const paymentKeywords = [
    // 한국 은행/카드사
    'kb국민', '우리은행', '신한은행', '하나은행', '농협', 'nh', '기업은행', '국민카드', '신한카드', '현대카드', 'bc카드', '삼성카드',
    // 결제 관련 키워드
    '승인', '결제', '사용', '출금', '이체', 'payment', 'transaction', 'approved', 'charged', 'debit',
    // 통화 기호
    'krw', 'usd', 'eur', 'gbp', '원', '달러', '유로', '파운드', '₩', '$', '€', '£',
  ];

  const lowerText = text.toLowerCase();
  return paymentKeywords.some((keyword) => lowerText.includes(keyword));
}

/**
 * 클립보드에서 결제 알림 텍스트 감지 및 자동 추가
 * 사용자가 은행 앱에서 알림을 복사하면 자동으로 감지
 */
export async function monitorClipboard(onClipboardChange: (text: string) => void): Promise<() => void> {
  // 웹 환경에서는 Clipboard API 사용, 네이티브는 별도 라이브러리 필요
  // 현재는 기본 구현만 제공 (실제 구현은 react-native-clipboard 등 필요)

  let lastClipboardText = '';

  const checkClipboard = async () => {
    try {
      // 실제 구현을 위해서는 react-native-clipboard 라이브러리 필요
      // const text = await Clipboard.getString();
      // if (text !== lastClipboardText && isPaymentNotification(text)) {
      //   lastClipboardText = text;
      //   onClipboardChange(text);
      // }
    } catch (error) {
      console.error('Failed to monitor clipboard:', error);
    }
  };

  const interval = setInterval(checkClipboard, 2000);
  return () => clearInterval(interval);
}

/**
 * 은행 API 연동 (향후 확장)
 * 실제 은행 API를 통해 거래내역 직접 조회
 */
export async function fetchBankTransactions(bankCode: string, accountNumber: string, apiKey: string): Promise<Transaction[]> {
  // 향후 구현: 은행 API 연동
  // 현재는 스텁 구현
  console.log('Bank API integration placeholder:', { bankCode, accountNumber });
  return [];
}
