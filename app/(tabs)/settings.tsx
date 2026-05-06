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
