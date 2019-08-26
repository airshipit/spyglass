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
import unittest
from unittest import mock

from netaddr import IPNetwork
from pytest import mark

from spyglass import exceptions
from spyglass.parser.engine import ProcessDataSource

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared')


@mark.usefixtures('tmpdir')
@mark.usefixtures('site_document_data_objects')
@mark.usefixtures('invalid_site_document_data_objects')
@mark.usefixtures('rules_data')
class TestProcessDataSource(unittest.TestCase):
    REGION_NAME = 'test'

    def test___init__(self):
        expected_data = 'data'
        obj = ProcessDataSource(self.REGION_NAME, expected_data)
        self.assertEqual(self.REGION_NAME, obj.region_name)
        self.assertDictEqual({}, obj.host_type)
        self.assertEqual(expected_data, obj.data)
        self.assertIsNone(obj.sitetype)
        self.assertIsNone(obj.genesis_node)
        self.assertIsNone(obj.network_subnets)

    def test__read_file(self):
        test_file = os.path.join(FIXTURE_DIR, 'site_config.yaml')
        with open(test_file, 'r') as f:
            expected_data = f.read()
        data = ProcessDataSource._read_file(test_file)
        self.assertEqual(expected_data, data)

    def test__get_network_subnets(self):
        expected_result = {
            'calico': IPNetwork('30.29.1.0/25'),
            'oam': IPNetwork('10.0.220.0/26'),
            'oob': IPNetwork('10.0.220.128/27'),
            'overlay': IPNetwork('30.19.0.0/25'),
            'pxe': IPNetwork('30.30.4.0/25'),
            'storage': IPNetwork('30.31.1.0/25')
        }
        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        result = obj._get_network_subnets()
        self.assertDictEqual(expected_result, result)

    def test__get_genesis_node_details(self):
        expected_result = self.site_document_data.get_baremetal_host_by_type(
            'genesis')[0]

        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        obj._get_genesis_node_details()
        self.assertEqual(expected_result, obj.genesis_node)

    def test__validate_intermediary_data(self):
        schema_path = os.path.join(FIXTURE_DIR, 'intermediary_schema.json')
        obj = ProcessDataSource(
            self.REGION_NAME, self.site_document_data, schema_path, False)
        result = obj._validate_intermediary_data()
        self.assertIsNone(result)

    def test__validate_intermediary_data_invalid(self):
        schema_path = os.path.join(FIXTURE_DIR, 'intermediary_schema.json')
        obj = ProcessDataSource(
            self.REGION_NAME, self.invalid_site_document_data, schema_path,
            False)
        with self.assertRaises(exceptions.IntermediaryValidationException):
            obj._validate_intermediary_data()

    @mock.patch.object(ProcessDataSource, '_apply_rule_ip_alloc_offset')
    @mock.patch.object(ProcessDataSource, '_apply_rule_hardware_profile')
    def test__apply_design_rules(
            self, mock_rule_hw_profile, mock_rule_ip_alloc_offset):
        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        obj._apply_design_rules()
        mock_rule_hw_profile.assert_called_once()
        mock_rule_ip_alloc_offset.assert_called_once()

    def test__apply_rule_hardware_profile(self):
        input_rules = self.rules_data['rule_hardware_profile'][
            'hardware_profile']

        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        obj._apply_rule_hardware_profile(input_rules)
        self.assertEqual(
            1, len(obj.data.get_baremetal_host_by_type('genesis')))
        self.assertEqual(
            3, len(obj.data.get_baremetal_host_by_type('controller')))
        self.assertEqual(
            8, len(obj.data.get_baremetal_host_by_type('compute')))
        for host in obj.data.get_baremetal_host_by_type('genesis'):
            self.assertEqual('cp-r720', host.host_profile)
        for host in obj.data.get_baremetal_host_by_type('controller'):
            self.assertEqual('cp-r720', host.host_profile)
        for host in obj.data.get_baremetal_host_by_type('compute'):
            self.assertEqual('dp-r720', host.host_profile)

    @mock.patch.object(ProcessDataSource, '_update_baremetal_host_ip_data')
    @mock.patch.object(ProcessDataSource, '_update_vlan_net_data')
    @mock.patch.object(
        ProcessDataSource, '_get_network_subnets', return_value='success')
    def test__apply_rule_ip_alloc_offset(
            self, mock__get_network_subnets, mock__update_vlan_net_data,
            mock__update_baremetal_host_ip_data):
        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        obj._apply_rule_ip_alloc_offset(self.rules_data)
        self.assertEqual('success', obj.network_subnets)
        mock__get_network_subnets.assert_called_once()
        mock__update_vlan_net_data.assert_called_once_with(self.rules_data)
        mock__update_baremetal_host_ip_data.assert_called_once_with(
            self.rules_data)

    def test__update_baremetal_host_ip_data(self):
        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        obj.network_subnets = obj._get_network_subnets()
        ip_alloc_offset_rules = self.rules_data['rule_ip_alloc_offset'][
            'ip_alloc_offset']
        obj._update_baremetal_host_ip_data(ip_alloc_offset_rules)

        counter = 0
        for rack in obj.data.baremetal:
            for host in rack.hosts:
                for net_type, net_ip in iter(host.ip):
                    ips = list(obj.network_subnets[net_type])
                    self.assertEqual(
                        str(ips[counter + ip_alloc_offset_rules['default']]),
                        net_ip)
                counter += 1

    def test__update_vlan_net_data(self):
        ip_alloc_offset_rules = self.rules_data['rule_ip_alloc_offset'][
            'ip_alloc_offset']

        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        obj.network_subnets = obj._get_network_subnets()
        obj._update_vlan_net_data(ip_alloc_offset_rules)

        ingress_data = obj.data.network.get_vlan_data_by_name('ingress')
        subnet = IPNetwork(ingress_data.subnet[0])
        ips = list(subnet)
        self.assertEqual(
            str(ips[ip_alloc_offset_rules['ingress_vip']]),
            obj.data.network.bgp['ingress_vip'])
        self.assertEqual(
            ingress_data.subnet[0],
            obj.data.network.bgp['public_service_cidr'])
        subnets = obj.network_subnets
        for vlan in self.site_document_data.network.vlan_network_data:
            if vlan.role == 'ingress':
                continue
            ips = list(subnets[vlan.role])
            self.assertEqual(
                str(ips[ip_alloc_offset_rules['gateway']]), vlan.gateway)

            if vlan.role == 'oob':
                ip_offset = ip_alloc_offset_rules['oob']
            else:
                ip_offset = ip_alloc_offset_rules['default']
            self.assertEqual(str(ips[1]), vlan.reserved_start)
            self.assertEqual(str(ips[ip_offset]), vlan.reserved_end)
            self.assertEqual(str(ips[ip_offset + 1]), vlan.static_start)

            if vlan.role == 'pxe':
                self.assertEqual(
                    str(ips[(len(ips) // 2) - 1]), vlan.static_end)
                self.assertEqual(str(ips[len(ips) // 2]), vlan.dhcp_start)
                self.assertEqual(
                    str(ips[ip_alloc_offset_rules['dhcp_ip_end']]),
                    vlan.dhcp_end)
            else:
                self.assertEqual(
                    str(ips[ip_alloc_offset_rules['static_ip_end']]),
                    vlan.static_end)

            if vlan.role == 'oam':
                self.assertEqual(['0.0.0.0/0'], vlan.routes)
            else:
                self.assertEqual([], vlan.routes)

    def test_load_extracted_data_from_data_source(self):
        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        self.assertEqual(self.site_document_data, obj.data)

    @mock.patch('yaml.dump', return_value='success')
    def test_dump_intermediary_file(self, mock_dump):
        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        mock_open = mock.mock_open()
        with mock.patch('spyglass.parser.engine.open', mock_open):
            obj.dump_intermediary_file(None)
        mock_dump.assert_called_once_with(
            self.site_document_data.dict_from_class(),
            default_flow_style=False)
        mock_open.return_value.write.assert_called_once()
        mock_open.return_value.close.assert_called_once()

    @mock.patch.object(ProcessDataSource, '_apply_design_rules')
    @mock.patch.object(ProcessDataSource, '_get_genesis_node_details')
    def test_generate_intermediary_yaml(
            self, mock__apply_design_rules, mock__get_genesis_node_details):
        obj = ProcessDataSource(self.REGION_NAME, self.site_document_data)
        result = obj.generate_intermediary_yaml()
        self.assertEqual(self.site_document_data, result)
        mock__apply_design_rules.assert_called_once()
        mock__get_genesis_node_details.assert_called_once()
