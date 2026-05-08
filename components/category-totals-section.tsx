import { Text, View } from 'react-native';

import { summarizeByCategory, Transaction } from '@/lib/finance';

type Props = {
  transactions: Transaction[];
  isEn: boolean;
};

const CATEGORY_LABEL_EN: Record<string, string> = {
  food: 'Food',
  transport: 'Transport',
  housing: 'Housing',
  study: 'Study',
  shopping: 'Shopping',
  health: 'Health',
  transfer: 'Transfer',
  other: 'Other',
};

export function CategoryTotalsSection({ transactions, isEn }: Props) {
  const locale = isEn ? 'en-US' : 'ko-KR';
  const rows = summarizeByCategory(transactions);
  const total = rows.reduce((sum, row) => sum + row.amount, 0);

  return (
    <View className="gap-3">
      <Text className="text-lg font-bold text-foreground">{isEn ? 'Totals by category' : '카테고리별 합계'}</Text>
      {rows.length === 0 ? (
        <View className="rounded-2xl bg-surface border border-border p-4">
          <Text className="text-sm text-muted">{isEn ? 'No categorized transactions yet' : '분류된 거래가 아직 없습니다'}</Text>
        </View>
      ) : (
        rows.map((item) => {
          const percent = total > 0 ? Math.round((item.amount / total) * 100) : 0;
          const label = isEn ? (CATEGORY_LABEL_EN[item.category.id] ?? item.category.label) : item.category.label;
          return (
            <View key={item.category.id} className="rounded-2xl bg-surface border border-border p-4">
              <View className="flex-row items-center justify-between">
                <View className="flex-row items-center gap-3">
                  <View style={{ backgroundColor: item.category.tone }} className="h-4 w-4 rounded-full" />
                  <View>
                    <Text className="text-base font-bold text-foreground">{label}</Text>
                    <Text className="text-xs text-muted">{isEn ? `${item.count} items · ${percent}% of total` : `${item.count}건 · 전체 ${percent}%`}</Text>
                  </View>
                </View>
                <Text className="text-base font-bold text-foreground">₩{Math.round(item.amount).toLocaleString(locale)}</Text>
              </View>
              <View className="mt-3 h-2 overflow-hidden rounded-full bg-background">
                <View style={{ width: `${Math.min(percent, 100)}%`, backgroundColor: item.category.tone }} className="h-2 rounded-full" />
              </View>
            </View>
          );
        })
      )}
    </View>
  );
}
