import argparse
import json
import uuid

metadataFileName = "../../resources/CDM.json"


def loadCDMFile(fileName):

  """Opens a file containing a CDM JSON instance, and decodes into a Python
     dictionary."""

  with open(fileName) as cdmJsonString:
    return json.load(cdmJsonString)


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


def convertCDMFileToDAMLFile(cdmEventFileName, damlEventFileName):
    print(f"#### Loading CDM JSON from {cdmEventFileName} ####")
    cdmJson = loadCDMFile(cdmEventFileName)
    cdmJson["meta"]["globalKey"] = str(uuid.uuid4()) # We overwrite the globalKey, to avoid DAML key clashes, allowing us to reload the same contract many times.
    print("Loaded the following JSON object:")
    print(cdmJson)

    print("#### Converting to DAML JSON, wrapping in an 'Transfer' contract ####")
    damlJson = convertCDMJsonToDAMLJson(cdmJson)
    print("Resulting JSON object:")
    print(damlJson)

    print(f"#### Writing DAML JSON file {damlEventFileName} ####")
    with open(damlEventFileName, 'w') as outfile:
        json.dump(damlJson, outfile, indent=4)

def main():
    parser = argparse.ArgumentParser("CDM/DAML JSON Converter")
    parser.add_argument('-i', '--input', type=str, help="CDM JSON file to convert")
    parser.add_argument('-o', '--output', type=str, help="Name of the output JSON file to write")

    args = parser.parse_args()

    if not args.input:
        parser.error("Please the name of the input JSON file")

    if not args.output:
        parser.error("Please provide the name of the output JSON file")

    cdmEventFileName = args.input
    damlEventFileName = args.output

    convertCDMFileToDAMLFile(cdmEventFileName, damlEventFileName)

if __name__ == '__main__' :
    main()
