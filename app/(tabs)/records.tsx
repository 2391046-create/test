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
