<div align="center">

<img src="support/epicecu-programmor-logo.png" alt="EpicECU Programmor Adapters" width="400" />

##### An open source tuning software communication adapter collection

</div>

[![Tests](https://github.com/epicecu/programmor/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/epicecu/programmor/actions/workflows/tests.yml)

## Notes
- The Gevent webserver is prefered over the eventlet server due to the server emit function failing to work and causing the server to restart, generating a new session id.  

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

```bash
make run
```
## Compiling the Protobuf files

```bash
make compile-proto
```

## Run tests

```bash
make test
```

Note: Your system will need to have the 3.10 python environment installed
```bash
make tox
```

## Packaging for Production

To package apps for the local platform:

```bash
todo
```

## Docs

While in the python virtual environment, navigate to `/documentation` and run the command `make html`
View the docs in the browser by running `python3 -m http.server -d build/html`

### Communications Flow Chart

![Communications Flow Diagram](support/communications-flow-diagram.png)

## Donations

**Donations will ensure the following:**

- 🔨 Long term maintenance of the project
- 🛣 Progress on the [roadmap](https://epicecu.com/programmor/roadmap)
- 🐛 Quick responses to bug reports and help requests

## Maintainers

- [David Cedar](https://github.com/devvid)

## License

GPL V2 © [Programmor](https://github.com/epicecu/programmor)

## Todo

1. When messages are received from the device, the emit and receive on the HMI side takes too long to complete
2. Test with multiple USB devices connected
3. Test on Windows 10, 11
4. Test on Mac
