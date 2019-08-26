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

import json
import logging
import os
import pprint

from jsonschema import Draft7Validator
from netaddr import IPNetwork
from pkg_resources import resource_filename
import yaml

from spyglass import exceptions

LOG = logging.getLogger(__name__)


class ProcessDataSource(object):
    def __init__(
            self,
            region,
            extracted_data,
            intermediary_schema=None,
            no_validation=True):
        # Initialize intermediary and save site type
        self.host_type = {}
        self.sitetype = None
        self.genesis_node = None
        self.network_subnets = None
        self.region_name = region
        self.no_validation = no_validation
        if intermediary_schema and not self.no_validation:
            with open(intermediary_schema, 'r') as loaded_schema:
                self.intermediary_schema = json.load(loaded_schema)

        LOG.info("Loading plugin data source")
        self.data = extracted_data
        LOG.debug(
            "Extracted data from plugin:\n{}".format(
                pprint.pformat(extracted_data)))

    @staticmethod
    def _read_file(file_name):
        with open(file_name, "r") as f:
            raw_data = f.read()
        return raw_data

    def _get_network_subnets(self):
        """Extract subnet information for networks.

        In some networks, there are multiple subnets, in that case
        we assign only the first subnet
        """

        LOG.info("Extracting network subnets")
        network_subnets = {}
        for net_type in self.data.network.vlan_network_data:
            # One of the type is ingress and we don't want that here
            if net_type.name != "ingress":
                network_subnets[net_type.name] = IPNetwork(net_type.subnet[0])

        LOG.debug(
            "Network subnets:\n{}".format(pprint.pformat(network_subnets)))
        return network_subnets

    def _get_genesis_node_details(self):
        """Get genesis host node details from the hosts based on host type"""
        for host in self.data.get_baremetal_host_by_type('genesis'):
            self.genesis_node = host
        LOG.debug(
            "Genesis Node Details:\n{}".format(
                pprint.pformat(self.genesis_node)))

    def _validate_intermediary_data(self):
        """Validates the intermediary data before generating manifests.

        It checks whether the data types and data format are as expected.
        The method validates this with regex pattern defined for each
        data type.
        """

        LOG.info("Validating Intermediary data")
        validator = Draft7Validator(self.intermediary_schema)
        errors = sorted(
            validator.iter_errors(self.data.dict_from_class()),
            key=lambda e: e.path)
        if errors:
            raise exceptions.IntermediaryValidationException(errors=errors)

        LOG.info("Data validation Passed!")
        return

    def _apply_design_rules(self):
        """Applies design rules from rules.yaml

        These rules are used to determine ip address allocation ranges,
        host profile interfaces and also to create hardware profile
        information. The method calls corresponding rule handler function
        based on rule name and applies them to appropriate data objects.
        """

        LOG.info("Apply design rules")
        # TODO(ian-pittwood): We may want to let users specify these in cli
        #                     opts. We also need better guidelines over how
        #                     to write these rules and how they are applied.

        rules_dir = resource_filename("spyglass", "config/")
        rules_file = os.path.join(rules_dir, "rules.yaml")
        rules_data_raw = self._read_file(rules_file)
        rules_yaml = yaml.safe_load(rules_data_raw)
        for rule in rules_yaml.keys():
            rule_name = rules_yaml[rule]["name"]
            function_str = "_apply_rule_" + rule_name
            rule_data_name = rules_yaml[rule][rule_name]
            function = getattr(self, function_str)
            function(rule_data_name)
            LOG.info("Applying rule:{}".format(rule_name))

    def _apply_rule_hardware_profile(self, rule_data):
        """Apply rules to define host type from hardware profile info.

        Host profile will define host types as "controller, compute or
        genesis". The rule_data has pre-defined information to define
        compute or controller based on host_profile. For defining 'genesis'
        the first controller host is defined as genesis.
        """

        is_genesis = False
        hardware_profile = rule_data[self.data.site_info.sitetype]
        # Getting individual racks. The racks are sorted to ensure that the
        # first controller of the first rack is assigned as 'genesis' node.
        for rack in sorted(self.data.baremetal, key=lambda x: x.name):
            # Getting individual hosts in each rack. Sorting of the hosts are
            # done to determine the genesis node.
            for host in sorted(rack.hosts, key=lambda x: x.name):
                if host.host_profile == \
                        hardware_profile["profile_name"]["ctrl"]:
                    if not is_genesis:
                        host.type = "genesis"
                        is_genesis = True
                    else:
                        host.type = "controller"
                else:
                    host.type = "compute"

    def _apply_rule_ip_alloc_offset(self, rule_data):
        """Apply offset rules to update baremetal host

        ip's and vlan network
        """

        # Get network subnets
        self.network_subnets = self._get_network_subnets()

        self._update_vlan_net_data(rule_data)
        self._update_baremetal_host_ip_data(rule_data)

    def _update_baremetal_host_ip_data(self, rule_data):
        """Update baremetal host ip's for applicable networks.

        The applicable networks are oob, oam, ksn, storage and overlay.
        These IPs are assigned based on network subnets ranges.
        If a particular ip exists it is overridden.
        """

        # Ger default ip offset
        default_ip_offset = rule_data["default"]

        host_idx = 0
        LOG.info("Update baremetal host ip's")
        for rack in self.data.baremetal:
            for host in rack.hosts:
                for net_type, net_ip in iter(host.ip):
                    ips = list(self.network_subnets[net_type])
                    host.ip.set_ip_by_role(
                        net_type, str(ips[host_idx + default_ip_offset]))
                host_idx += 1
        return

    def _update_vlan_net_data(self, rule_data):
        """Offset allocation rules to determine ip address range(s)

        This rule is applied to incoming network data to determine
        network address, gateway ip and other address ranges
        """

        LOG.info("Apply network design rules")

        # Collect Rules
        default_ip_offset = rule_data["default"]
        oob_ip_offset = rule_data["oob"]
        gateway_ip_offset = rule_data["gateway"]
        ingress_vip_offset = rule_data["ingress_vip"]
        # static_ip_end_offset for non pxe network
        static_ip_end_offset = rule_data["static_ip_end"]
        # dhcp_ip_end_offset for pxe network
        dhcp_ip_end_offset = rule_data["dhcp_ip_end"]

        # Set ingress vip and CIDR for bgp
        LOG.info("Apply network design rules:bgp")
        ingress_data = self.data.network.get_vlan_data_by_name('ingress')
        subnet = IPNetwork(ingress_data.subnet[0])
        ips = list(subnet)
        self.data.network.bgp["ingress_vip"] = \
            str(ips[ingress_vip_offset])
        self.data.network.bgp["public_service_cidr"] = \
            ingress_data.subnet[0]
        LOG.debug(
            "Updated network bgp data:\n{}".format(
                pprint.pformat(self.data.network.bgp)))

        LOG.info("Apply network design rules:vlan")
        # Apply rules to vlan networks
        for net_type in self.network_subnets.keys():
            vlan_network_data_ = \
                self.data.network.get_vlan_data_by_name(net_type)
            if net_type == "oob":
                ip_offset = oob_ip_offset
            else:
                ip_offset = default_ip_offset

            subnet = self.network_subnets[net_type]
            ips = list(subnet)

            vlan_network_data_.gateway = str(ips[gateway_ip_offset])

            vlan_network_data_.reserved_start = str(ips[1])
            vlan_network_data_.reserved_end = str(ips[ip_offset])

            static_start = str(ips[ip_offset + 1])
            static_end = str(ips[static_ip_end_offset])

            if net_type == "pxe":
                mid = len(ips) // 2
                static_end = str(ips[mid - 1])
                dhcp_start = str(ips[mid])
                dhcp_end = str(ips[dhcp_ip_end_offset])

                vlan_network_data_.dhcp_start = dhcp_start
                vlan_network_data_.dhcp_end = dhcp_end

            vlan_network_data_.static_start = static_start
            vlan_network_data_.static_end = static_end

            # OAM have default routes. Only for cruiser. TBD
            if net_type == "oam":
                vlan_network_data_.routes = ["0.0.0.0/0"]  # nosec
            else:
                vlan_network_data_.routes = []

        LOG.debug(
            "Updated vlan network data:\n{}".format(
                pprint.pformat(vlan_network_data_.dict_from_class())))

    def dump_intermediary_file(self, intermediary_dir):
        """Writing intermediary yaml"""

        LOG.info("Writing intermediary yaml")
        intermediary_file = "{}_intermediary.yaml" \
                            .format(self.region_name)
        # Check of if output dir = intermediary_dir exists
        if intermediary_dir is not None:
            outfile = os.path.join(intermediary_dir, intermediary_file)
        else:
            outfile = intermediary_file
        LOG.info("Intermediary file:{}".format(outfile))
        yaml_file = yaml.dump(
            self.data.dict_from_class(), default_flow_style=False)
        with open(outfile, "w") as f:
            f.write(yaml_file)
        f.close()

    def generate_intermediary_yaml(self):
        """Generating intermediary yaml"""

        LOG.info("Start: Generate Intermediary")
        self._apply_design_rules()
        self._get_genesis_node_details()
        # This will validate the extracted data from different sources.
        if not self.no_validation and self.intermediary_schema:
            self._validate_intermediary_data()
        return self.data
