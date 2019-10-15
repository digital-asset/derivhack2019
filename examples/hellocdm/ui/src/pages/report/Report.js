import React from "react";
import Contracts from "../../components/Contracts/Contracts";
import { useLedgerDispatch, useLedgerState, getContracts, sendCommand, fetchContracts } from "../../context/LedgerContext";
import { useUserState } from "../../context/UserContext";

export default function Report() {

  const user = useUserState();
  const ledger = useLedgerState();
  const ledgerDispatch = useLedgerDispatch();
  const transfers = getContracts(ledger, "Main", "Transfer");

  const exerciseChoice = async (c, whomToGreet) => {
    const command = {
      templateId: { moduleName: "Main", entityName: "Transfer" },
      contractId: c.contractId,
      choice: "SayHello",
      argument: { whomToGreet },
      meta: { ledgerEffectiveTime: 0 }
    };
    await sendCommand(ledgerDispatch, user.token, user.party, "exercise", command, () => {}, () => {});
    await fetchContracts(ledgerDispatch, user.token, () => {}, () => {});
  }

  return (
    <>
      <Contracts
        contracts={transfers}
        columns={[
          ["ContractId", "contractId"],
          ["Identifier", "argument.event.eventIdentifier.0.assignedIdentifier.0.identifier.value"],
          ["Version", "argument.event.eventIdentifier.0.assignedIdentifier.0.version"],
          ["Amount", "argument.event.primitive.transfer.0.cashTransfer.0.amount.amount"],
          ["Ccy", "argument.event.primitive.transfer.0.cashTransfer.0.amount.currency.value"],
          ["Payer", "argument.event.primitive.transfer.0.cashTransfer.0.payerReceiver.payerPartyReference.externalReference"],
          ["Receiver", "argument.event.primitive.transfer.0.cashTransfer.0.payerReceiver.receiverPartyReference.externalReference"],
        ]}
        actions={[["Say Hello", exerciseChoice, "Whom to greet"]]}
      />
    </>
  );
}
