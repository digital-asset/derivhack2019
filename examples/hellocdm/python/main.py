# Copyright (c) 2019 Digital Asset (Switzerland) GmbH and/or its affiliates. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import csv
import json
import requests
import uuid
import time

isLocalDev = True
owner = "Alice"
localToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsZWRnZXJJZCI6ImhlbGxvY2RtIiwiYXBwbGljYXRpb25JZCI6ImZvb2JhciIsInBhcnR5IjoiQWxpY2UifQ.SY9x-Eh_mnPJwKzn4UXvHgtDSbFCRWZFqv0HgaGeXNI"
epoch = 0 # millis from epoch
localEndpoint = "http://localhost:7575"
dablEndpoint = "https://api.projectdabl.com/data"
metadataFileName = "../../resources/CDM.json"
cdmEventFileName = "CashTransfer.json"

endpoint = ''
ledgerID = ''
partyMap = {}
partyNameMap = {}


def loadCDMFile(fileName):

  """Opens a file containing a CDM JSON instance, and decodes into a Python
     dictionary."""

  with open(fileName) as cdmJsonString:
    return json.load(cdmJsonString)

def validateCDMJson(cdmDict, className, rosettaUsername, rosettaAuthToken):

  """Sends a CDM message to the Regnosys validation service, returning HTTP code."""

  return requests.post(
    f"https://ui.rosetta-technology.io/api/promoted/validation/{rosettaUsername}/derivhack2019/latest/{className}",
    headers = {"Authorization" : rosettaAuthToken},
    json = cdmDict
  )

def convertCDMJsonToDAMLJson(cdmDict):

  """Given a CDM dict, convert it into a dict that can be understood by the
     DAML HTTP REST service"""

  from message_integration.metadata.cdm.cdmMetaDataReader import CdmMetaDataReader
  from message_integration.metadata.damlTypes import Record
  from message_integration.strategies.jsonCdmDecodeStrategy import JsonCdmDecodeStrategy
  from message_integration.strategies.jsonCdmEncodeStrategy import JsonCdmEncodeStrategy

  with open(metadataFileName) as metadataRaw:
    metadata = CdmMetaDataReader().fromJSON(json.load(metadataRaw))
    return JsonCdmDecodeStrategy(metadata).decode(cdmDict, Record("Event"))

def writeDAMLJsonToLedger(damlDict, contractName, signatoryName, httpEndpointPrefix):

  """Given a dict containing a DAML contract, load to the ledger via the HTTP
     REST service. Return resulting HTTP response."""

  singatoryParty = partyNameToParty(signatoryName)
  token = partyNameToToken(signatoryName)
  tokenHeader = {
    'Authorization': f'Bearer {token}',
    'X-DA-Party': singatoryParty
    }

  return requests.post(
    f"{endpoint}/command/create",
    headers = tokenHeader,
    json = {
      "templateId" : {
        "moduleName": "Main",
        "entityName": contractName
      },
      "meta" : {
        "ledgerEffectiveTime": epoch # Wall time unsupported on DABL
      },
      "argument": {
        "event": damlDict,
        "owner": singatoryParty,
        "obs": singatoryParty
      }
    },
    verify=False
  )

def readDAMLJsonFromLedger(contractName, signatoryName, httpEndpointPrefix):

  """Given the contract name, query ledger for all such contracts, returning
     the HTTP response, with a monkey patched `contract` accessor."""

  token = partyNameToToken(signatoryName)
  tokenHeader = {
    'Authorization': f'Bearer {token}',
  }

  response = requests.post(
    f"{endpoint}/contracts/search",
    headers = tokenHeader,
    json = {
      "%templates" : [
        {
          "moduleName" : "Main",
          "entityName" : contractName
        }
      ]
    },
    verify=False
  )

  if response.status_code == 200:
    result = response.json()["result"]
    response.contractId = result[0]["contractId"] if result else None

  return response

def exerciseChoice(controllerName, contractIdToExerciseOn, choiceName, choiceArguments, httpEndpointPrefix):

  """Exercises 'SayHello' on a CashTransfer contract.
  This sets the `contract.eventIdentifier.assignedIdentifier.identifier.value`
  to the given text, and increments the `version` by one.
  Return the updated contract:
  """

  controllerParty = partyNameToParty(controllerName)
  token = partyNameToToken(controllerName)
  tokenHeader = {
    'Authorization': f'Bearer {token}',
    'X-DA-Party': controllerParty
    }

  return requests.post(
    f"{endpoint}/command/exercise",
    headers = tokenHeader,
    json = {
      "meta" : {
        "ledgerEffectiveTime": epoch # Wall time unsupported on DABL
      },
      "templateId" : {
        "moduleName" : "Main",
        "entityName" : "Transfer",
      },
      "contractId": contractIdToExerciseOn,
      "choice": choiceName,
      "argument": choiceArguments,
    },
    verify=False
  )

def partyToPartyName(party):
  partyData = partyMap.get(party, None)
  if not partyData:
    raise Exception(f'Could not translate party "{party}" to a party name')
  return partyData['partyName']

def partyNameToParty(partyName):
  partyData = partyNameMap.get(partyName, None)
  if not partyData:
    raise Exception(f'Could not translate party name "{partyName}" to a party')
  return partyData['party']

def partyToToken(party):
  partyData = partyMap.get(party, None)
  if not partyData:
    raise Exception(f'Could not fetch party JWT from party "{party}"')
  return partyData['jwt']

def partyNameToToken(partyName):
  partyData = partyNameMap.get(partyName, None)
  if not partyData:
    raise Exception(f'Could not fetch party JWT from party name "{partyName}"')
  return partyData['jwt']


if __name__ == '__main__' :
  parser = argparse.ArgumentParser("Hello CDM")
  parser.add_argument('-d', '--local_dev', action='store_true')
  parser.add_argument('-l', '--ledger_id', type=str, help="The DABL Ledger ID")
  parser.add_argument('-p', '--party_map', type=str, help="Path to a .csv file containing a list of DABL partyName,party,jwt (no header)")
  parser.add_argument('-u', '--rosetta_user', type=str, help="Rosetta validation service user name.")
  parser.add_argument('-t', '--rosetta_token', type=str, help="Rosetta validation service authorization token.")
  args = parser.parse_args()
  if not args.local_dev and (not args.ledger_id or not args.party_map):
    parser.error('Please provide a ledger ID and a path to partymap.csv when connecting to DABL')

  isLocalDev = args.local_dev
  ledgerID = args.ledger_id
  endpoint = localEndpoint if isLocalDev else f'{dablEndpoint}/{ledgerID}'

  if args.party_map:
    with open(args.party_map) as csvFile:
      readCSV = csv.reader(csvFile, delimiter=',')
      for row in readCSV:
        partyName, party, jwt = row
        data = {'partyName': partyName, 'party': party, 'jwt': jwt}
        partyMap[party] = data
        partyNameMap[partyName] = data
  else:
    data = {'partyName': owner, 'party': owner, 'jwt': localToken}
    partyMap[owner] = data
    partyNameMap[owner] = data

  print(f"#### Loading CDM JSON from {cdmEventFileName} ####")
  cdmJson = loadCDMFile(cdmEventFileName)
  cdmJson["meta"]["globalKey"] = str(uuid.uuid4()) # We overwrite the globalKey, to avoid DAML key clashes, allowing us to reload the same contract many times.
  print("Loaded the following JSON object:")
  print(cdmJson)

  if (args.rosetta_user and args.rosetta_token):
    print(f"#### Sending model to Rosetta validation service ####")
    httpValidateResponse = validateCDMJson(cdmJson, "Event", args.rosetta_user, args.rosetta_token)
    if httpValidateResponse.status_code != 200 or len(httpValidateResponse.json()) != 0:
      print("Rosetta validation failed:")
      print(httpValidateResponse.json())
      exit(1)
  else:
    print("#### Skipping Rosetta validation (provide -u and -t to enable) ####")

  print("#### Converting to DAML JSON, wrapping in an 'Transfer' contract ####")
  damlJson = convertCDMJsonToDAMLJson(cdmJson)
  print("Resulting JSON object:")
  print(damlJson)

  print("#### Sending Transfer contract to ledger ####")
  httpCreateResponse = writeDAMLJsonToLedger(damlJson, "Transfer", owner, endpoint)
  print("HTTP service responded: {}".format(httpCreateResponse))

  if httpCreateResponse.status_code == 200:
    print("#### Reading back Transfer contracts from Ledger ####")
    httpContractsResponse = readDAMLJsonFromLedger("Transfer", owner, endpoint)
    print("HTTP service responded: {}".format(httpContractsResponse))

    if httpContractsResponse.status_code == 200 and httpContractsResponse.contractId:
      print("#### Exercising `SayHello` on the first `CashTransfer` contract ####")
      httpExerciseResponse = exerciseChoice(owner, httpContractsResponse.contractId, "SayHello", { "whomToGreet" : "world!" }, endpoint)
      print("HTTP service responded: {}".format(httpExerciseResponse))
      if httpExerciseResponse.status_code != 200:
        print(httpExerciseResponse.json())

    else:
      print("#### Failed trying to fetch the new contract ###")
      print(httpContractsResponse.json())

  else:
    print("There was a problem creating the contract:")
    print(httpCreateResponse.json())
