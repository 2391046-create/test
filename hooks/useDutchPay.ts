import { useState } from "react";
import { DutchPaySettlement, DutchPayMember } from "@/types";

export function useDutchPay() {
  const [members, setMembers] = useState<DutchPayMember[]>([]);
  const [totalAmount, setTotalAmount] = useState(0);

  const addMember = (name: string) => {
    const newMember: DutchPayMember = {
      name,
      amount_paid: 0,
      should_pay: 0,
      settlement: 0,
    };
    setMembers([...members, newMember]);
  };

  const removeMember = (index: number) => {
    setMembers(members.filter((_, i) => i !== index));
  };

  const updateMemberPaid = (index: number, amount: number) => {
    const updated = [...members];
    updated[index].amount_paid = amount;
    setMembers(updated);
  };

  const setTotal = (amount: number) => {
    setTotalAmount(amount);
  };

  const calculateSettlement = (): DutchPaySettlement => {
    const numPeople = members.length;
    const perPerson = numPeople > 0 ? totalAmount / numPeople : 0;

    // 각 사람이 얼마를 더 내야 하거나 받아야 하는지 계산
    const updatedMembers = members.map((member) => ({
      ...member,
      should_pay: perPerson,
      settlement: member.amount_paid - perPerson,
    }));

    // 정산 계산 (누가 누구에게 얼마를 줄 것인가)
    const settlements: Array<{ from: string; to: string; amount: number }> = [];

    // 받을 사람들 (settlement < 0)
    const debtors = updatedMembers.filter((m) => m.settlement < 0);
    // 줄 사람들 (settlement > 0)
    const creditors = updatedMembers.filter((m) => m.settlement > 0);

    for (const debtor of debtors) {
      let remaining = Math.abs(debtor.settlement);

      for (const creditor of creditors) {
        if (remaining <= 0) break;

        const creditAmount = creditor.settlement;
        if (creditAmount <= 0) continue;

        const transferAmount = Math.min(remaining, creditAmount);
        settlements.push({
          from: debtor.name,
          to: creditor.name,
          amount: Math.round(transferAmount * 100) / 100,
        });

        creditor.settlement -= transferAmount;
        remaining -= transferAmount;
      }
    }

    return {
      total_amount: totalAmount,
      num_people: numPeople,
      per_person: perPerson,
      members: updatedMembers,
      settlements,
    };
  };

  const reset = () => {
    setMembers([]);
    setTotalAmount(0);
  };

  return {
    members,
    totalAmount,
    addMember,
    removeMember,
    updateMemberPaid,
    setTotal,
    calculateSettlement,
    reset,
  };
}
