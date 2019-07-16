# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
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

import os

import pytest
import yaml

from spyglass.data_extractor.models import site_document_data_factory

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'shared')


@pytest.fixture(scope='class')
def site_document_data_objects(request):
    with open(os.path.join(FIXTURE_DIR, 'test_intermediary.yaml'), 'r') as f:
        yaml_data = yaml.safe_load(f)
    request.cls.site_document_data = site_document_data_factory(yaml_data)


@pytest.fixture(scope='class')
def rules_data(request):
    with open(os.path.join(FIXTURE_DIR, 'rules.yaml'), 'r') as f:
        request.cls.rules_data = yaml.safe_load(f)
