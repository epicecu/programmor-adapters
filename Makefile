# help:
# help:	Programmor Tuning Software
# help:

# help: help					- displays this make file help information
.PHONY: help
help:
	@grep "^# help\:" Makefile | sed 's/\# help\: *//'

# help: run					- starts the application
.PHONY: run
run:
	@source venv/bin/activate
	@python -m usb

# help: venv				- creates a virtual environment
.PHONY: venv
venv:
	@python3.11 -m venv venv
	@source venv/bin/activate

# help: install					- installs the application
.PHONY: install
install:
	@echo "Installing"
	@pip install -e .
	@pip install -r requirements.txt

# help: install-dev				- installs the application with development dependencies
.PHONY: install-dev
install-dev: install
	@echo "Installing with Development Dependencies"
	@make install
	@pip install -r requirements_dev.txt

# help: style					- fixes the project style
.PHONY: style
style:
	@find src -path "*proto*" -prune -o -path "*include*" -prune -o -type f -name '*.py' -exec autopep8 --in-place '{}' \;

# help: check-style				- checks the project style
.PHONY: check-style
check-style:
	@flake8 src tests

# help: check-type				- checks the projects types
.PHONY: check-type
check-type:
	@mypy src

# help: test					- runs app tests
.PHONY: test
test:
	@pytest

# help: tox					- runs the tox test suit
.PHONY: tox
tox:
	@tox

# help: proto				- compiles the protobug file (Only for testing purposes)
.PHONY: proto
proto:
	@find src/programmor/proto -name '*.proto' -exec protoc --python_out=. src/programmor/proto/transaction.proto \;