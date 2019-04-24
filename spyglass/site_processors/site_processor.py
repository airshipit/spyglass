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

import logging
import os

from jinja2 import Environment
from jinja2 import FileSystemLoader

from spyglass.site_processors.base import BaseProcessor

LOG = logging.getLogger(__name__)


class SiteProcessor(BaseProcessor):
    def __init__(self, intermediary_yaml, manifest_dir):
        super().__init__()
        self.yaml_data = intermediary_yaml
        self.manifest_dir = manifest_dir

    def render_template(self, template_dir):
        """The method  renders network config yaml from j2 templates.


        Network configs common to all racks (i.e oam, overlay, storage,
        calico) are generated in a single file. Rack specific
        configs( pxe and oob) are generated per rack.
        """
        # Check of manifest_dir exists
        if self.manifest_dir is not None:
            site_manifest_dir = self.manifest_dir + "/pegleg_manifests/site/"
        else:
            site_manifest_dir = "pegleg_manifests/site/"
        LOG.info("Site manifest output dir:{}".format(site_manifest_dir))

        template_software_dir = template_dir + "/"
        template_dir_abspath = os.path.dirname(template_software_dir)
        LOG.debug("Template Path:%s", template_dir_abspath)

        for dirpath, dirs, files in os.walk(template_dir_abspath):
            for filename in files:
                j2_env = Environment(autoescape=True,
                                     loader=FileSystemLoader(dirpath),
                                     trim_blocks=True)
                j2_env.filters["get_role_wise_nodes"] = \
                    self.get_role_wise_nodes
                templatefile = os.path.join(dirpath, filename)
                outdirs = dirpath.split("templates")[1]

                outfile_path = "{}{}{}".format(site_manifest_dir,
                                               self.yaml_data["region_name"],
                                               outdirs)
                outfile_yaml = templatefile.split(".j2")[0].split("/")[-1]
                outfile = outfile_path + "/" + outfile_yaml
                outfile_dir = os.path.dirname(outfile)
                if not os.path.exists(outfile_dir):
                    os.makedirs(outfile_dir)
                template_j2 = j2_env.get_template(filename)
                try:
                    out = open(outfile, "w")
                    template_j2.stream(data=self.yaml_data).dump(out)
                    LOG.info("Rendering {}".format(outfile_yaml))
                    out.close()
                except IOError as ioe:
                    LOG.error(
                        "IOError during rendering:{}".format(outfile_yaml))
                    raise SystemExit(
                        "Error when generating {:s}:\n{:s}".format(
                            outfile, ioe.strerror))
