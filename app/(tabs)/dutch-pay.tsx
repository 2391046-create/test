import { ScrollView, Text, View, TouchableOpacity, TextInput, FlatList, Alert } from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { useDutchPay } from "@/hooks/useDutchPay";
import { useSettings } from "@/hooks/useSettings";
import { useState } from "react";

export default function DutchPayScreen() {
  const { members, totalAmount, addMember, removeMember, updateMemberPaid, setTotal, calculateSettlement, reset } = useDutchPay();
  const { settings } = useSettings();
  const isEn = settings.language === "en";
  const [newMemberName, setNewMemberName] = useState("");
  const [totalInput, setTotalInput] = useState("");
  const [settlement, setSettlement] = useState<ReturnType<typeof calculateSettlement> | null>(null);

  const handleAddMember = () => {
    if (!newMemberName.trim()) {
      Alert.alert(isEn ? "Error" : "오류", isEn ? "Please enter a name" : "이름을 입력해주세요");
      return;
    }
    addMember(newMemberName);
    setNewMemberName("");
  };

  const handleSetTotal = () => {
    const amount = parseFloat(totalInput);
    if (isNaN(amount) || amount <= 0) {
      Alert.alert(isEn ? "Error" : "오류", isEn ? "Please enter a valid amount" : "올바른 금액을 입력해주세요");
      return;
    }
    setTotal(amount);
  };

  const handleCalculate = () => {
    if (members.length === 0) {
      Alert.alert(isEn ? "Error" : "오류", isEn ? "Add at least one member" : "최소 1명 이상의 인원을 추가해주세요");
      return;
    }
    if (totalAmount === 0) {
      Alert.alert(isEn ? "Error" : "오류", isEn ? "Please enter total amount" : "총액을 입력해주세요");
      return;
    }
    const result = calculateSettlement();
    setSettlement(result);
  };

  const handleReset = () => {
    reset();
    setSettlement(null);
    setTotalInput("");
    setNewMemberName("");
  };

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} className="gap-6">
        {/* 헤더 */}
        <View className="gap-2">
          <Text className="text-3xl font-bold text-foreground">{isEn ? "Split Bill" : "더치페이 정산"}</Text>
          <Text className="text-sm text-muted">{isEn ? "Settle payments fairly among members" : "여러 명의 결제 금액을 공정하게 정산"}</Text>
        </View>

        {/* 총액 입력 */}
        <View className="gap-3">
          <Text className="text-lg font-semibold text-foreground">{isEn ? "Total payment" : "총 결제 금액"}</Text>
          <View className="flex-row gap-2">
            <TextInput
              value={totalInput}
              onChangeText={setTotalInput}
              placeholder={isEn ? "Enter amount (KRW)" : "금액 입력 (원)"}
              keyboardType="decimal-pad"
              className="flex-1 p-3 bg-surface border border-border rounded-lg text-foreground"
              placeholderTextColor="#9BA1A6"
            />
            <TouchableOpacity onPress={handleSetTotal} className="p-3 bg-primary rounded-lg">
              <Text className="font-semibold text-background">{isEn ? "Set" : "설정"}</Text>
            </TouchableOpacity>
          </View>
          {totalAmount > 0 && (
            <Text className="text-sm text-success">✓ {isEn ? "Total" : "총액"}: ₩{totalAmount.toLocaleString()}</Text>
          )}
        </View>

        {/* 인원 추가 */}
        <View className="gap-3">
          <Text className="text-lg font-semibold text-foreground">{isEn ? `Members (${members.length})` : `참가자 (${members.length}명)`}</Text>
          <View className="flex-row gap-2">
            <TextInput
              value={newMemberName}
              onChangeText={setNewMemberName}
              placeholder={isEn ? "Enter name" : "이름 입력"}
              className="flex-1 p-3 bg-surface border border-border rounded-lg text-foreground"
              placeholderTextColor="#9BA1A6"
            />
            <TouchableOpacity onPress={handleAddMember} className="p-3 bg-primary rounded-lg">
              <Text className="font-semibold text-background">{isEn ? "Add" : "추가"}</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 참가자 목록 */}
        {members.length > 0 && (
          <View className="gap-2">
            {members.map((member, index) => (
              <View key={index} className="p-4 bg-surface rounded-lg border border-border flex-row items-center justify-between">
                <View className="flex-1">
                  <Text className="font-semibold text-foreground">{member.name}</Text>
                  <View className="flex-row gap-3 mt-2">
                    <View className="flex-1">
                      <Text className="text-xs text-muted">{isEn ? "Paid amount" : "낸 금액"}</Text>
                      <TextInput
                        value={member.amount_paid.toString()}
                        onChangeText={(val) => updateMemberPaid(index, parseFloat(val) || 0)}
                        placeholder="0"
                        keyboardType="decimal-pad"
                        className="p-2 bg-background border border-border rounded mt-1 text-foreground text-sm"
                        placeholderTextColor="#9BA1A6"
                      />
                    </View>
                  </View>
                </View>
                <TouchableOpacity
                  onPress={() => removeMember(index)}
                  className="p-2 bg-error rounded-lg ml-2"
                >
                  <Text className="text-background font-bold">×</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {/* 계산 버튼 */}
        {members.length > 0 && totalAmount > 0 && !settlement && (
          <TouchableOpacity onPress={handleCalculate} className="p-4 bg-primary rounded-lg">
            <Text className="text-center font-semibold text-background text-lg">{isEn ? "Calculate split" : "정산 계산"}</Text>
          </TouchableOpacity>
        )}

        {/* 정산 결과 */}
        {settlement && (
          <View className="gap-4">
            <Text className="text-lg font-semibold text-foreground">{isEn ? "Settlement result" : "정산 결과"}</Text>

            {/* 1인당 금액 */}
            <View className="p-4 bg-primary rounded-lg">
              <Text className="text-sm text-background">{isEn ? "Per person" : "1인당 부담액"}</Text>
              <Text className="text-3xl font-bold text-background mt-1">
                ₩{Math.round(settlement.per_person).toLocaleString()}
              </Text>
            </View>

            {/* 정산 내역 */}
            {settlement.settlements.length > 0 ? (
              <View className="gap-2">
                <Text className="text-base font-semibold text-foreground">{isEn ? "Settlement details" : "정산 내역"}</Text>
                {settlement.settlements.map((s, index) => (
                  <View key={index} className="p-3 bg-surface rounded-lg border border-border">
                    <Text className="text-sm text-foreground">
                      <Text className="font-bold">{s.from}</Text>
                      {" → "}
                      <Text className="font-bold">{s.to}</Text>
                    </Text>
                    <Text className="text-lg font-bold text-primary mt-1">
                      ₩{Math.round(s.amount).toLocaleString()}
                    </Text>
                  </View>
                ))}
              </View>
            ) : (
              <View className="p-4 bg-success rounded-lg">
                <Text className="text-center text-background font-semibold">
                  {isEn ? "Everyone paid equally ✓" : "모두 동일한 금액을 냈습니다 ✓"}
                </Text>
              </View>
            )}

            {/* 액션 버튼 */}
            <View className="gap-2">
              <TouchableOpacity className="p-4 bg-primary rounded-lg">
                <Text className="text-center font-semibold text-background">{isEn ? "💾 Save" : "💾 저장하기"}</Text>
              </TouchableOpacity>

              <TouchableOpacity onPress={handleReset} className="p-4 bg-surface border border-border rounded-lg">
                <Text className="text-center font-semibold text-foreground">{isEn ? "Recalculate" : "다시 계산"}</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}
