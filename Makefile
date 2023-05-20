DOCKER_REVISION ?= testing-$(USER)
DOCKER_TAG = docker-push.ocf.berkeley.edu/ircbot:$(DOCKER_REVISION)
RANDOM_PORT ?= $(shell expr $$(( 8010 + (`id -u` % 1000))))

.PHONY: test
test: venv install-hooks mypy
	venv/bin/pre-commit run --all-files

.PHONY: mypy
mypy: venv
	venv/bin/mypy -p ircbot

.PHONY: install-hooks
install-hooks: venv
	venv/bin/pre-commit install -f --install-hooks

venv: vendor/venv-update requirements.txt requirements-dev.txt
	vendor/venv-update \
		venv= -ppython3.9 venv \
		install= -r requirements.txt -r requirements-dev.txt

.PHONY: dev
dev: export HTTP_PORT ?= $(RANDOM_PORT)
dev: venv
	@echo "\e[1m\e[93mRunning help on http://$(shell hostname -f ):$(RANDOM_PORT)/\e[0m"
	venv/bin/python -m ircbot.ircbot

.PHONY: clean
clean:
	rm -rf venv

.PHONY: cook-image
cook-image:
	# TODO: make ocflib an argument
	docker build --pull -t $(DOCKER_TAG) .

.PHONY: push-image
push-image:
	docker push $(DOCKER_TAG)

.PHONY: update-requirements
update-requirements: venv
	venv/bin/upgrade-requirements
	sed -i 's/^ocflib==.*/ocflib/' requirements.txt
