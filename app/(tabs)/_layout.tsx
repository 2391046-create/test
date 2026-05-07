import { Tabs } from 'expo-router';
import { Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useColors } from '@/hooks/use-colors';

export default function TabLayout() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const bottomPadding = Platform.OS === 'web' ? 12 : Math.max(insets.bottom, 10);
  const tabBarHeight = 62 + bottomPadding;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.tint,
        tabBarInactiveTintColor: colors.muted,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarLabelStyle: { fontSize: 10, fontWeight: '600', marginTop: 2 },
        tabBarStyle: {
          paddingTop: 8,
          paddingBottom: bottomPadding,
          height: tabBarHeight,
          backgroundColor: colors.background,
          borderTopColor: colors.border,
          borderTopWidth: 0.5,
        },
      }}
    >
      <Tabs.Screen name="index" options={{ title: '홈', tabBarIcon: ({ color }) => <IconSymbol size={26} name="house.fill" color={color} /> }} />
      <Tabs.Screen name="records" options={{ title: '기록', tabBarIcon: ({ color }) => <IconSymbol size={26} name="list.bullet.rectangle.fill" color={color} /> }} />
      <Tabs.Screen name="receipt-scanner" options={{ title: '영수증', tabBarIcon: ({ color }) => <IconSymbol size={26} name="doc.text.image.fill" color={color} /> }} />
      <Tabs.Screen name="menu-scanner" options={{ title: '가격분석', tabBarIcon: ({ color }) => <IconSymbol size={26} name="chart.bar.fill" color={color} /> }} />
      <Tabs.Screen name="rates" options={{ title: '환율', tabBarIcon: ({ color }) => <IconSymbol size={26} name="chart.line.uptrend.xyaxis" color={color} /> }} />
      <Tabs.Screen name="wallet" options={{ title: '지갑', tabBarIcon: ({ color }) => <IconSymbol size={26} name="creditcard.fill" color={color} /> }} />
      <Tabs.Screen name="settings" options={{ title: '설정', tabBarIcon: ({ color }) => <IconSymbol size={26} name="gearshape.fill" color={color} /> }} />
      <Tabs.Screen name="dutch-pay" options={{ href: null }} />
      <Tabs.Screen name="rules" options={{ href: null }} />
    </Tabs>
  );
}
