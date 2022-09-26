SHELL := /bin/bash
SRC_DIR = "src"

format:
	black ${SRC_DIR}

lint:
	export PYYHONPATH=SRC_DIR && pylint --rcfile setup.cfg ${SRC_DIR}
	export PYYHONPATH=SRC_DIR && flake8 ${SRC_DIR}