# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import pkg_resources
import pprint

import click
import yaml

from spyglass.parser.engine import ProcessDataSource
from spyglass.site_processors.site_processor import SiteProcessor

LOG = logging.getLogger('spyglass')


@click.command()
@click.option(
    '--site',
    '-s',
    help='Specify the site for which manifests to be generated')
@click.option(
    '--type', '-t', help='Specify the plugin type formation or tugboat')
@click.option('--formation_url', '-f', help='Specify the formation url')
@click.option('--formation_user', '-u', help='Specify the formation user id')
@click.option(
    '--formation_password', '-p', help='Specify the formation user password')
@click.option(
    '--intermediary',
    '-i',
    type=click.Path(exists=True),
    help=
    'Intermediary file path  generate manifests, use -m also with this option')
@click.option(
    '--additional_config',
    '-d',
    type=click.Path(exists=True),
    help='Site specific configuraton details')
@click.option(
    '--generate_intermediary',
    '-g',
    is_flag=True,
    help='Dump intermediary file from passed excel and excel spec')
@click.option(
    '--intermediary_dir',
    '-idir',
    type=click.Path(exists=True),
    help='The path where intermediary file needs to be generated')
@click.option(
    '--edit_intermediary/--no_edit_intermediary',
    '-e/-nedit',
    default=True,
    help='Flag to let user edit intermediary')
@click.option(
    '--generate_manifests',
    '-m',
    is_flag=True,
    help='Generate manifests from the generated intermediary file')
@click.option(
    '--manifest_dir',
    '-mdir',
    type=click.Path(exists=True),
    help='The path where manifest files needs to be generated')
@click.option(
    '--template_dir',
    '-tdir',
    type=click.Path(exists=True),
    help='The path where J2 templates are available')
@click.option(
    '--excel',
    '-x',
    multiple=True,
    type=click.Path(exists=True),
    help=
    'Path to engineering excel file, to be passed with generate_intermediary')
@click.option(
    '--excel_spec',
    '-e',
    type=click.Path(exists=True),
    help='Path to excel spec, to be passed with generate_intermediary')
@click.option(
    '--loglevel',
    '-l',
    default=20,
    multiple=False,
    show_default=True,
    help='Loglevel NOTSET:0 ,DEBUG:10, \
    INFO:20, WARNING:30, ERROR:40, CRITICAL:50')
def main(*args, **kwargs):
    # Extract user provided inputs
    generate_intermediary = kwargs['generate_intermediary']
    intermediary_dir = kwargs['intermediary_dir']
    edit_intermediary = kwargs['edit_intermediary']
    generate_manifests = kwargs['generate_manifests']
    manifest_dir = kwargs['manifest_dir']
    intermediary = kwargs['intermediary']
    site = kwargs['site']
    template_dir = kwargs['template_dir']
    loglevel = kwargs['loglevel']

    # Set Logging format
    LOG.setLevel(loglevel)
    stream_handle = logging.StreamHandler()
    formatter = logging.Formatter(
        '(%(name)s): %(asctime)s %(levelname)s %(message)s')
    stream_handle.setFormatter(formatter)
    LOG.addHandler(stream_handle)

    LOG.info("Spyglass start")
    LOG.info("CLI Parameters passed:\n{}".format(kwargs))

    if not (generate_intermediary or generate_manifests):
        LOG.error("Invalid CLI parameters passed!! Spyglass exited")
        LOG.error("One of the options -m/-g is mandatory")
        LOG.info("CLI Parameters:\n{}".format(kwargs))
        exit()

    if generate_manifests:
        if template_dir is None:
            LOG.error("Template directory not specified!! Spyglass exited")
            LOG.error(
                "It is mandatory to provide it when generate_manifests is true"
            )
            exit()

    # Generate Intermediary yaml and manifests extracting data
    # from data source specified by plugin type
    intermediary_yaml = {}
    if intermediary is None:
        LOG.info("Generating Intermediary yaml")
        plugin_type = kwargs.get('type', None)
        plugin_class = None

        # Discover the plugin and load the plugin class
        LOG.info("Load the plugin class")
        for entry_point in pkg_resources.iter_entry_points(
                'data_extractor_plugins'):
            if entry_point.name == plugin_type:
                plugin_class = entry_point.load()

        if plugin_class is None:
            LOG.error(
                "Unsupported Plugin type. Plugin type:{}".format(plugin_type))
            exit()

        # Extract data from plugin data source
        LOG.info("Extract data from plugin data source")
        data_extractor = plugin_class(site)
        plugin_conf = data_extractor.get_plugin_conf(kwargs)
        data_extractor.set_config_opts(plugin_conf)
        data_extractor.extract_data()

        # Apply any additional_config provided by user
        additional_config = kwargs.get('additional_config', None)
        if additional_config is not None:
            with open(additional_config, 'r') as config:
                raw_data = config.read()
                additional_config_data = yaml.safe_load(raw_data)
            LOG.debug("Additional config data:\n{}".format(
                pprint.pformat(additional_config_data)))

            LOG.info("Apply additional configuration from:{}".format(
                additional_config))
            data_extractor.apply_additional_data(additional_config_data)
            LOG.debug(pprint.pformat(data_extractor.site_data))

        # Apply design rules to the data
        LOG.info("Apply design rules to the extracted data")
        process_input_ob = ProcessDataSource(site)
        process_input_ob.load_extracted_data_from_data_source(
            data_extractor.site_data)

        LOG.info("Generate intermediary yaml")
        intermediary_yaml = process_input_ob.generate_intermediary_yaml(
            edit_intermediary)
    else:
        LOG.info("Loading intermediary from user provided input")
        with open(intermediary, 'r') as intermediary_file:
            raw_data = intermediary_file.read()
            intermediary_yaml = yaml.safe_load(raw_data)

    if generate_intermediary:
        process_input_ob.dump_intermediary_file(intermediary_dir)

    if generate_manifests:
        LOG.info("Generating site Manifests")
        processor_engine = SiteProcessor(intermediary_yaml, manifest_dir)
        processor_engine.render_template(template_dir)

    LOG.info("Spyglass Execution Completed")


if __name__ == '__main__':
    main()
