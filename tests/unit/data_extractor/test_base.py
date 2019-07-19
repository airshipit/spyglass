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

import unittest
from unittest import mock

from spyglass.data_extractor.base import BaseDataSourcePlugin
from spyglass.data_extractor import models


class TestBaseDataSourcePlugin(unittest.TestCase):

    REGION = 'test'

    @mock.patch.multiple(BaseDataSourcePlugin, __abstractmethods__=set())
    def setUp(self):
        self.instance = BaseDataSourcePlugin(self.REGION)

    def test___init__(self):
        self.assertIsNone(self.instance.source_type)
        self.assertIsNone(self.instance.source_name)
        self.assertEqual(self.REGION, self.instance.region)
        self.assertIsNone(self.instance.raw_data)
        self.assertIsNone(self.instance.data)

    @mock.patch.object(
        BaseDataSourcePlugin, 'parse_racks', return_value='success')
    def test_parse_baremetal_information(self, mock_parse_racks):
        result = self.instance.parse_baremetal_information()
        self.assertEqual('success', result)
        mock_parse_racks.assert_called_once()

    @mock.patch.object(
        BaseDataSourcePlugin, 'parse_dns_servers', return_value='1.1.1.1')
    @mock.patch.object(
        BaseDataSourcePlugin, 'parse_ntp_servers', return_value='2.2.2.2')
    @mock.patch.object(
        BaseDataSourcePlugin,
        'parse_ldap_information',
        return_value={
            'common_name': 'test',
            'url': 'ldap://ldap.example.com',
            'subdomain': 'test'
        })
    @mock.patch.object(
        BaseDataSourcePlugin, 'parse_domain_name', return_value='example.com')
    @mock.patch.object(
        BaseDataSourcePlugin,
        'parse_location_information',
        return_value={
            'corridor': 'c1',
            'country': 'USA',
            'state': 'IL',
            'physical_location_id': 1,
            'sitetype': 'foundry',
            'name': 'ExampleSiteName'
        })
    def test_parse_site_information(
            self, mock_parse_location, mock_parse_domain, mock_parse_ldap,
            mock_parse_ntp, mock_parse_dns):
        expected_data = {
            'dns': {
                'servers': '1.1.1.1'
            },
            'ntp': {
                'servers': '2.2.2.2'
            },
            'ldap': {
                'common_name': 'test',
                'url': 'ldap://ldap.example.com',
                'subdomain': 'test'
            },
            'domain': 'example.com',
            'corridor': 'c1',
            'country': 'USA',
            'state': 'IL',
            'physical_location_id': 1,
            'sitetype': 'foundry',
            'name': 'ExampleSiteName'
        }
        result = self.instance.parse_site_information()
        self.assertIsInstance(result, models.SiteInfo)
        self.assertEqual(self.REGION, result.region_name)
        self.assertDictEqual(expected_data, result.dict_from_class())

    @mock.patch.object(BaseDataSourcePlugin, 'parse_networks')
    @mock.patch('spyglass.data_extractor.models.Network', autospec=True)
    def test_parse_network_information(self, Network, mock_parse_networks):
        vlan1 = mock.MagicMock(models.VLANNetworkData)
        vlan1.name = 'oam'
        vlan2 = mock.MagicMock(models.VLANNetworkData)
        vlan2.name = 'dne'
        vlan3 = mock.MagicMock(models.VLANNetworkData)
        vlan3.name = 'pxe'
        mock_parse_networks.return_value = [vlan1, vlan2, vlan3]
        self.instance.parse_network_information()
        Network.assert_called_once_with([vlan1, vlan3])

    @mock.patch.object(
        BaseDataSourcePlugin,
        'parse_site_information',
        return_value='site_info')
    @mock.patch.object(
        BaseDataSourcePlugin,
        'parse_network_information',
        return_value='network_info')
    @mock.patch.object(
        BaseDataSourcePlugin,
        'parse_baremetal_information',
        return_value='baremetal_info')
    @mock.patch.object(models.SiteDocumentData, '__init__', return_value=None)
    def test_parse_data_objects(
            self, mock_init, mock_parse_baremetal, mock_parse_network,
            mock_parse_site):
        self.instance.parse_data_objects()
        mock_init.assert_called_once_with(
            'site_info', 'network_info', 'baremetal_info')

    def test_merge_additional_data(self):
        self.instance.data = mock.MagicMock(models.SiteDocumentData)
        extra = 'data'
        self.instance.merge_additional_data(extra)
        self.instance.data.merge_additional_data.assert_called_once_with(extra)

    @mock.patch.object(BaseDataSourcePlugin, 'load_raw_data')
    @mock.patch.object(BaseDataSourcePlugin, 'parse_data_objects')
    def test_get_data(self, mock_parse_data_objects, mock_load_raw_data):
        self.instance.data = 'data'
        self.instance.get_data()
        mock_parse_data_objects.assert_called_once()
        mock_load_raw_data.assert_called_once()

    @mock.patch.object(BaseDataSourcePlugin, 'load_raw_data')
    @mock.patch.object(BaseDataSourcePlugin, 'parse_data_objects')
    @mock.patch.object(BaseDataSourcePlugin, 'merge_additional_data')
    def test_get_data_extra_data_defined(
            self, mock_merge, mock_parse_data_objects, mock_load_raw_data):
        extra_data = 'extra_data'
        self.instance.data = 'data'
        self.instance.get_data(extra_data)
        mock_parse_data_objects.assert_called_once()
        mock_load_raw_data.assert_called_once()
        mock_merge.assert_called_once_with(extra_data)
