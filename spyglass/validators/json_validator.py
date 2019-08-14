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

from glob import glob
import logging
import os

from jsonschema import Draft7Validator
import yaml

from spyglass import exceptions
from spyglass.validators.validator import BaseDocumentValidator

LOG = logging.getLogger(__name__)

LOG_FORMAT = '%(asctime)s %(levelname)-8s %(name)s:' \
             '%(funcName)s [%(lineno)3d] %(message)s'


class JSONSchemaValidator(BaseDocumentValidator):
    """Validator for validating documents using jsonschema"""
    def __init__(
            self,
            document_path,
            schema_path,
            document_extension='.yaml',
            schema_extension='.yaml',
            document_loader=yaml.safe_load,
            schema_loader=yaml.safe_load):
        super().__init__()

        # Check that given paths are valid
        if not os.path.exists(document_path):
            raise exceptions.PathDoesNotExistError(
                file_type='Document', path=document_path)
        if not os.path.exists(schema_path):
            raise exceptions.PathDoesNotExistError(
                file_type='Schema', path=schema_path)

        # Extract list of document file paths from path
        if os.path.isdir(document_path):
            # Create match string and use glob to generate list of file paths
            match = os.path.join(document_path, '**', '*' + document_extension)
            self.documents = glob(match, recursive=True)

            # Directory should not be empty
            if not self.documents:
                raise exceptions.DirectoryEmptyError(
                    ext=document_extension, path=document_path)
        elif os.path.splitext(document_path) == document_extension:
            # Single files can just be appended to the list to process the same
            # so long as the extension matches
            self.documents.append(document_path)
        else:
            # Throw error if unexpected file type given
            raise exceptions.UnexpectedFileType(
                found_ext=os.path.splitext(document_path),
                expected_ext=document_extension)

        # Extract list of schema file paths from path
        if os.path.isdir(schema_path):
            # Create match string and use glob to generate list of file paths
            match = os.path.join(schema_path, '**', '*' + schema_extension)
            self.schemas = glob(match, recursive=True)

            # Directory should not be empty
            if not self.schemas:
                raise exceptions.DirectoryEmptyError(
                    ext=schema_extension, path=schema_path)
        elif os.path.splitext(schema_path) == schema_extension:
            # Single files can just be appended to the list to process the same
            self.schemas.append(schema_path)
        else:
            # Throw error if unexpected file type given
            raise exceptions.UnexpectedFileType(
                found_ext=os.path.splitext(schema_path),
                expected_ext=schema_extension)

        # Initialize pairs list for next step
        self.document_schema_pairs = []

        self.document_loader = document_loader
        self.schema_loader = schema_loader
        self._match_documents_to_schemas()

    def _match_documents_to_schemas(self):
        """Pairs documents to their schemas for easier processing

        Loops through all documents and finds its associated schema using the
        "schema" key from documents and the "metadata:name" key from schemas.
        Matching document/schema pairs are added to document_schema_pairs. Any
        unmatched documents will display a warning.
        """
        if not self.documents:
            LOG.warning('No documents found.')

        if not self.schemas:
            LOG.warning('No schemas found.')

        for document in self.documents:
            pair_found = False
            with open(document, 'r') as f_doc:
                loaded_doc = self.document_loader(f_doc)
            if 'schema' in loaded_doc:
                schema_name = loaded_doc['schema']
                for schema in self.schemas:
                    with open(schema, 'r') as f_schema:
                        loaded_schema = self.schema_loader(f_schema)
                    if schema_name == loaded_schema['metadata']['name']:
                        self.document_schema_pairs.append((document, schema))
                        pair_found = True
                        break
            else:
                LOG.warning('No schema entry found for file %s', document)
            if not pair_found:
                LOG.warning(
                    'No matching schema found for file %s, '
                    'data will not be validated.', document)

    def _validate_file(self, document, schema):
        """Validate a document against a schema using JSON Schema Draft 7

        :param document: File path to the document to validate
        :param schema: File path to the schema used to validate document
        :return: A list of errors from the validator
        """
        with open(document, 'r') as f_doc:
            loaded_doc = self.document_loader(f_doc)
        with open(schema, 'r') as f_schema:
            loaded_schema = self.schema_loader(f_schema)
        validator = Draft7Validator(loaded_schema)
        return sorted(validator.iter_errors(loaded_doc), key=lambda e: e.path)

    def validate(self):
        """Validates document against its schema

        Loops through document_schema_pairs list and validates each pair. Any
        errors are logged and returned in a dictionary by file.

        :return: A dictionary of filenames and their list of validation errors
        """
        error_list = {}
        for document, schema in self.document_schema_pairs:
            LOG.info(
                'Validating document %s using schema %s', document, schema)
            errors = self._validate_file(document, schema)
            if errors:
                for error in errors:
                    LOG.error(error.message)
                error_list[document] = errors

        return error_list
