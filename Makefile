# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SPYGLASS_BUILD_CTX  ?= .
IMAGE_NAME        ?= spyglass
IMAGE_PREFIX      ?= att-comdev
DOCKER_REGISTRY   ?= quay.io
IMAGE_TAG         ?= latest
PROXY             ?= http://proxy.foo.com:8000
NO_PROXY          ?= localhost,127.0.0.1,.svc.cluster.local
USE_PROXY         ?= false
PUSH_IMAGE        ?= false
LABEL             ?= commit-id
IMAGE             ?= $(DOCKER_REGISTRY)/$(IMAGE_PREFIX)/$(IMAGE_NAME):$(IMAGE_TAG)
PYTHON_BASE_IMAGE ?= python:3.6
export

# Build all docker images for this project
.PHONY: images
images: build_spyglass

# Run an image locally and exercise simple tests
.PHONY: run_images
run_images: run_spyglass

.PHONY: run_spyglass
run_spyglass: build_spyglass
	tools/spyglass.sh --help

.PHONY: security
security:
	tox -c tox.ini -e bandit

# Perform Linting
.PHONY: lint
lint: py_lint

# Perform auto formatting
.PHONY: format
format: py_format

.PHONY: build_spyglass
build_spyglass:
ifeq ($(USE_PROXY), true)
	docker build -t $(IMAGE) --network=host --label $(LABEL) -f images/spyglass/Dockerfile \
		--build-arg FROM=$(PYTHON_BASE_IMAGE) \
		--build-arg http_proxy=$(PROXY) \
		--build-arg https_proxy=$(PROXY) \
		--build-arg HTTP_PROXY=$(PROXY) \
		--build-arg HTTPS_PROXY=$(PROXY) \
		--build-arg no_proxy=$(NO_PROXY) \
		--build-arg NO_PROXY=$(NO_PROXY) \
		--build-arg ctx_base=$(SPYGLASS_BUILD_CTX) .
else
	docker build -t $(IMAGE) --network=host --label $(LABEL) -f images/spyglass/Dockerfile \
		--build-arg FROM=$(PYTHON_BASE_IMAGE) \
		--build-arg ctx_base=$(SPYGLASS_BUILD_CTX) .
endif
ifeq ($(PUSH_IMAGE), true)
	docker push $(IMAGE)
endif

.PHONY: clean
clean:
	rm -rf build

.PHONY: py_lint
py_lint:
	tox -e pep8

.PHONY: py_format
py_format:
	tox -e fmt
