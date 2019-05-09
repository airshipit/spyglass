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
import pkg_resources
import yaml

from spyglass.parser.engine import ProcessDataSource
from spyglass.site_processors.site_processor import SiteProcessor

LOG = logging.getLogger(__name__)

LOG_FORMAT = '%(asctime)s %(levelname)-8s %(name)s:' \
             '%(funcName)s [%(lineno)3d] %(message)s'

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}


def tugboat_required_callback(ctx, param, value):
    LOG.debug('Evaluating %s: %s', param.name, value)
    if 'plugin_type' not in ctx.params or \
            ctx.params['plugin_type'] == 'tugboat':
        if not value:
            raise click.UsageError(
                '%s is required for the tugboat '
                'plugin.' % str(param.name),
                ctx=ctx)
    return value


def formation_required_callback(ctx, param, value):
    LOG.debug('Evaluating %s: %s', param.name, value)
    if 'plugin_type' in ctx.params:
        if ctx.params['plugin_type'] == 'formation':
            if not value:
                raise click.UsageError(
                    '%s is required for the '
                    'formation plugin.' % str(param.name),
                    ctx=ctx)
            return value
    return ['', '', '']


PLUGIN_TYPE_OPTION = click.option(
    '-p',
    '--plugin-type',
    'plugin_type',
    type=click.Choice(['formation', 'tugboat']),
    default='tugboat',
    show_default=True,
    help='The plugin type to use.')

# TODO(ianp): Either provide a prompt for passwords or use environment
# variable so passwords are no longer plain text
FORMATION_TARGET_OPTION = click.option(
    '-f',
    '--formation-target',
    'formation_target',
    nargs=3,
    help=(
        'Target URL, username, and password for formation plugin. Required '
        'for formation plugin.'),
    callback=formation_required_callback)

INTERMEDIARY_DIR_OPTION = click.option(
    '-d',
    '--intermediary-dir',
    'intermediary_dir',
    type=click.Path(exists=True, file_okay=False, writable=True),
    default='./',
    help='Directory in which the intermediary file will be created.')

EXCEL_FILE_OPTION = click.option(
    '-x',
    '--excel-file',
    'excel_file',
    multiple=True,
    type=click.Path(exists=True, readable=True, dir_okay=False),
    help='Path to the engineering Excel file. Required for tugboat plugin.',
    callback=tugboat_required_callback)

EXCEL_SPEC_OPTION = click.option(
    '-e',
    '--excel-spec',
    'excel_spec',
    type=click.Path(exists=True, readable=True, dir_okay=False),
    help=(
        'Path to the Excel specification YAML file for the engineering '
        'Excel file. Required for tugboat plugin.'),
    callback=tugboat_required_callback)

SITE_CONFIGURATION_FILE_OPTION = click.option(
    '-c',
    '--site-configuration',
    'site_configuration',
    type=click.Path(exists=True, readable=True, dir_okay=False),
    required=False,
    help='Path to site specific configuration details YAML file.')

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


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    '-v',
    '--verbose',
    is_flag=True,
    default=False,
    help='Enable debug messages in log.')
def main(*, verbose):
    """CLI for Airship Spyglass"""
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format=LOG_FORMAT, level=log_level)


def _intermediary_helper(
        plugin_type, formation_data, site, excel_file, excel_spec,
        additional_configuration):
    LOG.info("Generating Intermediary yaml")
    plugin_type = plugin_type
    plugin_class = None

    # Discover the plugin and load the plugin class
    LOG.info("Load the plugin class")
    for entry_point in \
            pkg_resources.iter_entry_points('data_extractor_plugins'):
        if entry_point.name == plugin_type:
            plugin_class = entry_point.load()

    if plugin_class is None:
        LOG.error(
            "Unsupported Plugin type. Plugin type:{}".format(plugin_type))
        exit()

    # Extract data from plugin data source
    LOG.info("Extract data from plugin data source")
    data_extractor = plugin_class(site)
    plugin_conf = data_extractor.get_plugin_conf(
        {
            'excel': excel_file,
            'excel_spec': excel_spec,
            'formation_url': formation_data[0],
            'formation_user': formation_data[1],
            'formation_password': formation_data[2]
        })
    data_extractor.set_config_opts(plugin_conf)
    data_extractor.extract_data()

    # Apply any additional_config provided by user
    additional_config = additional_configuration
    if additional_config is not None:
        with open(additional_config, 'r') as config:
            raw_data = config.read()
            additional_config_data = yaml.safe_load(raw_data)
        LOG.debug(
            "Additional config data:\n{}".format(
                pprint.pformat(additional_config_data)))

        LOG.info(
            "Apply additional configuration from:{}".format(additional_config))
        data_extractor.apply_additional_data(additional_config_data)
        LOG.debug(pprint.pformat(data_extractor.site_data))

    # Apply design rules to the data
    LOG.info("Apply design rules to the extracted data")
    process_input_ob = ProcessDataSource(site)
    process_input_ob.load_extracted_data_from_data_source(
        data_extractor.site_data)
    return process_input_ob


@main.command(
    'i',
    short_help='generate intermediary',
    help='Generates an intermediary file from passed excel data.')
@PLUGIN_TYPE_OPTION
@FORMATION_TARGET_OPTION
@INTERMEDIARY_DIR_OPTION
@EXCEL_FILE_OPTION
@EXCEL_SPEC_OPTION
@SITE_CONFIGURATION_FILE_OPTION
@SITE_NAME_CONFIGURATION_OPTION
def generate_intermediary(
        *, plugin_type, formation_target, intermediary_dir, excel_file,
        excel_spec, site_configuration, site_name):
    process_input_ob = _intermediary_helper(
        plugin_type, formation_target, site_name, excel_file, excel_spec,
        site_configuration)
    LOG.info("Generate intermediary yaml")
    process_input_ob.generate_intermediary_yaml()
    process_input_ob.dump_intermediary_file(intermediary_dir)


@main.command(
    'm',
    short_help='generates manifest and intermediary',
    help='Generates manifest and intermediary files.')
@click.option(
    '-i',
    '--save-intermediary',
    'save_intermediary',
    is_flag=True,
    default=False,
    help='Flag to save the generated intermediary file used for the manifests.'
)
@PLUGIN_TYPE_OPTION
@FORMATION_TARGET_OPTION
@INTERMEDIARY_DIR_OPTION
@EXCEL_FILE_OPTION
@EXCEL_SPEC_OPTION
@SITE_CONFIGURATION_FILE_OPTION
@SITE_NAME_CONFIGURATION_OPTION
@TEMPLATE_DIR_OPTION
@MANIFEST_DIR_OPTION
def generate_manifests_and_intermediary(
        *, save_intermediary, plugin_type, formation_target, intermediary_dir,
        excel_file, excel_spec, site_configuration, site_name, template_dir,
        manifest_dir):
    process_input_ob = _intermediary_helper(
        plugin_type, formation_target, site_name, excel_file, excel_spec,
        site_configuration)
    LOG.info("Generate intermediary yaml")
    intermediary_yaml = process_input_ob.generate_intermediary_yaml()
    if save_intermediary:
        LOG.debug("Dumping intermediary yaml")
        process_input_ob.dump_intermediary_file(intermediary_dir)
    else:
        LOG.debug("Skipping dump for intermediary yaml")

    LOG.info("Generating site Manifests")
    processor_engine = SiteProcessor(intermediary_yaml, manifest_dir)
    processor_engine.render_template(template_dir)


@main.command(
    'mi',
    short_help='generates manifest from intermediary',
    help='Generate manifest files from specified intermediary file.')
@click.argument(
    'intermediary_file',
    type=click.Path(exists=True, readable=True, dir_okay=False))
@TEMPLATE_DIR_OPTION
@MANIFEST_DIR_OPTION
def generate_manifests_using_intermediary(
        *, intermediary_file, template_dir, manifest_dir):
    LOG.info("Loading intermediary from user provided input")
    with open(intermediary_file, 'r') as f:
        raw_data = f.read()
        intermediary_yaml = yaml.safe_load(raw_data)

    LOG.info("Generating site Manifests")
    processor_engine = SiteProcessor(intermediary_yaml, manifest_dir)
    processor_engine.render_template(template_dir)
