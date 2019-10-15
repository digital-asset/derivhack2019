import React from "react";
import Contracts from "../../components/Contracts/Contracts";
import { useLedgerDispatch, useLedgerState, getContracts, sendCommand, fetchContracts } from "../../context/LedgerContext";
import { useUserState } from "../../context/UserContext";

export default function Greeter() {

  const user = useUserState();
  const ledger = useLedgerState();
  const ledgerDispatch = useLedgerDispatch();
  const greeters = getContracts(ledger, "Sample", "Greeter");

  const exerciseChoice = async (c, to, message) => {
    const command = {
      templateId: { moduleName: "Sample", entityName: "Greeter" },
      contractId: c.contractId,
      choice: "SayHello",
      argument: { to, message },
      meta: { ledgerEffectiveTime: 0 }
    };
    await sendCommand(ledgerDispatch, user.token, user.party, "exercise", command, () => {}, () => {});
    await fetchContracts(ledgerDispatch, user.token, () => {}, () => {});
  }

  return (
    <>
      <Contracts
        contracts={greeters}
        columns={[
          ["ContractId", "contractId"],
          ["Party", "argument.party"],
        ]}
        actions={[["Say Hello", exerciseChoice, "To", "Message"]]}
      />
    </>
  );
}
