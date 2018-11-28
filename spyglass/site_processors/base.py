# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class BaseProcessor:
    def __init__(self, file_name):
        pass

    def render_template(self, template):
        pass

    @staticmethod
    def get_role_wise_nodes(yaml_data):
        hosts = {
            'genesis': {},
            'masters': [],
            'workers': [],
        }

        for rack in yaml_data['baremetal']:
            for host in yaml_data['baremetal'][rack]:
                if yaml_data['baremetal'][rack][host]['type'] == 'genesis':
                    hosts['genesis'] = {
                        'name': host,
                        'pxe': yaml_data['baremetal'][rack][host]['ip']['pxe'],
                        'oam': yaml_data['baremetal'][rack][host]['ip']['oam'],
                    }
                elif yaml_data['baremetal'][rack][host][
                        'type'] == 'controller':
                    hosts['masters'].append(host)
                else:
                    hosts['workers'].append(host)
        return hosts
