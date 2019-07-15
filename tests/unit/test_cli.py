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
from unittest import mock

from click.testing import CliRunner
import pytest
import yaml

from spyglass.cli import generate_manifests_using_intermediary
from spyglass.cli import intermediary_processor
from spyglass.cli import validate_manifests_against_schemas
from spyglass import exceptions
from spyglass.parser.engine import ProcessDataSource
from spyglass.site_processors.site_processor import SiteProcessor
from spyglass.validators.json_validator import JSONSchemaValidator

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'shared')

INTERMEDIARY_PATH = os.path.join(FIXTURE_DIR, 'test_intermediary.yaml')

TEMPLATE_DIR_PATH = os.path.join(FIXTURE_DIR, 'templates')

SITE_CONFIG_PATH = os.path.join(FIXTURE_DIR, 'site_config.yaml')

DOCUMENTS_PATH = os.path.join(FIXTURE_DIR, 'documents')

SCHEMAS_PATH = os.path.join(FIXTURE_DIR, 'schemas')


def _get_intermediary_process_kwargs():
    return {'site_name': 'test'}


def _get_site_config_data():
    with open(SITE_CONFIG_PATH, 'r') as f:
        data = f.read()
    return yaml.safe_load(data)


def _get_intermediary_data():
    with open(INTERMEDIARY_PATH, 'r') as f:
        data = f.read()
    return yaml.safe_load(data)


@mock.patch('spyglass.parser.engine.ProcessDataSource', autospec=True)
@mock.patch('spyglass_plugin_xls.excel.ExcelPlugin', autospec=False)
def test_intermediary_processor(mock_excel_plugin, mock_process_data_source):
    """Tests that the intermediary processor produces expected results"""
    plugin_name = 'excel'
    data = _get_intermediary_process_kwargs()
    mock_excel_plugin.return_value.site_data = {}
    result = intermediary_processor(plugin_name, **data)
    assert type(result) == ProcessDataSource


def test_intermediary_processor_unsupported_plugin():
    """Tests that an exception is raised if a plugin is not configured"""
    plugin_name = 'invalid_plugin'
    with pytest.raises(exceptions.UnsupportedPlugin):
        intermediary_processor(
            plugin_name, **_get_intermediary_process_kwargs())


@mock.patch('spyglass.parser.engine.ProcessDataSource', autospec=True)
@mock.patch('spyglass_plugin_xls.excel.ExcelPlugin', autospec=False)
def test_intermediary_processor_additional_config(
        mock_excel_plugin, mock_process_data_source):
    """Tests that an additional configuration is processed if included"""
    plugin_name = 'excel'
    data = _get_intermediary_process_kwargs()
    data['site_configuration'] = SITE_CONFIG_PATH
    mock_excel_plugin.return_value.site_data = {}
    result = intermediary_processor(plugin_name, **data)
    assert type(result) == ProcessDataSource
    mock_excel_plugin.return_value.get_data.\
        assert_called_once_with(_get_site_config_data())


@mock.patch.object(
    SiteProcessor, '__init__', spec=SiteProcessor, return_value=None)
def test_generate_manifests_using_intermediary(mock_site_processor):
    """Tests `mi` command from CLI"""
    runner = CliRunner()
    with mock.patch.object(SiteProcessor, 'render_template',
                           spec=SiteProcessor) as mock_render:
        result = runner.invoke(
            generate_manifests_using_intermediary,
            [INTERMEDIARY_PATH, '-t', TEMPLATE_DIR_PATH])
    assert result.exit_code == 0
    mock_site_processor.assert_called_once_with(
        _get_intermediary_data(), None, False)
    mock_render.assert_called_once_with(TEMPLATE_DIR_PATH)


def test_generate_manifests_using_intermediary_no_intermediary_file():
    """Tests bad input for intermediary file for `mi` command"""
    runner = CliRunner()
    with mock.patch.object(SiteProcessor, 'render_template',
                           spec=SiteProcessor) as mock_render:
        result = runner.invoke(
            generate_manifests_using_intermediary, ['-t', TEMPLATE_DIR_PATH])
    assert result.exit_code != 0
    assert not mock_render.called


def test_generate_manifests_using_intermediary_no_templates():
    """Tests bad input for templates folder for `mi` command"""
    runner = CliRunner()
    with mock.patch.object(SiteProcessor, 'render_template',
                           spec=SiteProcessor) as mock_render:
        result = runner.invoke(
            generate_manifests_using_intermediary, [INTERMEDIARY_PATH])
    assert result.exit_code != 0
    assert not mock_render.called


@mock.patch.object(
    JSONSchemaValidator, '__init__', autospec=True, return_value=None)
@mock.patch.object(JSONSchemaValidator, 'validate', autospec=True)
def test_validate_manifests_against_schemas(mock_validate, mock_validator):
    """Tests `validate` command from CLI using defualt behavior"""
    runner = CliRunner()
    result = runner.invoke(
        validate_manifests_against_schemas,
        ['-d', DOCUMENTS_PATH, '-p', SCHEMAS_PATH])
    assert result.exit_code == 0
    mock_validator.assert_called_once_with(
        mock.ANY, DOCUMENTS_PATH, SCHEMAS_PATH)
    mock_validate.assert_called_once()
