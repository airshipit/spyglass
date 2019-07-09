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

from spyglass.exceptions import PathDoesNotExistError
from spyglass.validators.json_validator import JSONSchemaValidator

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared')

DOCUMENT_DIR = os.path.join(FIXTURE_DIR, 'documents')

VALID_DOCUMENTS_DIR = os.path.join(DOCUMENT_DIR, 'valid')

INVALID_DOCUMENTS_DIR = os.path.join(DOCUMENT_DIR, 'invalid')

SCHEMA_DIR = os.path.join(FIXTURE_DIR, 'schemas')


def test_bad_document_path():
    """Tests that an invalid document path raises a PathDoesNotExistError"""
    bad_path = os.path.join(FIXTURE_DIR, 'not_documents')
    with pytest.raises(PathDoesNotExistError):
        JSONSchemaValidator(bad_path, SCHEMA_DIR)


def test_bad_schema_path():
    """Tests that an invalid schema path raises a PathDoesNotExistError"""
    bad_path = os.path.join(FIXTURE_DIR, 'not_schemas')
    with pytest.raises(PathDoesNotExistError):
        JSONSchemaValidator(DOCUMENT_DIR, bad_path)


def test_document_schema_matching():
    """Tests that documents and schema are correctly paired up"""
    expected_pairs = [
        ('site-definition.yaml', 'site-definition-schema.yaml'),
        ('pki-catalogue.yaml', 'pki-catalogue-schema.yaml')
    ]
    validator = JSONSchemaValidator(VALID_DOCUMENTS_DIR, SCHEMA_DIR)
    no_path_pairs = []
    for pair in validator.document_schema_pairs:
        no_path_pairs.append(
            (os.path.split(pair[0])[1], os.path.split(pair[1])[1]))
    for pair in expected_pairs:
        assert pair in no_path_pairs


def test_document_schema_matching_no_files():
    """Tests that document and schema are not paired if there are no matches"""
    site_definition_doc_dir = os.path.join(
        VALID_DOCUMENTS_DIR, 'SiteDefinition')
    site_definition_schema_dir = os.path.join(SCHEMA_DIR, 'PKICatalogue')

    expected_pairs = []
    validator = JSONSchemaValidator(
        site_definition_doc_dir, site_definition_schema_dir)
    no_path_pairs = []
    for pair in validator.document_schema_pairs:
        no_path_pairs.append(
            (os.path.split(pair[0])[1], os.path.split(pair[1])[1]))
    assert no_path_pairs == expected_pairs


def test_validate():
    """Tests that validation of correct files yields no errors"""
    validator = JSONSchemaValidator(VALID_DOCUMENTS_DIR, SCHEMA_DIR)
    errors = validator.validate()
    assert not errors


def test_validate_with_errors():
    """Tests that correct errors are generated for an invalid document"""
    validator = JSONSchemaValidator(INVALID_DOCUMENTS_DIR, SCHEMA_DIR)
    errors = validator.validate()
    assert errors
