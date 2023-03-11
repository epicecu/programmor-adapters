# help:
# help:	Programmor-Adapter An adapter software for Programmor GUI
# help:

PYTHON_VERSION = python3.11

VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

# help: help					- displays this make file help information
.PHONY: help
help:
	@grep "^# help\:" Makefile | sed 's/\# help\: *//'

# help: run					- starts the application
.PHONY: run
run:
	@echo "Starting Programmor USB Adapter"
	@. ./$(VENV)/bin/activate
	$(PYTHON) -m adapter_usb

# help: venv					- creates a virtual environment
.PHONY: venv
venv:
	@echo "Creating virtual environment"
	$(PYTHON_VERSION) -m venv $(VENV)
	. ./$(VENV)/bin/activate

# help: install					- installs the application
.PHONY: install
install: requirements.txt
	@echo "Installing Application"
	@make venv
	@$(PIP) install -e .
	@$(PIP) install -r requirements.txt

# help: install-dev				- installs the application with development dependencies
.PHONY: install-dev
install-dev: requirements_dev.txt
	@echo "Installing with Development Dependencies"
	@make venv
	@make install
	@$(PIP) install -r requirements_dev.txt

# help: installer					- creates installer exe's
# Note: Pyinstaller need the python dev shared libs installed. Use `apt-get install python3.11-dev`
.PHONY: installer
installer:
	@echo "Creating intaller files"
	@. ./$(VENV)/bin/activate
	pyinstaller ./programmor_adapters/usb_adapter/main.py --name usb_adapter --onefile

# help: style					- fixes the project style
.PHONY: style
style:
	@echo "Apply styles to source code"
	@find programmor_adapters -path "*proto*" -prune -o -path "*include*" -prune -o -type f -name '*.py' -exec autopep8 --in-place '{}' \;

# help: check-style				- checks the project style
.PHONY: check-style
check-style:
	flake8 programmor_adapters tests

# help: check-type				- checks the projects types
.PHONY: check-type
check-type:
	mypy programmor_adapters

# help: test					- runs app tests
.PHONY: test
test:
	pytest

# help: tox					- runs the tox test suit
.PHONY: tox
tox:
	tox

# help: proto					- compiles the protobug file (Only for testing purposes)
.PHONY: proto
proto:
	@find programmor_adapters/shared/proto -name '*.proto' -exec protoc --python_out=. programmor_adapters/shared/proto/transaction.proto \;

# help: docsgen					- generates the documentation
.PHONY: docsgen
docsgen:
	@cd documentation
	@make html
	@cd ..

# help: docsrun					- serves the documentation
.PHONY: docsrun
docsrun:
	python3 -m http.server -d documentation/build/html