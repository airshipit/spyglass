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
import os
import shutil

import jinja2

from spyglass.site_processors.base import BaseProcessor

LOG = logging.getLogger(__name__)


class SiteProcessor(BaseProcessor):

    def __init__(self, intermediary_yaml, manifest_dir, force_write):
        super().__init__()
        self.yaml_data = intermediary_yaml
        self.manifest_dir = manifest_dir
        self.force_write = force_write

    def render_template(self, template_dir):
        """The method  renders network config yaml from j2 templates.

        Network configs common to all racks (i.e oam, overlay, storage,
        calico) are generated in a single file. Rack specific
        configs( pxe and oob) are generated per rack.
        """
        # Check of manifest_dir exists
        if self.manifest_dir is not None:
            site_manifest_dir = os.path.join(
                self.manifest_dir, 'pegleg_manifests', 'site')
        else:
            site_manifest_dir = os.path.join('pegleg_manifests', 'site')
        LOG.info("Site manifest output dir:{}".format(site_manifest_dir))

        LOG.debug("Template Path: %s", template_dir)

        if self.force_write:
            logging_undefined = \
                jinja2.make_logging_undefined(LOG, base=jinja2.Undefined)
        else:
            logging_undefined = \
                jinja2.make_logging_undefined(LOG, base=jinja2.StrictUndefined)

        template_folder_name = os.path.split(template_dir)[1]
        created_file_list = []
        created_dir_list = []

        for dirpath, dirs, files in os.walk(template_dir):
            loader = jinja2.FileSystemLoader(dirpath)
            for filename in files:
                j2_env = jinja2.Environment(
                    autoescape=True,
                    loader=loader,
                    trim_blocks=True,
                    undefined=logging_undefined)
                j2_env.filters["get_role_wise_nodes"] = \
                    self.get_role_wise_nodes
                templatefile = os.path.join(dirpath, filename)
                LOG.debug("Template file: %s", templatefile)
                outdirs = dirpath.split(template_folder_name)[1].lstrip(os.sep)
                LOG.debug("outdirs: %s", outdirs)

                outfile_path = os.path.join(
                    site_manifest_dir, self.yaml_data["region_name"], outdirs)
                LOG.debug("outfile path: %s", outfile_path)
                outfile_yaml = os.path.split(templatefile)[1]
                outfile_yaml = os.path.splitext(outfile_yaml)[0]
                outfile = os.path.join(outfile_path, outfile_yaml)
                LOG.debug("outfile: %s", outfile)
                outfile_dir = os.path.dirname(outfile)
                if not os.path.exists(outfile_dir):
                    os.makedirs(outfile_dir)
                    created_dir_list.append(outfile_dir)
                template_j2 = j2_env.get_template(filename)
                try:
                    out = open(outfile, "w")
                    created_file_list.append(outfile)
                    LOG.info("Rendering {}".format(outfile_yaml))
                    rendered = template_j2.render(data=self.yaml_data)
                    out.write(rendered)
                    out.close()
                except IOError as ioe:
                    LOG.error(
                        "IOError during rendering:{}".format(outfile_yaml))
                    raise SystemExit(
                        "Error when generating {:s}:\n{:s}".format(
                            outfile, ioe.strerror))
                except jinja2.UndefinedError as e:
                    LOG.info('Undefined data found, rolling back changes...')
                    out.close()
                    shutil.rmtree(site_manifest_dir)
                    raise e
