DOCKER_REVISION ?= testing-$(USER)
DOCKER_TAG = docker-push.ocf.berkeley.edu/ircbot:$(DOCKER_REVISION)

.PHONY: test
test: venv
	venv/bin/pre-commit run --all-files
	venv/bin/pre-commit install -f --install-hooks

venv: vendor/venv-update requirements.txt requirements-dev.txt
	vendor/venv-update \
		venv= -ppython3 venv \
		install= -r requirements.txt -r requirements-dev.txt

.PHONY: clean
clean:
	rm -rf venv

.PHONY: update-requirements
update-requirements:
	$(eval TMP := $(shell mktemp -d))
	virtualenv -p python3 $(TMP)
	. $(TMP)/bin/activate && \
		pip install --upgrade pip && \
		pip install . && \
		pip freeze | grep -v '^ircbot==' | sed 's/^ocflib==.*/ocflib/' > requirements.txt

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
