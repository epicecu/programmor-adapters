<div align="center">

<img src="support/epicecu-programmor-logo.png" alt="EpicECU Programmor Adapters" width="400" />

##### An open source tuning software communication adapters

</div>

[![Tests](https://github.com/epicecu/programmor/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/epicecu/programmor/actions/workflows/tests.yml)

## Install

Clone the repo and install dependencies:

Linux/Mac

```bash
git clone --branch master https://github.com/epicecu/programmor.git
cd programmor
make venv
make install-dev
```

Windows

```bash
git clone --branch master https://github.com/epicecu/programmor.git
cd programmor
virtualenv venv
venv\Scripts\activate
pip install -e .
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

## Starting Development

Set the `PROGRAMMOR_PROTO_FILE` environment variable to override the default behaviour for local testing
with hardware development. This may be useful when the hardware repo may not be public yet and can not
access the proto file via http get.

Linux/Mac

```bash
make run
```

Windows

```bash
venv\Scripts\activate
python src/programmor
```

Qt Designer on Windows: designer.exe

## Compiling the Protobuf files

```bash
make compile-proto
```

Windows
```bash
protoc.exe --python_out=. src/programmor/proto/transaction.proto
```

## Styles

Check the code style by running flake8

```bash
make check-style
```

Check and apply style alternation to the source files. Update the last line option to select a file to process

```bash
make style
```

## Run tests

```bash
make test
```

Note: Your system will need to have the 3.10 python environment installed
```bash
make tox
```

## Type Checking

Type checking is currently disable in the tox test pipeline

```bash
make check-type
```

## Packaging for Production

To package apps for the local platform:

```bash
todo
```

## Docs

See our [docs and guides here](https://epicecu.com/programmor/docs/installation)

## Donations

**Donations will ensure the following:**

- 🔨 Long term maintenance of the project
- 🛣 Progress on the [roadmap](https://epicecu.com/programmor/docs/roadmap)
- 🐛 Quick responses to bug reports and help requests

## Maintainers

- [David Cedar](https://github.com/devvid)

## License

GPL V2 © [Programmor](https://github.com/epicecu/programmor)

## Tasks to do

- Properlly close the session when exit is clicked for session, this includes closing the serial connection.
- Fix "defaultPin" for connection being send and over ridding user selected configuration. Actually, the default should be set on the device, the gui should just display currect values and allow to update.
    - This has now been fixed
- Fix the receive handler to better support messages spread over multiple data packets. Currently updated so system fits all data in single frame, this works for now but does not guarantee working order on other pc's, setups. 
    - This has now been fixed
- The hardware seems to lock up on 8/9 x refreshes on the main page. I have traced it down to opening and closing the usb connection too many times, needs more investigation.