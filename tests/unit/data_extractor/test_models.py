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

from copy import copy
import os
import unittest
from unittest import mock

import yaml

from spyglass.data_extractor import models
from spyglass.exceptions import InvalidIntermediary

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared')


class TestParseIp(unittest.TestCase):
    """Tests the _parse_ip validator for Spyglass models"""
    def test__parse_ip(self):
        """Tests basic function of _parse_ip validator"""
        addr = '10.23.0.1'
        result = models._parse_ip(addr)
        self.assertEqual(addr, result)

    def test__parse_ip_bad_ip(self):
        """Tests that invalid IP addresses are logged as a warning and returned

        without changes
        """
        addr = 'not4nip4ddr3$$'
        expected_message = '%s is not a valid IP address.' % addr
        with self.assertLogs(level='WARNING') as test_log:
            result = models._parse_ip(addr)
            self.assertEqual(len(test_log.output), 1)
            self.assertEqual(len(test_log.records), 1)
            self.assertIn(expected_message, test_log.output[0])
        self.assertEqual(addr, result)


class TestServerList(unittest.TestCase):
    """Tests for the ServerList model"""

    VALID_SERVERS = ['121.12.13.1', '193.153.1.1', '12.23.9.11']
    INVALID_SERVERS = ['not4nip4ddr3$$', '124.34.1.1', 'ALSONOTVALID']

    def test___init__(self):
        """Tests basic initialization of ServerList"""
        result = models.ServerList(self.VALID_SERVERS)
        self.assertEqual(set(self.VALID_SERVERS), set(result.servers))

    def test___init___invalid_servers(self):
        """Tests initialization of ServerList with bad IPs

        If ServerList is given IP addresses that appear invalid, it should log
        warnings for the user. ServerList should still initialize regardless
        of the IPs it is given.
        """
        expected_messages = [
            '%s is not a valid IP address.' % self.INVALID_SERVERS[0],
            '%s is not a valid IP address.' % self.INVALID_SERVERS[2]
        ]
        with self.assertLogs(level='WARNING') as test_log:
            result = models.ServerList(self.INVALID_SERVERS)
            self.assertEqual(len(test_log.output), 2)
            self.assertEqual(len(test_log.records), 2)
            self.assertIn(expected_messages[0], test_log.output[0])
            self.assertIn(expected_messages[1], test_log.output[1])
        self.assertEqual(set(self.INVALID_SERVERS), set(result.servers))

    def test___str__(self):
        """Tests str type casting for ServerList"""
        expected_result = ','.join(self.VALID_SERVERS)
        result = models.ServerList(self.VALID_SERVERS)
        self.assertEqual(expected_result, str(result))

    def test___iter__(self):
        """Tests iterator builtin for ServerList"""
        result = models.ServerList(self.VALID_SERVERS)
        iterator = iter(result)
        self.assertEqual(iterator.__next__(), self.VALID_SERVERS[0])
        self.assertEqual(iterator.__next__(), self.VALID_SERVERS[1])
        self.assertEqual(iterator.__next__(), self.VALID_SERVERS[2])

    def test_merge_list(self):
        """Tests that ServerList can merge additional servers from a list

        ServerList should be able to accept a list type object of IP address
        strings and merge them into its current list of servers.
        """
        list_to_merge = ['1.1.1.1', '2.2.2.2']
        result = models.ServerList(self.VALID_SERVERS)
        self.assertEqual(set(self.VALID_SERVERS), set(result.servers))
        expected_result = [*self.VALID_SERVERS, *list_to_merge]
        result.merge(list_to_merge)
        self.assertEqual(set(expected_result), set(result.servers))

    def test_merge_str(self):
        """Tests that ServerList can merge additional servers from a str

        ServerList should be able to accept a comma separated list of IP
        addresses as strings and merge them into its current list of servers.
        """
        list_to_merge = '1.1.1.1,2.2.2.2'
        result = models.ServerList(self.VALID_SERVERS)
        self.assertEqual(set(self.VALID_SERVERS), set(result.servers))
        expected_result = [*self.VALID_SERVERS, *(list_to_merge.split(','))]
        result.merge(list_to_merge)
        self.assertEqual(set(expected_result), set(result.servers))


class TestIPList(unittest.TestCase):
    """Tests for the IPList model"""

    VALID_IP = {
        'oob': '14.102.252.126',
        'oam': '120.145.167.87',
        'calico': '46.12.178.235',
        'overlay': '226.208.39.49',
        'pxe': '164.99.192.149',
        'storage': '252.63.220.22'
    }
    INVALID_IP = {
        'oob': '14.102.252.126',
        'oam': 'not4nip4ddr3$$',
        'calico': '46.12.178.235',
        'overlay': '226.208.39.49',
        'pxe': '164.99.192.149',
        'storage': '252.63.220.22'
    }
    MISSING_IP = {
        'oob': '14.102.252.126',
        'calico': '46.12.178.235',
        'overlay': '226.208.39.49',
        'pxe': '164.99.192.149',
        'storage': '252.63.220.22'
    }

    def test___init__(self):
        """Tests basic initialization of an IPList"""
        result = models.IPList(**self.VALID_IP)
        self.assertEqual(self.VALID_IP['oob'], result.oob)
        self.assertEqual(self.VALID_IP['oam'], result.oam)
        self.assertEqual(self.VALID_IP['calico'], result.calico)
        self.assertEqual(self.VALID_IP['overlay'], result.overlay)
        self.assertEqual(self.VALID_IP['pxe'], result.pxe)
        self.assertEqual(self.VALID_IP['storage'], result.storage)

    def test___init___invalid_ip(self):
        """Tests initialization of an IPList using invalid IPs

        When invalid IP addresses are given to IPList, it should log a warning
        to the user using _parse_ip(). IPList should still be created using
        the invalid address.
        """
        expected_message = \
            '%s is not a valid IP address.' % self.INVALID_IP['oam']
        with self.assertLogs(level='WARNING') as test_log:
            result = models.IPList(**self.INVALID_IP)
            self.assertEqual(len(test_log.output), 1)
            self.assertEqual(len(test_log.records), 1)
            self.assertIn(expected_message, test_log.output[0])
        self.assertEqual(self.INVALID_IP['oob'], result.oob)
        self.assertEqual(self.INVALID_IP['oam'], result.oam)
        self.assertEqual(self.INVALID_IP['calico'], result.calico)
        self.assertEqual(self.INVALID_IP['overlay'], result.overlay)
        self.assertEqual(self.INVALID_IP['pxe'], result.pxe)
        self.assertEqual(self.INVALID_IP['storage'], result.storage)

    def test___init___missing_ip(self):
        """Tests initialization of an IPList with an entry missing

        IPList should automatically fill in any missing entries with the value
        set by models.DATA_DEFAULT.
        """
        result = models.IPList(**self.MISSING_IP)
        self.assertEqual(self.MISSING_IP['oob'], result.oob)
        self.assertEqual(models.DATA_DEFAULT, result.oam)
        self.assertEqual(self.MISSING_IP['calico'], result.calico)
        self.assertEqual(self.MISSING_IP['overlay'], result.overlay)
        self.assertEqual(self.MISSING_IP['pxe'], result.pxe)
        self.assertEqual(self.MISSING_IP['storage'], result.storage)

    def test___iter__(self):
        """Tests iterator builtin for IPList

        When iter() is called on an IPList, it should yield key-value pairs of
        each role and its associated IP address.
        """
        result = models.IPList(**self.VALID_IP)
        for key, value in result.__iter__():
            self.assertIn(key, self.VALID_IP)
            self.assertEqual(self.VALID_IP[key], value)

    def test_set_ip_by_role(self):
        """Tests setting a single IP by role"""
        result = models.IPList(**self.VALID_IP)
        new_calico_ip = '87.85.178.249'
        result.set_ip_by_role('calico', new_calico_ip)
        self.assertEqual(self.VALID_IP['oob'], result.oob)
        self.assertEqual(self.VALID_IP['oam'], result.oam)
        self.assertEqual(new_calico_ip, result.calico)
        self.assertEqual(self.VALID_IP['overlay'], result.overlay)
        self.assertEqual(self.VALID_IP['pxe'], result.pxe)
        self.assertEqual(self.VALID_IP['storage'], result.storage)

    def test_set_ip_by_role_invalid_role(self):
        """Tests setting an invalid role's IP

        Attempting to set an invalid role should log a warning to the user and
        do nothing to the IPList's data.
        """
        result = models.IPList(**self.VALID_IP)
        new_ip = '87.85.178.249'
        role = 'DNE'
        expected_message = '%s role is not defined for IPList.' % role
        with self.assertLogs(level='WARNING') as test_log:
            result.set_ip_by_role(role, new_ip)
            self.assertEqual(len(test_log.output), 1)
            self.assertEqual(len(test_log.records), 1)
            self.assertIn(expected_message, test_log.output[0])
        self.assertEqual(self.VALID_IP['oob'], result.oob)
        self.assertEqual(self.VALID_IP['oam'], result.oam)
        self.assertEqual(self.VALID_IP['calico'], result.calico)
        self.assertEqual(self.VALID_IP['overlay'], result.overlay)
        self.assertEqual(self.VALID_IP['pxe'], result.pxe)
        self.assertEqual(self.VALID_IP['storage'], result.storage)

    def test_dict_from_class(self):
        """Tests production of a dictionary from IPList"""
        ip_list = models.IPList(**self.VALID_IP)
        result = ip_list.dict_from_class()
        self.assertDictEqual(self.VALID_IP, result)

    def test_dict_from_class_missing_ip(self):
        """Tests production of a dictionary from IPList with a missing IP

        If an IP address is not set for the IPList, it should not appear in the
        dictionary output.
        """
        missing_ip = copy(self.MISSING_IP)
        missing_ip['oam'] = ''
        ip_list = models.IPList(**missing_ip)
        result = ip_list.dict_from_class()
        self.assertDictEqual(self.MISSING_IP, result)

    def test_merge_additional_data(self):
        """Tests merging of additional data dictionaries

        Tests that merging of additional data will set a missing role's IP.
        """
        config_dict = {'oam': '87.85.178.249'}
        ip_list = models.IPList(**self.MISSING_IP)
        ip_list.merge_additional_data(config_dict)
        self.assertEqual(self.MISSING_IP['oob'], ip_list.oob)
        self.assertEqual(config_dict['oam'], ip_list.oam)
        self.assertEqual(self.MISSING_IP['calico'], ip_list.calico)
        self.assertEqual(self.MISSING_IP['overlay'], ip_list.overlay)
        self.assertEqual(self.MISSING_IP['pxe'], ip_list.pxe)
        self.assertEqual(self.MISSING_IP['storage'], ip_list.storage)


class TestHost(unittest.TestCase):
    """Tests for the Host model"""

    HOST_NAME = 'test_host1'
    HOST_DATA = {
        'rack_name': 'rack01',
        'host_profile': 'host',
        'type': 'compute'
    }

    @mock.patch('spyglass.data_extractor.models.IPList', autospec=True)
    def setUp(self, MockIPList):
        """Initializes a mocked IPList"""
        self.MockIPList = MockIPList
        self.HOST_DATA['ip'] = MockIPList()
        self.HOST_DATA['ip'].dict_from_class.return_value = 'success'

    def test___init__(self):
        """Tests basic initialization of Host"""
        result = models.Host(self.HOST_NAME, **self.HOST_DATA)
        self.assertEqual(self.HOST_NAME, result.name)
        self.assertEqual(self.HOST_DATA['rack_name'], result.rack_name)
        self.assertEqual(self.HOST_DATA['host_profile'], result.host_profile)
        self.assertEqual(self.HOST_DATA['type'], result.type)
        self.assertEqual(self.HOST_DATA['ip'], result.ip)

    def test___init___missing_data(self):
        """Tests initialization of Host with missing data

        Unless an attribute is required, Host should automatically fill in the
        value set by models.DATA_DEFAULT for each attribute. The only exception
        is for the Host's ip attribute which will be a new instance of IPList.
        """
        result = models.Host(self.HOST_NAME)
        self.assertEqual(self.HOST_NAME, result.name)
        self.assertEqual(models.DATA_DEFAULT, result.rack_name)
        self.assertEqual(models.DATA_DEFAULT, result.host_profile)
        self.assertEqual(models.DATA_DEFAULT, result.type)
        self.assertIsInstance(result.ip, models.IPList)

    def test_dict_from_class(self):
        """Tests production of a dictionary from a Host object"""
        expected_result = {
            self.HOST_NAME: {
                'host_profile': self.HOST_DATA['host_profile'],
                'ip': 'success',
                'type': self.HOST_DATA['type']
            }
        }
        host = models.Host(self.HOST_NAME, **self.HOST_DATA)
        result = host.dict_from_class()
        self.assertDictEqual(expected_result, result)

    def test_merge_additional_data(self):
        """Tests merging of an additional data dictionary into a Host object"""
        config_dict = copy(self.HOST_DATA)
        config_dict['ip'] = 'success'
        result = models.Host(self.HOST_NAME)
        self.assertEqual(self.HOST_NAME, result.name)
        self.assertEqual(models.DATA_DEFAULT, result.rack_name)
        self.assertEqual(models.DATA_DEFAULT, result.host_profile)
        self.assertEqual(models.DATA_DEFAULT, result.type)
        self.assertIsInstance(result.ip, models.IPList)
        result.merge_additional_data(config_dict)
        self.assertEqual(self.HOST_NAME, result.name)
        self.assertEqual(config_dict['rack_name'], result.rack_name)
        self.assertEqual(config_dict['host_profile'], result.host_profile)
        self.assertEqual(config_dict['type'], result.type)
        self.assertEqual(config_dict['ip'], 'success')


class TestRack(unittest.TestCase):
    """Tests for the Rack model"""

    RACK_NAME = 'test_rack1'
    HOST_DATA = {'rack_name': RACK_NAME, 'host_profile': 'host'}

    @mock.patch('spyglass.data_extractor.models.IPList', autospec=True)
    def setUp(self, MockIPList):
        """Sets up a mocked IPList and a list of Host objects for testing"""
        self.MockIPList = MockIPList
        self.HOST_DATA['ip'] = MockIPList()
        self.HOST_DATA['ip'].dict_from_class.return_value = 'success'
        self.hosts = [
            models.Host('test_host1', **self.HOST_DATA, type='genesis'),
            models.Host('test_host2', **self.HOST_DATA, type='compute'),
            models.Host('test_host3', **self.HOST_DATA, type='controller'),
        ]

    def test___init__(self):
        """Tests basic initialization of Rack"""
        result = models.Rack(self.RACK_NAME, self.hosts)
        self.assertEqual(self.RACK_NAME, result.name)
        self.assertEqual(self.hosts, result.hosts)

    def test_dict_from_class(self):
        """Tests production of a dictionary from a Rack object"""
        expected_result = {self.RACK_NAME: {}}
        expected_result[self.RACK_NAME].update(self.hosts[0].dict_from_class())
        expected_result[self.RACK_NAME].update(self.hosts[1].dict_from_class())
        expected_result[self.RACK_NAME].update(self.hosts[2].dict_from_class())
        result = models.Rack(self.RACK_NAME, self.hosts)
        self.assertDictEqual(expected_result, result.dict_from_class())

    def test_merge_additional_data_new_host(self):
        """Tests merging of data containing a new host

        If the additional data dictionary contains a host not already contained
        in Rack.hosts, Rack should add the host to the list.
        """
        config_dict = {'test_host4': {**self.HOST_DATA}}
        result = models.Rack(self.RACK_NAME, self.hosts)
        self.assertIsNone(result.get_host_by_name('test_host4'))
        result.merge_additional_data(config_dict)
        self.assertIsNotNone(result.get_host_by_name('test_host4'))

    def test_merge_additional_data_existing_host(self):
        """Tests merging of data containing data for an existing host

        If the additional data dictionary contains a host already contained in
        Rack.hosts, Rack should call merge_additional_data on the existing host
        with the new data.
        """
        config_dict = {'test_host1': {'host_profile': 'new_profile'}}
        result = models.Rack(self.RACK_NAME, self.hosts)
        self.assertEqual(
            self.HOST_DATA['host_profile'],
            result.get_host_by_name('test_host1').host_profile)
        result.merge_additional_data(config_dict)
        self.assertEqual(
            config_dict['test_host1']['host_profile'],
            result.get_host_by_name('test_host1').host_profile)

    def test_get_host_by_name(self):
        """Tests retrieval of a Rack's host by name"""
        result = models.Rack(self.RACK_NAME, self.hosts)
        self.assertEqual(
            self.hosts[1], result.get_host_by_name(self.hosts[1].name))

    def test_get_host_by_type(self):
        """Tests retrieval of a Rack's host(s) by type"""
        result = models.Rack(self.RACK_NAME, self.hosts)
        self.assertEqual(self.hosts[0], result.get_host_by_type('genesis')[0])
        self.assertEqual(self.hosts[1], result.get_host_by_type('compute')[0])
        self.assertEqual(
            self.hosts[2],
            result.get_host_by_type('controller')[0])


class TestVLANNetworkData(unittest.TestCase):
    """Tests for the VLANNetworkData model"""

    VLAN_NAME = 'test'
    VLAN_DATA = {
        'role': 'oam',
        'vlan': '23',
        'subnet': ['210.27.143.213', '127.13.31.192'],
        'routes': ['29.190.93.106', '252.240.25.174'],
        'gateway': '204.70.95.80',
        'dhcp_start': '88.9.225.29',
        'dhcp_end': '71.31.147.105',
        'static_start': '117.137.102.246',
        'static_end': '176.20.227.186',
        'reserved_start': '229.171.15.171',
        'reserved_end': '230.187.248.100'
    }

    def test___init__(self):
        """Tests basic initialization of VLANNetworkData"""
        result = models.VLANNetworkData(self.VLAN_NAME, **self.VLAN_DATA)
        self.assertEqual(self.VLAN_NAME, result.name)
        self.assertEqual(self.VLAN_DATA['role'], result.role)
        self.assertEqual(self.VLAN_DATA['vlan'], result.vlan)
        self.assertEqual(self.VLAN_DATA['subnet'], result.subnet)
        self.assertEqual(self.VLAN_DATA['routes'], result.routes)
        self.assertEqual(self.VLAN_DATA['gateway'], result.gateway)
        self.assertEqual(self.VLAN_DATA['dhcp_start'], result.dhcp_start)
        self.assertEqual(self.VLAN_DATA['dhcp_end'], result.dhcp_end)
        self.assertEqual(self.VLAN_DATA['static_start'], result.static_start)
        self.assertEqual(self.VLAN_DATA['static_end'], result.static_end)
        self.assertEqual(
            self.VLAN_DATA['reserved_start'], result.reserved_start)
        self.assertEqual(self.VLAN_DATA['reserved_end'], result.reserved_end)

    def test___init___missing_data(self):
        """Tests initialization of VLANNetworkData with missing data

        Any data not explicitly given to VLANNetworkData should be set to None
        or an empty list. Since VLANNetworkData can contain a variety of
        different settings, many of which are not required, most of these
        settings default to None so they will not be outputted when exporting
        to a dictionary.
        """
        result = models.VLANNetworkData(self.VLAN_NAME)
        self.assertEqual(self.VLAN_NAME, result.name)
        self.assertEqual(self.VLAN_NAME, result.role)
        self.assertIsNone(result.vlan)
        self.assertEqual([], result.subnet)
        self.assertEqual([], result.routes)
        self.assertIsNone(result.dhcp_start)
        self.assertIsNone(result.dhcp_end)
        self.assertIsNone(result.static_start)
        self.assertIsNone(result.static_end)
        self.assertIsNone(result.reserved_start)
        self.assertIsNone(result.reserved_end)

    def test_dict_from_class(self):
        """Tests production of a dictionary from a VLANNetworkData object"""
        copy_vlan_data = copy(self.VLAN_DATA)
        copy_vlan_data.pop('role')
        expected_result = {self.VLAN_DATA['role']: {**copy_vlan_data}}
        result = models.VLANNetworkData(self.VLAN_NAME, **self.VLAN_DATA)
        self.assertDictEqual(expected_result, result.dict_from_class())

    def test_merge_additional_data(self):
        """Tests merging of additional data into a VLANNetworkData object"""
        result = models.VLANNetworkData(self.VLAN_NAME)
        self.assertEqual(self.VLAN_NAME, result.name)
        self.assertEqual(self.VLAN_NAME, result.role)
        self.assertIsNone(result.vlan)
        self.assertEqual([], result.subnet)
        self.assertEqual([], result.routes)
        self.assertIsNone(result.dhcp_start)
        self.assertIsNone(result.dhcp_end)
        self.assertIsNone(result.static_start)
        self.assertIsNone(result.static_end)
        self.assertIsNone(result.reserved_start)
        self.assertIsNone(result.reserved_end)
        result.merge_additional_data(self.VLAN_DATA)
        self.assertEqual(self.VLAN_NAME, result.name)
        self.assertEqual(self.VLAN_DATA['role'], result.role)
        self.assertEqual(self.VLAN_DATA['vlan'], result.vlan)
        self.assertEqual(self.VLAN_DATA['subnet'], result.subnet)
        self.assertEqual(self.VLAN_DATA['routes'], result.routes)
        self.assertEqual(self.VLAN_DATA['gateway'], result.gateway)
        self.assertEqual(self.VLAN_DATA['dhcp_start'], result.dhcp_start)
        self.assertEqual(self.VLAN_DATA['dhcp_end'], result.dhcp_end)
        self.assertEqual(self.VLAN_DATA['static_start'], result.static_start)
        self.assertEqual(self.VLAN_DATA['static_end'], result.static_end)
        self.assertEqual(
            self.VLAN_DATA['reserved_start'], result.reserved_start)
        self.assertEqual(self.VLAN_DATA['reserved_end'], result.reserved_end)


class TestNetwork(unittest.TestCase):
    """Tests for the Network model"""

    VLAN_DATA = {
        'vlan': '23',
        'subnet': ['210.27.143.213', '127.13.31.192'],
        'routes': ['29.190.93.106', '252.240.25.174'],
        'gateway': '204.70.95.80',
        'dhcp_start': '88.9.225.29',
        'dhcp_end': '71.31.147.105',
        'static_start': '117.137.102.246',
        'static_end': '176.20.227.186',
        'reserved_start': '229.171.15.171',
        'reserved_end': '230.187.248.100'
    }
    BGP_DATA = {
        'asnumber': 64671,
        'ingress_vip': '10.0.220.73',
        'peer_asnumber': 64688
    }

    def setUp(self):
        """Sets up a list of VLANNetworkData used to test Network objects"""
        self.vlan_network_data = [
            models.VLANNetworkData('oam', **self.VLAN_DATA),
            models.VLANNetworkData('oob', **self.VLAN_DATA),
            models.VLANNetworkData('pxe', **self.VLAN_DATA)
        ]

    def test___init__(self):
        """Tests basic initialization of a Network object"""
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertEqual(
            set(self.vlan_network_data), set(result.vlan_network_data))
        self.assertDictEqual(self.BGP_DATA, result.bgp)

    def test_dict_from_class(self):
        """Tests production of a dictionary from a Network object"""
        oob = copy(self.VLAN_DATA)
        oob.pop('vlan')
        expected_result = {
            'bgp': self.BGP_DATA,
            'vlan_network_data': {
                'oam': {
                    **self.VLAN_DATA
                },
                'oob': {
                    **oob
                },
                'pxe': {
                    **self.VLAN_DATA
                },
            }
        }
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertDictEqual(expected_result, result.dict_from_class())

    def test_merge_additional_data_bgp(self):
        """Tests merging additional BGP data

        BGP data is often set after the initial generation of data objects.
        """
        result = models.Network(self.vlan_network_data)
        self.assertEqual({}, result.bgp)
        result.merge_additional_data({'bgp': self.BGP_DATA})
        self.assertEqual(self.BGP_DATA, result.bgp)

    def test_merge_additional_data_new_vlan_data(self):
        """Tests merging of data containing data for a new VLANNetworkData obj

        If a new set of VLANNetworkData is introduced in additional data,
        Network should create a new VLANNetworkData object for its list.
        """
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertIsNone(result.get_vlan_data_by_name('calico'))
        new_calico_vlan = {'vlan_network_data': {'calico': {**self.VLAN_DATA}}}
        result.merge_additional_data(new_calico_vlan)
        self.assertIsNotNone(result.get_vlan_data_by_name('calico'))

    def test_merge_additional_data_new_data_for_existing_vlan(self):
        """Tests merging of data for an existing VLANNetworkData object

        If a new set of data for an existing VLANNetworkData role is given by
        additional data, Network should merge this new data into the existing
        VLANNetworkData object.
        """
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertEqual(
            self.VLAN_DATA['vlan'],
            result.get_vlan_data_by_name('oam').vlan)
        new_vlan_data = {'vlan_network_data': {'oam': {'vlan': '12'}}}
        result.merge_additional_data(new_vlan_data)
        self.assertEqual(
            new_vlan_data['vlan_network_data']['oam']['vlan'],
            result.get_vlan_data_by_name('oam').vlan)

    def test_get_vlan_data_by_name(self):
        """Tests retrieval of VLANNetworkData by name attribute"""
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertEqual(
            self.vlan_network_data[1], result.get_vlan_data_by_name('oob'))

    def test_get_vlan_data_by_name_dne(self):
        """Tests retrieval of nonexistent name VLANNetworkData"""
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertIsNone(result.get_vlan_data_by_name('calico'))

    def test_get_vlan_data_by_role(self):
        """Tests retrieval of VLANNetworkData by role attribute"""
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertEqual(
            self.vlan_network_data[1], result.get_vlan_data_by_role('oob'))

    def test_get_vlan_data_by_role_dne(self):
        """Tests retrieval of nonexistent role VLANNetworkData"""
        result = models.Network(self.vlan_network_data, bgp=self.BGP_DATA)
        self.assertIsNone(result.get_vlan_data_by_role('calico'))


class TestSiteInfo(unittest.TestCase):
    """Tests for the SiteInfo model"""

    SITE_NAME = 'Test Site'
    SITE_INFO = {
        'physical_location_id': 12345,
        'state': 'MO',
        'country': 'USA',
        'corridor': 'C1',
        'sitetype': 'test',
        'dns': ['210.27.143.213', '127.13.31.192'],
        'ntp': ['29.190.93.106', '252.240.25.174'],
        'domain': 'example.com',
        'ldap': {
            'common_name': 'test',
            'domain': 'example',
            'subdomain': 'test',
            'url': 'ldap://ldap.example.com'
        }
    }

    def test___init__(self):
        """Tests basic initialization of SiteInfo"""
        result = models.SiteInfo(self.SITE_NAME, **self.SITE_INFO)
        self.assertEqual(self.SITE_NAME, result.name)
        self.assertEqual(
            self.SITE_INFO['physical_location_id'],
            result.physical_location_id)
        self.assertEqual(self.SITE_INFO['state'], result.state)
        self.assertEqual(self.SITE_INFO['country'], result.country)
        self.assertEqual(self.SITE_INFO['corridor'], result.corridor)
        self.assertEqual(self.SITE_INFO['sitetype'], result.sitetype)
        self.assertEqual(','.join(self.SITE_INFO['dns']), str(result.dns))
        self.assertEqual(','.join(self.SITE_INFO['ntp']), str(result.ntp))
        self.assertEqual(self.SITE_INFO['domain'], result.domain)
        self.assertDictEqual(self.SITE_INFO['ldap'], result.ldap)

    def test___init___missing_data(self):
        """Tests initailization of SiteInfo with missing data

        If data is not given for SiteInfo attributes, the attributes should
        be set to the value given by models.DATA_DEFAULT, an empty list, or
        an empty dictionary.
        """
        result = models.SiteInfo(self.SITE_NAME)
        self.assertEqual(self.SITE_NAME, result.name)
        self.assertEqual(models.DATA_DEFAULT, result.physical_location_id)
        self.assertEqual(models.DATA_DEFAULT, result.state)
        self.assertEqual(models.DATA_DEFAULT, result.country)
        self.assertEqual(models.DATA_DEFAULT, result.corridor)
        self.assertEqual(models.DATA_DEFAULT, result.sitetype)
        self.assertEqual(','.join([]), str(result.dns))
        self.assertEqual(','.join([]), str(result.ntp))
        self.assertEqual(models.DATA_DEFAULT, result.domain)
        self.assertDictEqual({}, result.ldap)

    def test_dict_from_class(self):
        """Tests production of a dictionary from a SiteInfo object"""
        expected_results = copy(self.SITE_INFO)
        expected_results['dns'] = \
            {'servers': ','.join(expected_results['dns'])}
        expected_results['ntp'] = \
            {'servers': ','.join(expected_results['ntp'])}
        expected_results['name'] = self.SITE_NAME
        result = models.SiteInfo(self.SITE_NAME, **self.SITE_INFO)
        self.assertDictEqual(expected_results, result.dict_from_class())

    def test_merge_additional_data(self):
        """Tests merging of additional data into SiteInfo"""
        result = models.SiteInfo(self.SITE_NAME)
        self.assertEqual(self.SITE_NAME, result.name)
        self.assertEqual(models.DATA_DEFAULT, result.physical_location_id)
        self.assertEqual(models.DATA_DEFAULT, result.state)
        self.assertEqual(models.DATA_DEFAULT, result.country)
        self.assertEqual(models.DATA_DEFAULT, result.corridor)
        self.assertEqual(models.DATA_DEFAULT, result.sitetype)
        self.assertEqual(','.join([]), str(result.dns))
        self.assertEqual(','.join([]), str(result.ntp))
        self.assertEqual(models.DATA_DEFAULT, result.domain)
        self.assertDictEqual({}, result.ldap)
        config_dict = copy(self.SITE_INFO)
        config_dict['dns'] = {'servers': config_dict['dns']}
        config_dict['ntp'] = {'servers': config_dict['ntp']}
        config_dict['name'] = 'new_name'
        result.merge_additional_data(config_dict)
        self.assertEqual(config_dict['name'], result.name)
        self.assertEqual(
            self.SITE_INFO['physical_location_id'],
            result.physical_location_id)
        self.assertEqual(self.SITE_INFO['state'], result.state)
        self.assertEqual(self.SITE_INFO['country'], result.country)
        self.assertEqual(self.SITE_INFO['corridor'], result.corridor)
        self.assertEqual(self.SITE_INFO['sitetype'], result.sitetype)
        self.assertEqual(','.join(self.SITE_INFO['dns']), str(result.dns))
        self.assertEqual(','.join(self.SITE_INFO['ntp']), str(result.ntp))
        self.assertEqual(self.SITE_INFO['domain'], result.domain)
        self.assertDictEqual(self.SITE_INFO['ldap'], result.ldap)


class TestSiteDocumentData(unittest.TestCase):
    """Tests for the SiteDocumentData model"""

    STORAGE_DICT = {'ceph': {'controller': {'osd_count': 6}}}

    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.Network')
    @mock.patch('spyglass.data_extractor.models.Rack')
    def test___init__(self, Rack, Network, SiteInfo):
        """Tests basic initialization of SiteDocumentData"""
        site_info = SiteInfo()
        network = Network()
        baremetal = [Rack(), Rack(), Rack()]
        result = models.SiteDocumentData(
            site_info, network, baremetal, self.STORAGE_DICT)
        self.assertEqual(site_info, result.site_info)
        self.assertEqual(network, result.network)
        self.assertEqual(set(baremetal), set(result.baremetal))
        self.assertDictEqual(self.STORAGE_DICT, result.storage)

    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.Network')
    @mock.patch('spyglass.data_extractor.models.Rack')
    def test_dict_from_class(self, Rack, Network, SiteInfo):
        """Tests production of a dictionary from a SiteDocumentData object"""
        mock_site_info_data = {'name': 'test', 'country': 'USA'}
        mock_network_data = {
            'bgp': 'bgp_data',
            'vlan_network_data': 'vlan_data'
        }
        mock_baremetal0_data = {'rack1': {'host1': 'data'}}
        mock_baremetal1_data = {'rack2': {'host2': 'data'}}

        site_info = SiteInfo()
        site_info.dict_from_class.return_value = mock_site_info_data
        type(SiteInfo()).region_name = mock.PropertyMock(
            return_value='region_name')
        network = Network()
        network.dict_from_class.return_value = mock_network_data
        baremetal = [Rack(), Rack()]
        Rack().dict_from_class.side_effect = \
            [mock_baremetal0_data, mock_baremetal1_data]

        expected_result = {
            'baremetal': {
                **mock_baremetal0_data,
                **mock_baremetal1_data
            },
            'network': mock_network_data,
            'region_name': 'region_name',
            'site_info': mock_site_info_data,
            'storage': self.STORAGE_DICT
        }

        result = models.SiteDocumentData(
            site_info, network, baremetal, self.STORAGE_DICT)
        self.assertDictEqual(expected_result, result.dict_from_class())

    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.Network')
    @mock.patch('spyglass.data_extractor.models.Rack')
    def test_merge_additional_data_storage(self, Rack, Network, SiteInfo):
        """Tests merging of storage data dictionary

        Storage data is often given after initialization of data objects.
        """
        site_info = SiteInfo()
        network = Network()
        baremetal = [Rack(), Rack(), Rack()]
        result = models.SiteDocumentData(site_info, network, baremetal)
        self.assertIsNone(result.storage)
        result.merge_additional_data({'storage': self.STORAGE_DICT})
        self.assertDictEqual(self.STORAGE_DICT, result.storage)

    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.Network')
    @mock.patch('spyglass.data_extractor.models.Rack')
    def test_get_baremetal_rack_by_name(self, Rack, Network, SiteInfo):
        """Tests retrieval of baremetal rack by name"""
        site_info = SiteInfo()
        network = Network()
        baremetal = [Rack(), Rack(), Rack()]
        type(Rack()).name = mock.PropertyMock(
            side_effect=['rack1', 'rack2', 'rack3'])
        result = models.SiteDocumentData(site_info, network, baremetal)
        self.assertIsNotNone(result.get_baremetal_rack_by_name('rack2'))

    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.Network')
    @mock.patch('spyglass.data_extractor.models.Rack')
    def test_get_baremetal_rack_by_name_dne(self, Rack, Network, SiteInfo):
        """Tests retrieval of nonexistent baremetal rack by name"""
        site_info = SiteInfo()
        network = Network()
        baremetal = [Rack(), Rack()]
        type(Rack()).name = mock.PropertyMock(side_effect=['rack1', 'rack3'])
        result = models.SiteDocumentData(site_info, network, baremetal)
        self.assertIsNone(result.get_baremetal_rack_by_name('rack2'))

    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.Network')
    @mock.patch('spyglass.data_extractor.models.Rack')
    @mock.patch('spyglass.data_extractor.models.Host')
    def test_get_baremetal_rack_by_name_multiple(
            self, Host, Rack, Network, SiteInfo):
        """Tests retrieval of baremetal host(s) by type"""
        site_info = SiteInfo()
        network = Network()
        baremetal = [Rack(), Rack()]
        Rack().get_host_by_type.return_value = [Host()]
        result = models.SiteDocumentData(site_info, network, baremetal)
        self.assertEqual(2, len(result.get_baremetal_host_by_type('genesis')))
        self.assertEqual(2, len(result.get_baremetal_host_by_type('computer')))
        self.assertEqual(
            2, len(result.get_baremetal_host_by_type('controller')))


class TestValidateKeyInIntermediaryDict(unittest.TestCase):
    """Tests the _validate_key_in_intermediary_dict function"""
    def test__validate_key_in_intermediary_dict(self):
        test_dictionary = {'test_key': 'value'}
        key = 'test_key'
        self.assertIsNone(
            models._validate_key_in_intermediary_dict(key, test_dictionary))

    def test__validate_key_in_intermediary_dict_key_dne(self):
        test_dictionary = {'test_key': 'value'}
        key = 'not_test_key'
        with self.assertRaises(InvalidIntermediary):
            models._validate_key_in_intermediary_dict(key, test_dictionary)


class TestSiteDocumentDataFactory(unittest.TestCase):
    """Tests the site_document_data_factory function"""
    def setUp(self) -> None:
        test_intermediary_path = os.path.join(
            FIXTURE_DIR, 'test_intermediary.yaml')
        with open(test_intermediary_path, 'r') as f:
            self.intermediary_dict = yaml.safe_load(f)

    def test_site_document_data_factory(self):
        site_document_data = models.site_document_data_factory(
            self.intermediary_dict)

        # Check correct return type
        self.assertIsInstance(site_document_data, models.SiteDocumentData)

    def test_site_document_data_factory_saves_storage(self):
        site_document_data = models.site_document_data_factory(
            self.intermediary_dict)

        # Check that storage was saved without changes in the SiteDocumentData
        self.assertDictEqual(
            self.intermediary_dict['storage'], site_document_data.storage)

    def test_site_document_data_factory_saves_site_info(self):
        site_document_data = models.site_document_data_factory(
            self.intermediary_dict)

        # Check that site info saved correctly in SiteInfo object
        site_info_dict = self.intermediary_dict['site_info']
        self.assertIsInstance(site_document_data.site_info, models.SiteInfo)
        self.assertEqual(
            site_info_dict['name'], site_document_data.site_info.name)
        self.assertEqual(
            self.intermediary_dict['region_name'],
            site_document_data.site_info.region_name)
        self.assertEqual(
            site_info_dict['state'], site_document_data.site_info.state)
        self.assertEqual(
            site_info_dict['physical_location_id'],
            site_document_data.site_info.physical_location_id)
        self.assertEqual(
            site_info_dict['country'], site_document_data.site_info.country)
        self.assertEqual(
            site_info_dict['corridor'], site_document_data.site_info.corridor)
        self.assertEqual(
            site_info_dict['sitetype'], site_document_data.site_info.sitetype)
        self.assertEqual(
            site_info_dict['domain'], site_document_data.site_info.domain)
        self.assertDictEqual(
            site_info_dict['ldap'], site_document_data.site_info.ldap)
        self.assertEqual(
            site_info_dict['dns']['servers'],
            str(site_document_data.site_info.dns))
        self.assertEqual(
            site_info_dict['ntp']['servers'],
            str(site_document_data.site_info.ntp))

    def test_site_document_data_factory_saves_network_data(self):
        site_document_data = models.site_document_data_factory(
            self.intermediary_dict)

        # Check that network data saved correctly into a Network object
        network_dict = self.intermediary_dict['network']
        self.assertIsInstance(site_document_data.network, models.Network)
        self.assertDictEqual(
            network_dict['bgp'], site_document_data.network.bgp)
        for network_type, network_data \
                in network_dict['vlan_network_data'].items():
            vlan_network_data = \
                site_document_data.network.get_vlan_data_by_name(network_type)
            self.assertIsInstance(vlan_network_data, models.VLANNetworkData)
            self.assertEqual(network_type, vlan_network_data.name)
            self.assertEqual(network_type, vlan_network_data.role)
            self.assertEqual(network_data['subnet'], vlan_network_data.subnet)
            if 'routes' in network_data:
                self.assertEqual(
                    network_data['routes'], vlan_network_data.routes)
            if 'gateway' in network_data:
                self.assertEqual(
                    network_data['gateway'], vlan_network_data.gateway)
            if 'vlan' in network_data:
                self.assertEqual(network_data['vlan'], vlan_network_data.vlan)
            if 'dhcp_start' in network_data and 'dhcp_end' in network_data:
                self.assertEqual(
                    network_data['dhcp_start'], vlan_network_data.dhcp_start)
                self.assertEqual(
                    network_data['dhcp_end'], vlan_network_data.dhcp_end)
            if 'static_start' in network_data and 'static_end' in network_data:
                self.assertEqual(
                    network_data['static_start'],
                    vlan_network_data.static_start)
                self.assertEqual(
                    network_data['static_end'], vlan_network_data.static_end)
            if 'reserved_start' in network_data \
                    and 'reserved_end' in network_data:
                self.assertEqual(
                    network_data['reserved_start'],
                    vlan_network_data.reserved_start)
                self.assertEqual(
                    network_data['reserved_end'],
                    vlan_network_data.reserved_end)

    def test_site_document_data_factory_saves_baremetal_data(self):
        site_document_data = models.site_document_data_factory(
            self.intermediary_dict)

        # Check that baremetal racks saved correctly into Rack objects
        for rack_name, hosts \
                in self.intermediary_dict['baremetal'].items():
            rack = site_document_data.get_baremetal_rack_by_name(rack_name)
            for host_name, host_data in hosts.items():
                host = rack.get_host_by_name(host_name)
                self.assertEqual(host_name, host.name)
                self.assertEqual(rack_name, host.rack_name)
                self.assertEqual(host_data['type'], host.type)
                self.assertEqual(host_data['host_profile'], host.host_profile)
                self.assertEqual(host_data['ip']['oob'], host.ip.oob)
                self.assertEqual(host_data['ip']['oam'], host.ip.oam)
                self.assertEqual(host_data['ip']['calico'], host.ip.calico)
                self.assertEqual(host_data['ip']['overlay'], host.ip.overlay)
                self.assertEqual(host_data['ip']['pxe'], host.ip.pxe)
                self.assertEqual(host_data['ip']['storage'], host.ip.storage)
            self.assertEqual(rack_name, rack.name)
