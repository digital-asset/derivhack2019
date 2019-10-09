# Hello CDM

This project shows you how to write a simple 'hello world' application that loads a CDM contract onto the ledger, exercises a choice, and reads it back. The application can run against a local environment or [project:DABL](https://projectdabl.com/)

## Prerequisites
* [DAML SDK](https://docs.daml.com/getting-started/installation.html)
* [Python 3.7](https://www.python.org/downloads/)
* [Pipenv](https://pipenv.kennethreitz.org/en/latest/install/#installing-pipenv)
* [Yarn](https://yarnpkg.com/lang/en/docs/install/) (Only required for react UI)

## Quickstart for project:DABL

Compile the DAML model, fetch Python dependencies:

```sh
daml build
pipenv install ../../resources/message_integration-0.0.1-py3-none-any.whl
```
Locate the `.daml/dist/hellocdm-0.0.1.dar` and upload it to DABL.

### Create your DABL Ledger

Create a DABL project and ledger and deploy your dar file to your ledger.

> ℹ️ Note: if you are uncertain of how to create and deploy in DABL you can check out the [docs](https://docs.projectdabl.com/)

Go to your ledger and in the Live Data tab, click on `Add Party` and add `Alice` as a party.

### Run the main program against DABL

Go to the Ledger Settings tab and in the General section download the Party Map as a `.csv`

Copy the `partymap.csv` file you just downloaded to the [`python/bot/`](python/bot/) directory.

Run `main.py` by replacing the `-l` argument with the Ledger ID of your DABL Ledger:

> ℹ️ Note: You can find your Ledger ID in the Ledger Settings tab

```sh
pipenv run python python/main.py -l yourledgerid -p python/bot/partymap.csv
```

### Run the bot against DABL

In `python/bot/hellocdm_bot.py` switch the `isLocalDev` flag to `False`

Package the bot into a `tar.gz` source distribution

```sh
make clean && make package
```

Locate the `target/artifacts/hello-cdm-0.1.tar.gz` file and upload it to DABL.

Deploy it to your ledger.

### Verify that the bot is working

> ⚠️ Warning: this section will soon be replaced with functionality available in the Automation tab in your DABL Ledger. For the time being feel free to use this workaround

In you Live Data tab under the Ledger Admin party check if a new `DABL.Artifact:DeployedArtifact` contract has been created. In the `metadata` object of your contract data should look something like this:

```json
"metadata": {
  "com.projectdabl.k8s.apiVersion": "dabl.com/v1",
  "com.projectdabl.k8s.kind": "PythonBot",
  "com.projectdabl.k8s.metadata.name": "fn8ppsbdsn3417tz",
  "com.projectdabl.pythonbot.party": "dabl_admin-k0d0s88jaumjx482"
}
```

If you want to check the log output of your bot you can `curl` the following endpoint using the Ledger Admin party JWT as the Bearer token:

```sh
https://api.projectdabl.com/api/ledger/[ledgerID]/bots/[botID]/logs
```

Where `ledgerID` is your DABL Ledger ID and `botID` is the `com.projectdabl.k8s.metadata.name` property of your bot. _(in this example `fn8ppsbdsn3417tz`)_

> ✅ Tip: You can form a `curl` command for the Ledger Admin by going to your Ledger Settings page selecting the Ledger Admin party in the Party JWT field and then `Copy As -> Curl`. Then replace the url with: `https://api.projectdabl.com/api/ledger/[ledgerID]/bots/[botID]/logs`

Finally you can also verify the bot's functionality by creating a new `Main:Transfer` contract for Alice and checking if the bot exercises the `SayHello` choice on it.

### Deleting a bot

> ⚠️ Warning: this section will soon be replaced with functionality available in the Automation tab in your DABL Ledger. For the time being feel free to use this workaround

In you Live Data tab under the Ledger Admin party find the `DABL.Artifact:DeployedArtifact` contract that corresponds to your deployed bot. Select the `Archive` choice and `Submit`. The contract is archived and the bot is deleted from your ledger.


## Quickstart for local environment

Compile the DAML model, fetch Python dependencies:

```sh
daml build
pipenv install ../../resources/message_integration-0.0.1-py3-none-any.whl
```

Load the templates into the ledger:

```sh
daml sandbox --port 6865 --ledgerid hellocdm --static-time .daml/dist/*.dar
```

Start the HTTP rest adapter:

```sh
daml json-api --ledger-host localhost --ledger-port 6865 --http-port 7575 --max-inbound-message-size 52428800
```

Run the main program:

```sh
pipenv run python python/main.py --local_dev
```

In another shell session, run the bot, and then ***re-run*** the main program to trigger some actions:
> ℹ️ Note: make sure that the `isLocalDev` flag in [`hellocdm_bot.py`](python/bot/hellocdm_bot.py) is set to `True`
```sh
pipenv run python python/bot/hellocdm_bot.py
```
```sh
pipenv run python python/main.py --local_dev
```

One of the scripts will emit a `A command submission failed!` message - this is because the two processes are racing to update the contract simultaneously; see the tutorial below for further explanation.

You can now run the reporting UI against the ledger by following the instructions [here](ui/).

## Tutorial

In this section we are going to walk through the app step-by-step. This is also available as a [video recording](https://youtu.be/YRrXoD_wabk).

### Loading the DAML model onto a local ledger

First, have a look at the directory structure:
```sh
hellocdm
├── CashTransfer.json
├── daml
│   ├── Main.daml
│   └── Org/Isda/Cdm
├── daml.yaml
├── Pipfile
├── Pipfile.lock
├── python
│   ├── bot
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── hellocdm_bot.py
│   │   └── partymap.csv
│   ├── main.py
│   ├── MANIFEST.in
│   └── setup.py
├── README.md
└── ui
    ├── package.json
    ├── public
    ├── README.md
    ├── src
    └── yarn.lock
```

You will find our DAML template in `daml/Main.daml`.

```haskell
template Transfer
  with
    event : CDM.Event
    owner : Party
    obs   : Party
  where
    signatory owner
    observer obs

    key (owner, getGlobalKey event) : (Party, Text)
    maintainer key._1

    controller owner can
      SayHello : ContractId Transfer
        with whomToGreet: Text
        do -- Need to project deep field this.contract.eventIdentifier[0].assignedIdentifier[0].value and version
          create this with event = updateIdentifier "CDM" event
```

This is a minimal template, which has only the bare requirements. It has some data, under `event`, and an `owner`, which will be the `signatory`. It has a single choice, `SayHello`, which updates the contract by setting `contract.eventIdentifier[0].assignedIdentifier[0].value` to `Hello, World!`, and incrementing `version`. This is done in a separate function, `update`, of which only the signature is shown above.

The CDM data model describing `CDM.Event`, is under `daml/Org/Isda/Cdm`, but we don't need to worry about it for this for the time being.

Bear in mind that a ledger can only house contracts instantiated from `template`s. Data can not live on it's own on the ledger (by analogy to SQL you must create a record in a table - you can't upload a plain data type).

Now, let's start the ledger and http services:

```sh
daml build
daml sandbox --port 6865 --ledgerid hellocdm --static-time .daml/dist/*.dar
```

The first command compiles our model to bytecode.

The second command will start a ledger locally. It's important that we don't change the `--ledgerid hellocdm`, as this is used for authentication using JWT. It's also important to pass `--static-time`, as DABL does not support wall-clock time, and creation of contracts would fail; this also means that we need to pass a `meta` element in any creation messages to the ledger, which we'll explain in the next section.

Now, let's start the HTTP service, so we can create contracts and query the ledger:

```sh
daml json-api --ledger-host localhost --ledger-port 6865 --http-port 7575 --max-inbound-message-size 52428800
```

Note the `--max-inbound-message-size`, which we require, to be able to process CDM messages. If you forget this, the process will fail with a related message on start-up.

### Talking CDM with the ledger

Now let's have a look at `python/main.py`. It has five methods which correspond to these four steps:

1. `loadCDMFile` simply opens the `CashTransfer.json` file and loads it into a python dictionary. This file would be provided to you in the Hackathon. When this is run in the script, it outputs something like this:

```json
#### Loading CDM JSON from 'CashTransfer.json' ####
Loaded the following JSON object:
{'action': 'NEW', 'eventDate': {'day': 20, 'month': 3, 'year': 2018}, 'eventEffect': {'transfer': [{'globalReference': '69e7b2f5'}]}, 'eventIdentifier': [{'assignedIdentifier': [{'identifier': {'value': 'payment-1'}, 'version': 1}], 'issuerReference': {'globalReference': 'baa9cf67', 'externalReference': 'party1'}, 'meta': {'globalKey': '4576e46b'}}], 'eventQualifier': 'CashTransfer', 'messageInformation': {'messageId': {'value': '1486297', 'meta': {'scheme': 'http://www.party1.com/message-id'}}, 'sentBy': {'value': '894500DM8LVOSCMP9T34'}, 'sentTo': [{'value': '49300JZDC6K840D7F79'}]}, 'meta': {'globalKey': '14801403'}, 'party': [{'meta': {'globalKey': 'baa9cf67', 'externalKey': 'party1'}, 'partyId': [{'value': '894500DM8LVOSCMP9T34', 'meta': {'scheme': 'http://www.fpml.org/coding-scheme/external/iso17442'}}]}, {'meta': {'globalKey': 'a275c2fe', 'externalKey': 'party2'}, 'partyId': [{'value': '549300JZDC6K840D7F79', 'meta': {'scheme': 'http://www.fpml.org/coding-scheme/external/iso17442'}}]}], 'primitive': {'transfer': [{'cashTransfer': [{'amount': {'amount': 1480, 'currency': {'value': 'USD'}, 'meta': {'globalKey': '7c20311f'}}, 'payerReceiver': {'payerPartyReference': {'globalReference': 'baa9cf67', 'externalReference': 'party1'}, 'receiverPartyReference': {'globalReference': 'a275c2fe', 'externalReference': 'party2'}}}], 'meta': {'globalKey': '69e7b2f5'}, 'settlementDate': {'adjustedDate': {'value': {'day': 22, 'month': 3, 'year': 2018}}}}]}, 'timestamp': [{'dateTime': '2018-03-20T18:13:51Z', 'qualification': 'EVENT_CREATION_DATE_TIME'}]}
```

As a side note, we mention that we override the `meta.globalKey` in posterity to avoid key clashes when creating new contracts from the main script.

2. `convertCDMJsonToAdmlJson` changes the schema from the official CDM to be compatible with the ledger HTTP API. Running this would output the following:

```json
#### Converting to DAML JSON, wrapping in an 'Event' contract ####
Resulting JSON object:
{'account': [], 'action': 'ActionEnum_New', 'eventDate': '2018-03-20', 'eventEffect': {'contract': [], 'effectedContract': [], 'effectedExecution': [], 'execution': [], 'productIdentifier': [], 'transfer': [{'globalReference': '69e7b2f5'}]}, 'eventIdentifier': [{'assignedIdentifier': [{'identifier': {'value': 'payment-1'}, 'version': 1}], 'issuerReference': {'globalReference': 'baa9cf67', 'externalReference': 'party1'}, 'meta': {'globalKey': '4576e46b'}}], 'eventQualifier': 'CashTransfer', 'messageInformation': {'copyTo': [], 'messageId': {'value': '1486297', 'meta': {'scheme': 'http://www.party1.com/message-id'}}, 'sentBy': {'value': '894500DM8LVOSCMP9T34'}, 'sentTo': [{'value': '49300JZDC6K840D7F79'}]}, 'meta': {'globalKey': '14801403'}, 'party': [{'meta': {'globalKey': 'baa9cf67', 'externalKey': 'party1'}, 'partyId': [{'value': '894500DM8LVOSCMP9T34', 'meta': {'scheme': 'http://www.fpml.org/coding-scheme/external/iso17442'}}], 'person': []}, {'meta': {'globalKey': 'a275c2fe', 'externalKey': 'party2'}, 'partyId': [{'value': '549300JZDC6K840D7F79', 'meta': {'scheme': 'http://www.fpml.org/coding-scheme/external/iso17442'}}], 'person': []}], 'primitive': {'allocation': [], 'contractFormation': [], 'execution': [], 'inception': [], 'observation': [], 'quantityChange': [], 'reset': [], 'transfer': [{'cashTransfer': [{'amount': {'amount': 1480, 'currency': {'value': 'USD'}, 'meta': {'globalKey': '7c20311f'}}, 'breakdown': [], 'payerReceiver': {'payerPartyReference': {'globalReference': 'baa9cf67', 'externalReference': 'party1'}, 'receiverPartyReference': {'globalReference': 'a275c2fe', 'externalReference': 'party2'}}}], 'commodityTransfer': [], 'meta': {'globalKey': '69e7b2f5'}, 'securityTransfer': [], 'settlementDate': {'adjustedDate': {'value': '2018-03-22'}}}]}, 'timestamp': [{'dateTime': {'dateTime': '2018-03-20T18:13:51Z', 'timezone': 'UTC'}, 'qualification': 'EventTimestampQualificationEnum_eventCreationDateTime'}]}
```
Although both are JSON, the are subtle differences in how the CDM and DAML are encoded. This simply calls an external library to do this conversion for you. Compare for example, the `timestamp` and `qualification` (last two fields) with the output of step one.

3. `writeDAMLJsonToLedger` uses the `requests` library to make an HTTP POST request to create the contract from the previous section. The command is very simple:

```python
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
    }
```

Notable is the `tokenHeader`, which must be passed to authenticate with the HTTP adapter. It is a digest of `argument.owner` and the ledger ID (`hellocdm` for local dev). The token for your local development environment is generated on https://JWT.io following [these instructions](https://docs.daml.com/json-api/index.html#example-session). Without this field, the HTTP adapter will reject the request. In DABL you will be able to download the JWT token as well as the ledger ID from the ledger settings page.

There is also a `meta.ledgerEffectiveTime` member which is not required for the local sandbox, but is mandatory for DABL, which doesn't expose a concept of ledger time. This is used in conjunction with the `--static-time` switch we used to start the ledger in the first section.

Finally, the `argument` is the DAML-encoded CDM message we created in the previous section.

This returns an `HttpResponse` object, which is rendered as the HTTP 200 response code, if everything worked ok. If the call fails, you can call `httpCreateResponse.json()` to render and debug the result.

4. `readDAMLJsonFromLedger` is similar to the previous method. Reads the contracts we just generated back from the sandbox. It posts an argument `%templates` to the HTTP endpoint, which can be used to filter specific types of contracts:

```python
requests.post(
    ...
    json = {
      "%templates" : [
        {
          "moduleName" : "Main",
          "entityName" : contractName
        }
      ]
    }
    ...
```

5. `exerciseChoice` is the final step and is used to exercise the `SayHello` choice on our contract.  Recall this updates the contract identifier to `Hello, ____!` and increments the `version` number. Again, it's very similar to the other HTTP calls. Besides the aforementioned header and meta blocks, it requires a `contractId`, `choice` and `argument` to pass to the DAML choice. In our example, the choice is `SayHello`, and the argument is the greeting message.

```python
  return requests.post(
    ...
    json = {
      ...
      "contractId": contractIdToExerciseOn,
      "choice": choiceName,
      "argument": choiceArguments,
    }
  )
```

Finally, let's test out the script:

```sh
pipenv install ../../resources/message_integration-0.0.1-py3-none-any.whl
pipenv run python python/main.py --local_dev
```

You should see some output from each step as it's executed, showing the HTTP responses. If you inspect the ledger now, you should see some new contracts.

### Workflow Automation

We now turn to the directory `python/bot` which shows how to automate workflows. It uses the python [DAZL](https://github.com/lucianojoublanc-da/dazl-client) API ([docs](https://lucianojoublanc-da.github.io/dazl-client/dazl.client.html#module-dazl.client.api)) to talk directly to the ledger, instead of making HTTP calls.

You'll see the file `python/bot/hellocdm_bot.py` has two annotated methods, which register callbacks:

```python

@clientOwner.ledger_init()
async def onInit(event: InitEvent):
  print("Ready & listening for new `Transfer` contracts ... ")

@clientOwner.ledger_created("Main.Transfer")
async def onCreate(event: ContractCreateEvent):
  allContracts = user.find(template = "Main.Transfer")
  ...
  clientOwner.submit_exercise(contract.cid, "SayHello", { "whomToGreet" : "CDM"})

network.run_forever()
```

The first, `ledger_init` is executed once the API is ready and connected to the ledger.

The second, `ledger_created` is executed whenever a new contract is created on the ledger. In our example, we exercise the same choice we did in our main script, but changed the id to `Hello, CDM!` (instead of `Hello, World!`).

The last line blocks the script and sits in a loop, making the above call-backs each time an event occurs.

We can now start up the script
> ℹ️ Note: make sure that the `isLocalDev` flag in [`hellocdm_bot.py`](python/bot/hellocdm_bot.py) is set to `True` if you are testing in a local environment
```sh
$ pipenv run python python/bot/hellocdm_bot.py
Ready & listening for new `Transfer` contracts ...
```

Now, run the main script again, in a separate shell. The bot should print out something like:
```sh
payment-1
I have already greeted contract ##2:0, ignoring.
Hello, World!
Greeting (exercising choice) on contract # #3:1
payment-1
I have already greeted contract ##2:0, ignoring.
Hello, World!
Greeting (exercising choice) on contract # #3:1
Tried to send a command and failed!
```

The bot checks to see whether it's already greeted each contract (the id should equal "Hello, CDM!" in this case), and if not, it updates it.

Curiously, you'll note that the last line says `Tried to send a command and failed!`. Your script may spew a lot of output or go into an infinite loop.
The reason for this is that _both_ our `main.py` and the `hellocdm_bot.py` are racing to update the same contract. To resolve this, comment out the lines related to

```python
httpExerciseResponse = exerciseChoice(...)
```

Now run the main script again. It should work without errors.

### Reporting UI

You can run the reporting UI against the ledger by following the instructions [here](ui/).
