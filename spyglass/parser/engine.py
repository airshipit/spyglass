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

import copy
import json
import logging
import os
import pkg_resources
import pprint
import sys
import tempfile

import jsonschema
import netaddr
import yaml

LOG = logging.getLogger(__name__)


class ProcessDataSource():
    def __init__(self, sitetype):
        # Initialize intermediary and save site type
        self._initialize_intermediary()
        self.region_name = sitetype

    @staticmethod
    def _read_file(file_name):
        with open(file_name, 'r') as f:
            raw_data = f.read()
        return raw_data

    def _initialize_intermediary(self):
        self.host_type = {}
        self.data = {
            'network': {},
            'baremetal': {},
            'region_name': '',
            'storage': {},
            'site_info': {},
        }
        self.sitetype = None
        self.genesis_node = None
        self.region_name = None
        self.network_subnets = None

    def _get_network_subnets(self):
        """ Extract subnet information for networks.


        In some networks, there are multiple subnets, in that case
        we assign only the first subnet """
        LOG.info("Extracting network subnets")
        network_subnets = {}
        for net_type in self.data['network']['vlan_network_data']:
            # One of the type is ingress and we don't want that here
            if (net_type != 'ingress'):
                network_subnets[net_type] = netaddr.IPNetwork(
                    self.data['network']['vlan_network_data'][net_type]
                    ['subnet'][0])

        LOG.debug("Network subnets:\n{}".format(
            pprint.pformat(network_subnets)))
        return network_subnets

    def _get_genesis_node_details(self):
        # Get genesis host node details from the hosts based on host type
        for racks in self.data['baremetal'].keys():
            rack_hosts = self.data['baremetal'][racks]
            for host in rack_hosts:
                if rack_hosts[host]['type'] == 'genesis':
                    self.genesis_node = rack_hosts[host]
                    self.genesis_node['name'] = host
        LOG.debug("Genesis Node Details:\n{}".format(
            pprint.pformat(self.genesis_node)))

    def _get_genesis_node_ip(self):
        """ Returns the genesis node ip """
        ip = '0.0.0.0'
        LOG.info("Getting Genesis Node IP")
        if not self.genesis_node:
            self._get_genesis_node_details()
        ips = self.genesis_node.get('ip', '')
        if ips:
            ip = ips.get('oam', '0.0.0.0')
        return ip

    def _validate_intermediary_data(self, data):
        """ Validates the intermediary data before generating manifests.


        It checks wether the data types and data format are as expected.
        The method validates this with regex pattern defined for each
        data type.
        """
        LOG.info('Validating Intermediary data')
        temp_data = {}
        # Peforming a deep copy
        temp_data = copy.deepcopy(data)
        # Converting baremetal dict to list.
        baremetal_list = []
        for rack in temp_data['baremetal'].keys():
            temp = [{k: v} for k, v in temp_data['baremetal'][rack].items()]
            baremetal_list = baremetal_list + temp

        temp_data['baremetal'] = baremetal_list
        schema_dir = pkg_resources.resource_filename('spyglass', 'schemas/')
        schema_file = schema_dir + "data_schema.json"
        json_data = json.loads(json.dumps(temp_data))
        with open(schema_file, 'r') as f:
            json_schema = json.load(f)
        try:
            # Suppressing writing of data2.json. Can use it for debugging
            with open('data2.json', 'w') as outfile:
                json.dump(temp_data, outfile, sort_keys=True, indent=4)
            jsonschema.validate(json_data, json_schema)
        except jsonschema.exceptions.ValidationError as e:
            LOG.error("Validation Error")
            LOG.error("Message:{}".format(e.message))
            LOG.error("Validator_path:{}".format(e.path))
            LOG.error("Validator_pattern:{}".format(e.validator_value))
            LOG.error("Validator:{}".format(e.validator))
            sys.exit()
        except jsonschema.exceptions.SchemaError as e:
            LOG.error("Schema Validation Error!!")
            LOG.error("Message:{}".format(e.message))
            LOG.error("Schema:{}".format(e.schema))
            LOG.error("Validator_value:{}".format(e.validator_value))
            LOG.error("Validator:{}".format(e.validator))
            LOG.error("path:{}".format(e.path))
            sys.exit()

        LOG.info("Data validation Passed!")

    def _apply_design_rules(self):
        """ Applies design rules from rules.yaml


        These rules are used to determine ip address allocation ranges,
        host profile interfaces and also to create hardware profile
        information. The method calls corresponding rule hander function
        based on rule name and applies them to appropriate data objects.
        """
        LOG.info("Apply design rules")
        rules_dir = pkg_resources.resource_filename('spyglass', 'config/')
        rules_file = rules_dir + 'rules.yaml'
        rules_data_raw = self._read_file(rules_file)
        rules_yaml = yaml.safe_load(rules_data_raw)
        rules_data = {}
        rules_data.update(rules_yaml)
        for rule in rules_data.keys():
            rule_name = rules_data[rule]['name']
            function_str = "_apply_rule_" + rule_name
            rule_data_name = rules_data[rule][rule_name]
            function = getattr(self, function_str)
            function(rule_data_name)
            LOG.info("Applying rule:{}".format(rule_name))

    def _apply_rule_host_profile_interfaces(self, rule_data):
        # TODO(pg710r)Nothing to do as of now since host profile
        # information is already present in plugin data.
        # This function shall be defined if plugin data source
        # doesn't provide host profile information.
        pass

    def _apply_rule_hardware_profile(self, rule_data):
        """ Apply rules to define host type from hardware profile info.


        Host profile will define host types as "controller, compute or
        genesis". The rule_data has pre-defined information to define
        compute or controller based on host_profile. For defining 'genesis'
        the first controller host is defined as genesis."""
        is_genesis = False
        hardware_profile = rule_data[self.data['site_info']['sitetype']]
        # Getting individual racks. The racks are sorted to ensure that the
        # first controller of the first rack is assigned as 'genesis' node.
        for rack in sorted(self.data['baremetal'].keys()):
            # Getting individual hosts in each rack. Sorting of the hosts are
            # done to determine the genesis node.
            for host in sorted(self.data['baremetal'][rack].keys()):
                host_info = self.data['baremetal'][rack][host]
                if (host_info['host_profile'] == hardware_profile[
                        'profile_name']['ctrl']):
                    if not is_genesis:
                        host_info['type'] = 'genesis'
                        is_genesis = True
                    else:
                        host_info['type'] = 'controller'
                else:
                    host_info['type'] = 'compute'

    def _apply_rule_ip_alloc_offset(self, rule_data):
        """ Apply  offset rules to update baremetal host ip's and vlan network
        data """

        # Get network subnets
        self.network_subnets = self._get_network_subnets()

        self._update_vlan_net_data(rule_data)
        self._update_baremetal_host_ip_data(rule_data)

    def _update_baremetal_host_ip_data(self, rule_data):
        """ Update baremetal host ip's for applicable networks.


        The applicable networks are oob, oam, ksn, storage and overlay.
        These IPs are assigned based on network subnets ranges.
        If a particular ip exists it is overridden."""

        # Ger defult ip offset
        default_ip_offset = rule_data['default']

        host_idx = 0
        LOG.info("Update baremetal host ip's")
        for racks in self.data['baremetal'].keys():
            rack_hosts = self.data['baremetal'][racks]
            for host in rack_hosts:
                host_networks = rack_hosts[host]['ip']
                for net in host_networks:
                    ips = list(self.network_subnets[net])
                    host_networks[net] = str(ips[host_idx + default_ip_offset])
                host_idx = host_idx + 1

        LOG.debug("Updated baremetal host:\n{}".format(
            pprint.pformat(self.data['baremetal'])))

    def _update_vlan_net_data(self, rule_data):
        """ Offset allocation rules to determine ip address range(s)


        This rule is applied to incoming network data to determine
        network address, gateway ip and other address ranges
        """
        LOG.info("Apply network design rules")

        # Collect Rules
        default_ip_offset = rule_data['default']
        oob_ip_offset = rule_data['oob']
        gateway_ip_offset = rule_data['gateway']
        ingress_vip_offset = rule_data['ingress_vip']
        # static_ip_end_offset for non pxe network
        static_ip_end_offset = rule_data['static_ip_end']
        # dhcp_ip_end_offset for pxe network
        dhcp_ip_end_offset = rule_data['dhcp_ip_end']

        # Set ingress vip and CIDR for bgp
        LOG.info("Apply network design rules:bgp")
        subnet = netaddr.IPNetwork(
            self.data['network']['vlan_network_data']['ingress']['subnet'][0])
        ips = list(subnet)
        self.data['network']['bgp']['ingress_vip'] = str(
            ips[ingress_vip_offset])
        self.data['network']['bgp']['public_service_cidr'] = self.data[
            'network']['vlan_network_data']['ingress']['subnet'][0]
        LOG.debug("Updated network bgp data:\n{}".format(
            pprint.pformat(self.data['network']['bgp'])))

        LOG.info("Apply network design rules:vlan")
        # Apply rules to vlan networks
        for net_type in self.network_subnets:
            if net_type == 'oob':
                ip_offset = oob_ip_offset
            else:
                ip_offset = default_ip_offset

            subnet = self.network_subnets[net_type]
            ips = list(subnet)

            self.data['network']['vlan_network_data'][net_type][
                'gateway'] = str(ips[gateway_ip_offset])

            self.data['network']['vlan_network_data'][net_type][
                'reserved_start'] = str(ips[1])
            self.data['network']['vlan_network_data'][net_type][
                'reserved_end'] = str(ips[ip_offset])

            static_start = str(ips[ip_offset + 1])
            static_end = str(ips[static_ip_end_offset])

            if net_type == 'pxe':
                mid = len(ips) // 2
                static_end = str(ips[mid - 1])
                dhcp_start = str(ips[mid])
                dhcp_end = str(ips[dhcp_ip_end_offset])

                self.data['network']['vlan_network_data'][net_type][
                    'dhcp_start'] = dhcp_start
                self.data['network']['vlan_network_data'][net_type][
                    'dhcp_end'] = dhcp_end

            self.data['network']['vlan_network_data'][net_type][
                'static_start'] = static_start
            self.data['network']['vlan_network_data'][net_type][
                'static_end'] = static_end

            # There is no vlan for oob network
            if (net_type != 'oob'):
                self.data['network']['vlan_network_data'][net_type][
                    'vlan'] = self.data['network']['vlan_network_data'][
                        net_type]['vlan']

            # OAM have default routes. Only for cruiser. TBD
            if (net_type == 'oam'):
                routes = ["0.0.0.0/0"]
            else:
                routes = []
            self.data['network']['vlan_network_data'][net_type][
                'routes'] = routes

        LOG.debug("Updated vlan network data:\n{}".format(
            pprint.pformat(self.data['network']['vlan_network_data'])))

    def load_extracted_data_from_data_source(self, extracted_data):
        """
        Function called from spyglass.py to pass extracted data
        from input data source
        """
        # TBR(pg710r): for internal testing
        """
        raw_data = self._read_file('extracted_data.yaml')
        extracted_data = yaml.safe_load(raw_data)
        """

        LOG.info("Loading plugin data source")
        self.data = extracted_data
        LOG.debug("Extracted data from plugin:\n{}".format(
            pprint.pformat(extracted_data)))
        extracted_file = "extracted_file.yaml"
        yaml_file = yaml.dump(extracted_data, default_flow_style=False)
        with open(extracted_file, 'w') as f:
            f.write(yaml_file)
        f.close()

        # Append region_data supplied from CLI to self.data
        self.data['region_name'] = self.region_name

    def dump_intermediary_file(self, intermediary_dir):
        """ Writing intermediary yaml """
        LOG.info("Writing intermediary yaml")
        intermediary_file = "{}_intermediary.yaml".format(
            self.data['region_name'])
        # Check of if output dir = intermediary_dir exists
        if intermediary_dir is not None:
            outfile = "{}/{}".format(intermediary_dir, intermediary_file)
        else:
            outfile = intermediary_file
        LOG.info("Intermediary file:{}".format(outfile))
        yaml_file = yaml.dump(self.data, default_flow_style=False)
        with open(outfile, 'w') as f:
            f.write(yaml_file)
        f.close()

    def generate_intermediary_yaml(self, edit_intermediary=False):
        """ Generating intermediary yaml """
        LOG.info("Start: Generate Intermediary")
        self._apply_design_rules()
        self._get_genesis_node_details()
        # This will validate the extracted data from different sources.
        self._validate_intermediary_data(self.data)
        if edit_intermediary:
            self.edit_intermediary_yaml()
            # This will check if user edited changes are in order.
            self._validate_intermediary_data(self.data)
        self.intermediary_yaml = self.data
        return self.intermediary_yaml

    def edit_intermediary_yaml(self):
        """ Edit generated data using on browser """
        LOG.info(
            "edit_intermediary_yaml: Invoking web server for yaml editing")
        with tempfile.NamedTemporaryFile(mode='r+') as file_obj:
            yaml.safe_dump(self.data, file_obj, default_flow_style=False)
            host = self._get_genesis_node_ip()
            os.system('yaml-editor -f {0} -h {1}'.format(file_obj.name, host))
            file_obj.seek(0)
            self.data = yaml.safe_load(file_obj)
