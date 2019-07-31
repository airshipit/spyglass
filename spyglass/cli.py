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

import logging
import pprint

import click
from click_plugins import with_plugins
import pkg_resources
import yaml

from spyglass import exceptions
from spyglass.parser.engine import ProcessDataSource
from spyglass.site_processors.site_processor import SiteProcessor
from spyglass.validators.json_validator import JSONSchemaValidator

LOG = logging.getLogger(__name__)

LOG_FORMAT = '%(asctime)s %(levelname)-8s %(name)s:' \
             '%(funcName)s [%(lineno)3d] %(message)s'

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}

SITE_CONFIGURATION_FILE_OPTION = click.option(
    '-c',
    '--site-configuration',
    'site_configuration',
    type=click.Path(exists=True, readable=True, dir_okay=False),
    required=False,
    help='Path to site specific configuration details YAML file.')

INTERMEDIARY_DIR_OPTION = click.option(
    '-d',
    '--intermediary-dir',
    'intermediary_dir',
    type=click.Path(exists=True, file_okay=False, writable=True),
    default='./',
    help='Directory in which the intermediary file will be created.')

SITE_NAME_CONFIGURATION_OPTION = click.option(
    '-s',
    '--site-name',
    'site_name',
    type=click.STRING,
    required=False,
    help='Name of the site for which the intermediary is being generated.')

TEMPLATE_DIR_OPTION = click.option(
    '-t',
    '--template-dir',
    'template_dir',
    type=click.Path(exists=True, readable=True, file_okay=False),
    required=True,
    help='Path to the directory containing manifest J2 templates.')

MANIFEST_DIR_OPTION = click.option(
    '-m',
    '--manifest-dir',
    'manifest_dir',
    type=click.Path(exists=True, writable=True, file_okay=False),
    required=False,
    help='Path to place created manifest files.')

FORCE_OPTION = click.option(
    '--force',
    'force',
    is_flag=True,
    default=False,
    help="Forces manifests to be written, regardless of undefined data.")


@click.option(
    '-v',
    '--verbose',
    is_flag=True,
    default=False,
    help='Enable debug messages in log.')
@with_plugins(pkg_resources.iter_entry_points('cli_plugins'))
@click.group()
def main(*, verbose):
    """CLI for Airship Spyglass"""
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format=LOG_FORMAT, level=log_level)


def intermediary_processor(plugin_type, **kwargs):
    LOG.info("Generating Intermediary yaml")
    plugin_type = plugin_type

    # Load the plugin class
    LOG.info("Load the plugin class")
    entry_point = "data_extractor_plugins"
    try:
        plugin_class = pkg_resources.load_entry_point(
            "spyglass", entry_point, plugin_type)
    except ImportError:
        raise exceptions.UnsupportedPlugin(
            plugin_name=plugin_type, entry_point=entry_point)

    # Extract data from plugin data source
    LOG.info("Extract data from plugin data source")
    data_extractor = plugin_class(kwargs['site_name'], **kwargs)

    # Apply any additional_config provided by user
    additional_config = kwargs.get('site_configuration', None)
    if additional_config is not None:
        with open(additional_config, 'r') as config:
            additional_config_data = yaml.safe_load(config)
        LOG.debug(
            "Additional config data:\n{}".format(
                pprint.pformat(additional_config_data)))
    else:
        additional_config_data = None

    # Extract data into data objects
    data_extractor.get_data(additional_config_data)
    LOG.debug(pprint.pformat(data_extractor.data.dict_from_class()))

    # Apply design rules to the data
    LOG.info("Apply design rules to the extracted data")
    process_input_ob = ProcessDataSource(
        kwargs['site_name'], data_extractor.data)
    return process_input_ob


@main.command(
    'mi',
    short_help='generates manifest from intermediary',
    help='Generate manifest files from specified intermediary file.')
@click.argument(
    'intermediary_file',
    type=click.Path(exists=True, readable=True, dir_okay=False))
@TEMPLATE_DIR_OPTION
@MANIFEST_DIR_OPTION
@FORCE_OPTION
def generate_manifests_using_intermediary(
        *, intermediary_file, template_dir, manifest_dir, force):
    LOG.info("Loading intermediary from user provided input")
    with open(intermediary_file, 'r') as f:
        raw_data = f.read()
        intermediary_yaml = yaml.safe_load(raw_data)

    LOG.info("Generating site Manifests")
    processor_engine = SiteProcessor(intermediary_yaml, manifest_dir, force)
    processor_engine.render_template(template_dir)


@main.command(
    'validate',
    short_help='validates pegleg documents',
    help='Validates pegleg documents against their schema.')
@click.option(
    '-d',
    '--document-path',
    'document_path',
    type=click.Path(exists=True, readable=True),
    required=True,
    help='Path to the documents to validate.')
@click.option(
    '-p',
    '--schema-path',
    'schema_path',
    type=click.Path(exists=True, readable=True),
    required=True,
    help=(
        'Path to a schema file or directory of schema files used to '
        'validate documents.'))
def validate_manifests_against_schemas(document_path, schema_path):
    validator = JSONSchemaValidator(document_path, schema_path)
    validator.validate()
