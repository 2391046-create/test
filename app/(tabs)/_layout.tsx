import { Tabs } from 'expo-router';
import { Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useColors } from '@/hooks/use-colors';

export default function TabLayout() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const bottomPadding = Platform.OS === 'web' ? 12 : Math.max(insets.bottom, 8);
  const tabBarHeight = 58 + bottomPadding;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.tint,
        tabBarInactiveTintColor: colors.muted,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
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
      <Tabs.Screen name="report" options={{ title: '리포트', tabBarIcon: ({ color }) => <IconSymbol size={26} name="chart.pie.fill" color={color} /> }} />
      <Tabs.Screen name="rates" options={{ title: '환율', tabBarIcon: ({ color }) => <IconSymbol size={26} name="chart.line.uptrend.xyaxis" color={color} /> }} />
      <Tabs.Screen name="settings" options={{ title: '설정', tabBarIcon: ({ color }) => <IconSymbol size={26} name="gearshape.fill" color={color} /> }} />
    </Tabs>
  );
}
