# 프론트엔드 통합 가이드

React Native 프론트엔드와 FastAPI 백엔드를 통합하는 방법

## 🔗 API 클라이언트 설정

### 1. Axios 인스턴스 생성

```typescript
// lib/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // 필요시 인증 토큰 추가
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
```

## 📝 분류 API 사용

### 텍스트 분류

```typescript
// hooks/useClassify.ts
import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { ClassifyResponse } from '@/types/api';

export function useClassify() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const classifyText = async (text: string): Promise<ClassifyResponse | null> => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post<ClassifyResponse>('/classify', {
        text,
      });
      
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Classification failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const classifyImage = async (imageBase64: string): Promise<ClassifyResponse | null> => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post<ClassifyResponse>('/classify', {
        image_base64: imageBase64,
      });
      
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Image classification failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { classifyText, classifyImage, loading, error };
}
```

### 컴포넌트에서 사용

```typescript
// app/(tabs)/index.tsx
import { useState } from 'react';
import { View, Text, TextInput, Pressable, ScrollView } from 'react-native';
import { useClassify } from '@/hooks/useClassify';
import { ScreenContainer } from '@/components/screen-container';

export default function HomeScreen() {
  const [paymentText, setPaymentText] = useState('');
  const [result, setResult] = useState(null);
  const { classifyText, loading } = useClassify();

  const handleClassify = async () => {
    const classified = await classifyText(paymentText);
    if (classified) {
      setResult(classified);
    }
  };

  return (
    <ScreenContainer className="p-4">
      <ScrollView>
        <Text className="text-2xl font-bold text-foreground mb-4">
          결제 내역 분류
        </Text>

        <TextInput
          className="border border-border rounded-lg p-3 mb-4 text-foreground"
          placeholder="결제 알림 텍스트를 입력하세요"
          value={paymentText}
          onChangeText={setPaymentText}
          multiline
        />

        <Pressable
          onPress={handleClassify}
          disabled={loading}
          className="bg-primary p-3 rounded-lg mb-4"
        >
          <Text className="text-background font-semibold text-center">
            {loading ? '분류 중...' : '분류하기'}
          </Text>
        </Pressable>

        {result && (
          <View className="bg-surface p-4 rounded-lg">
            <Text className="text-lg font-bold text-foreground mb-2">
              분류 결과
            </Text>
            <Text className="text-foreground">상호명: {result.merchant}</Text>
            <Text className="text-foreground">금액: ₩{result.amount.toLocaleString()}</Text>
            <Text className="text-foreground">카테고리: {result.category}</Text>
            <Text className="text-foreground">신뢰도: {(result.confidence * 100).toFixed(1)}%</Text>
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}
```

## 💾 거래 기록 API 사용

```typescript
// hooks/useRecordTransaction.ts
import { useState } from 'react';
import { apiClient } from '@/lib/api';
import { RecordResponse } from '@/types/api';

export function useRecordTransaction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recordTransaction = async (
    merchant: string,
    amount: number,
    category: string,
    currency: string = 'KRW',
    description?: string
  ): Promise<RecordResponse | null> => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.post<RecordResponse>('/record', {
        merchant,
        amount,
        currency,
        category,
        description,
        transaction_date: new Date().toISOString(),
        record_on_blockchain: true,
      });

      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Recording failed';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { recordTransaction, loading, error };
}
```

## 📊 거래 조회 및 차트 표시

```typescript
// hooks/useTransactions.ts
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { TransactionListResponse } from '@/types/api';

export function useTransactions(category?: string) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        if (category) params.append('category', category);

        const response = await apiClient.get<TransactionListResponse>(
          `/transactions?${params.toString()}`
        );

        setTransactions(response.items);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch transactions';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [category]);

  return { transactions, loading, error };
}
```

### Chart.js 통합

```typescript
// components/ExpenseChart.tsx
import { View } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useTransactions } from '@/hooks/useTransactions';

export function ExpenseChart() {
  const { transactions } = useTransactions();

  // 카테고리별 지출 합계 계산
  const categoryTotals: Record<string, number> = {};
  transactions.forEach((tx) => {
    if (!categoryTotals[tx.category]) {
      categoryTotals[tx.category] = 0;
    }
    categoryTotals[tx.category] += tx.amount;
  });

  const data = {
    labels: Object.keys(categoryTotals),
    datasets: [
      {
        data: Object.values(categoryTotals),
        color: (opacity = 1) => `rgba(26, 255, 146, ${opacity})`,
        strokeWidth: 2,
      },
    ],
  };

  return (
    <View>
      <LineChart
        data={data}
        width={350}
        height={220}
        chartConfig={{
          backgroundColor: '#ffffff',
          backgroundGradientFrom: '#ffffff',
          backgroundGradientTo: '#ffffff',
          color: (opacity = 1) => `rgba(26, 255, 146, ${opacity})`,
          labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
          style: { borderRadius: 16 },
        }}
        bezier
      />
    </View>
  );
}
```

## 💰 예산 상태 조회

```typescript
// hooks/useBudgetStatus.ts
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { BudgetStatusResponse } from '@/types/api';

export function useBudgetStatus(monthYear: string) {
  const [budgets, setBudgets] = useState<BudgetStatusResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBudgetStatus = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get<BudgetStatusResponse[]>(
          `/budgets/${monthYear}`
        );
        setBudgets(response);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch budgets';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchBudgetStatus();
  }, [monthYear]);

  return { budgets, loading, error };
}
```

### 예산 상태 표시

```typescript
// components/BudgetStatus.tsx
import { View, Text, ScrollView } from 'react-native';
import { useBudgetStatus } from '@/hooks/useBudgetStatus';

export function BudgetStatus() {
  const currentMonth = new Date().toISOString().slice(0, 7);
  const { budgets } = useBudgetStatus(currentMonth);

  return (
    <ScrollView>
      {budgets.map((budget) => (
        <View key={budget.category} className="bg-surface p-4 rounded-lg mb-3">
          <Text className="text-lg font-bold text-foreground">
            {budget.category}
          </Text>
          
          {/* 진행률 바 */}
          <View className="bg-border rounded-full h-2 mt-2 overflow-hidden">
            <View
              className={`h-full ${
                budget.status === 'exceeded' ? 'bg-error' :
                budget.status === 'warning' ? 'bg-warning' :
                'bg-success'
              }`}
              style={{
                width: `${Math.min(budget.percentage_used, 100)}%`,
              }}
            />
          </View>

          <View className="flex-row justify-between mt-2">
            <Text className="text-sm text-muted">
              ₩{budget.spent_amount.toLocaleString()} / ₩{budget.budget_amount.toLocaleString()}
            </Text>
            <Text className="text-sm text-muted">
              {budget.percentage_used.toFixed(1)}%
            </Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}
```

## 🔗 XRPL 트랜잭션 조회

```typescript
// hooks/useXRPLTransaction.ts
import { useState } from 'react';
import { apiClient } from '@/lib/api';

export function useXRPLTransaction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getTransaction = async (txHash: string) => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/xrpl/transactions/${txHash}`);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch transaction';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { getTransaction, loading, error };
}
```

## 🌍 환경 변수 설정

### .env 파일

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=true
```

### app.config.ts 업데이트

```typescript
const env = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  // ... 기타 설정
};
```

## 🧪 테스트 예시

### 전체 흐름 테스트

```typescript
// __tests__/integration.test.ts
import { useClassify } from '@/hooks/useClassify';
import { useRecordTransaction } from '@/hooks/useRecordTransaction';

describe('Frontend-Backend Integration', () => {
  it('should classify payment and record transaction', async () => {
    const { classifyText } = useClassify();
    const { recordTransaction } = useRecordTransaction();

    // 1. 분류
    const classified = await classifyText('[신한카드] 스타벅스 ₩5,500 승인');
    expect(classified?.merchant).toBe('스타벅스');
    expect(classified?.category).toBe('food');

    // 2. 기록
    const recorded = await recordTransaction(
      classified!.merchant,
      classified!.amount,
      classified!.category
    );
    expect(recorded?.transaction_id).toBeDefined();
    expect(recorded?.xrpl_tx_hash).toBeDefined();
  });
});
```

## 📱 모바일 최적화

### 이미지 업로드 (영수증 OCR)

```typescript
// hooks/useImageUpload.ts
import * as ImagePicker from 'expo-image-picker';
import { useClassify } from './useClassify';

export function useImageUpload() {
  const { classifyImage } = useClassify();

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 1,
    });

    if (!result.canceled) {
      const base64 = await FileSystem.readAsStringAsync(
        result.assets[0].uri,
        { encoding: 'base64' }
      );
      
      const classified = await classifyImage(base64);
      return classified;
    }
  };

  return { pickImage };
}
```

## 🔐 보안 고려사항

1. **HTTPS 사용**: 프로덕션에서는 HTTPS만 사용
2. **API 키 보호**: 민감한 정보는 환경 변수로 관리
3. **CORS 설정**: 백엔드에서 신뢰할 수 있는 도메인만 허용
4. **Rate Limiting**: API 남용 방지를 위해 Rate Limiting 구현
5. **입력 검증**: 모든 사용자 입력 검증

## 📞 문제 해결

### CORS 오류
```
Access to XMLHttpRequest blocked by CORS policy
```

**해결책**: 백엔드 `config.py`의 `CORS_ORIGINS`에 프론트엔드 URL 추가

### API 타임아웃
```
Request timeout
```

**해결책**: 
- 네트워크 연결 확인
- API 서버 상태 확인 (`/health` 엔드포인트)
- 타임아웃 값 증가 (axios 인스턴스에서 `timeout` 조정)

### 인증 오류
```
401 Unauthorized
```

**해결책**: 
- API 키 확인
- 환경 변수 설정 확인
- 토큰 갱신 로직 구현

## 📚 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [React Native 문서](https://reactnative.dev/)
- [XRPL 개발자 가이드](https://xrpl.org/docs/)
- [Gemini API 문서](https://ai.google.dev/)
