SHELL := /bin/bash
SRC_DIR = "src"

format:
	black ${SRC_DIR}
	isort ${SRC_DIR}
	autopep8 --in-place --recursive ${SRC_DIR}
	autoflake --recursive --in-place --remove-all-unused-imports ${SRC_DIR}

lint:
	export PYYHONPATH=SRC_DIR && pylint --rcfile setup.cfg ${SRC_DIR}
	export PYYHONPATH=SRC_DIR && flake8 ${SRC_DIR}
	black --check ${SRC_DIR}