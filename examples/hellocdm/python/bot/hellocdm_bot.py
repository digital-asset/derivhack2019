# Copyright (c) 2019 Digital Asset (Switzerland) GmbH and/or its affiliates. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import os
import csv
import logging

import dazl
from dazl.model.reading import ContractCreateEvent, InitEvent
from os.path import dirname, join

isLocalDev = True
localEndpoint = "http://localhost:6865"  # Note DAZL talks directly to the Ledger; NOT the HTTP adapter.
owner = 'Alice'

dazl.setup_default_logger(logging.INFO)

def main():
  partyNameMap = {}

  if not isLocalDev:
    print("Fetching party map...")
    partyMapPath = join(dirname(__file__), 'partymap.csv')

    with open(partyMapPath) as csvFile:
      readCSV = csv.reader(csvFile, delimiter=',')
      for row in readCSV:
        partyName, party, _ = row
        partyNameMap[partyName] = party
      print("Done fetching party map!")
  else:
    partyNameMap[owner] = owner

  ownerParty = partyNameMap.get(owner, None)
  if not ownerParty:
    print(f'Could not get party for party name "{owner}". Exiting...')
    exit(1)

  url = localEndpoint if isLocalDev else os.getenv('DAML_LEDGER_URL')

  print(f'Starting a ledger for party {ownerParty!r} ({owner}) on {url}...')
  network = dazl.Network()
  network.set_config(url=url)
  clientOwner = network.aio_party(ownerParty)

  @clientOwner.ledger_init()
  async def onInit(event: InitEvent):
    print("Ready & listening for new `Transfer` contracts ... ")

  @clientOwner.ledger_created("Main.Transfer")  # note: this needs to have a '.' and not a ':'
  async def onCreate(event: ContractCreateEvent):
    allContracts = clientOwner.find(template = "Main.Transfer")
    for contract in allContracts:
      print(contract.cdata["event"]["eventIdentifier"][0]["assignedIdentifier"][0]["identifier"]["value"])
      if contract.cdata["event"]["eventIdentifier"][0]["assignedIdentifier"][0]["identifier"]["value"] == "Hello, CDM!":
        print("I have already greeted contract {}, ignoring.".format(contract.cid))
      else:
        print("Greeting (exercising choice) on contract {}".format(contract.cid))
        clientOwner.submit_exercise(contract.cid, "SayHello", { "whomToGreet" : "CDM"})

  network.run_forever()


if __name__ == '__main__':
  main()
