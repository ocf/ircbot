DOCKER_REVISION ?= testing-$(USER)
DOCKER_TAG = docker-push.ocf.berkeley.edu/ircbot:$(DOCKER_REVISION)

.PHONY: test
test: venv install-hooks
	venv/bin/pre-commit run --all-files

.PHONY: install-hooks
install-hooks: venv
	venv/bin/pre-commit install -f --install-hooks

venv: vendor/venv-update requirements.txt requirements-dev.txt
	vendor/venv-update \
		venv= -ppython3 venv \
		install= -r requirements.txt -r requirements-dev.txt

.PHONY: dev
dev: venv
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
