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

import abc
import pprint
import six
import logging

from spyglass.utils import utils

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseDataSourcePlugin(object):
    """Provide basic hooks for data source plugins"""

    def __init__(self, region):
        self.source_type = None
        self.source_name = None
        self.region = region
        self.site_data = {}

    @abc.abstractmethod
    def set_config_opts(self, conf):
        """Placeholder to set confgiuration options
        specific to each plugin.

        :param dict conf: Configuration options as dict

        Example: conf = { 'excel_spec': 'spec1.yaml',
                          'excel_path': 'excel.xls' }

        Each plugin will have their own config opts.
        """
        return

    @abc.abstractmethod
    def get_plugin_conf(self, kwargs):
        """ Validate and returns the plugin config parameters.
        If validation fails, Spyglass exits.

        :param char pointer: Spyglass CLI parameters.

        :returns plugin conf if successfully validated.

        Each plugin implements their own validaton mechanism.
        """
        return {}

    @abc.abstractmethod
    def get_racks(self, region):
        """Return list of racks in the region

        :param string region: Region name

        :returns: list of rack names

        :rtype: list

        Example: ['rack01', 'rack02']
        """
        return []

    @abc.abstractmethod
    def get_hosts(self, region, rack):
        """Return list of hosts in the region

        :param string region: Region name
        :param string rack: Rack name

        :returns: list of hosts information

        :rtype: list of dict

        Example: [
                     {
                         'name': 'host01',
                         'type': 'controller',
                         'host_profile': 'hp_01'
                     },
                     {
                         'name': 'host02',
                         'type': 'compute',
                         'host_profile': 'hp_02'}
                 ]
        """
        return []

    @abc.abstractmethod
    def get_networks(self, region):
        """Return list of networks in the region

        :param string region: Region name

        :returns: list of networks and their vlans

        :rtype: list of dict

        Example: [
                     {
                         'name': 'oob',
                         'vlan': '41',
                         'subnet': '192.168.1.0/24',
                         'gateway': '192.168.1.1'
                     },
                     {
                         'name': 'pxe',
                         'vlan': '42',
                         'subnet': '192.168.2.0/24',
                         'gateway': '192.168.2.1'
                     },
                     {
                         'name': 'oam',
                         'vlan': '43',
                         'subnet': '192.168.3.0/24',
                         'gateway': '192.168.3.1'
                     },
                     {
                         'name': 'ksn',
                         'vlan': '44',
                         'subnet': '192.168.4.0/24',
                         'gateway': '192.168.4.1'
                     },
                     {
                         'name': 'storage',
                         'vlan': '45',
                         'subnet': '192.168.5.0/24',
                         'gateway': '192.168.5.1'
                     },
                     {
                         'name': 'overlay',
                         'vlan': '45',
                         'subnet': '192.168.6.0/24',
                         'gateway': '192.168.6.1'
                     }
                 ]
        """

        # TODO(nh863p): Expand the return type if they are rack level subnets
        # TODO(nh863p): Is ingress information can be provided here?
        return []

    @abc.abstractmethod
    def get_ips(self, region, host):
        """Return list of IPs on the host

        :param string region: Region name
        :param string host: Host name

        :returns: Dict of IPs per network on the host

        :rtype: dict

        Example: {'oob': {'ipv4': '192.168.1.10'},
                  'pxe': {'ipv4': '192.168.2.10'}}

        The network name from get_networks is expected to be the keys of this
        dict. In case some networks are missed, they are expected to be either
        DHCP or internally generated n the next steps by the design rules.
        """
        return {}

    @abc.abstractmethod
    def get_dns_servers(self, region):
        """Return the DNS servers

        :param string region: Region name

        :returns: List of DNS servers to be configured on host

        :rtype: List

        Example: ['8.8.8.8', '8.8.8.4']
        """
        return []

    @abc.abstractmethod
    def get_ntp_servers(self, region):
        """Return the NTP servers

        :param string region: Region name

        :returns: List of NTP servers to be configured on host

        :rtype: List

        Example: ['ntp1.ubuntu1.example', 'ntp2.ubuntu.example']
        """
        return []

    @abc.abstractmethod
    def get_ldap_information(self, region):
        """Return the LDAP server information

        :param string region: Region name

        :returns: LDAP server information

        :rtype: Dict

        Example: {'url': 'ldap.example.com',
                  'common_name': 'ldap-site1',
                  'domain': 'test',
                  'subdomain': 'test_sub1'}
        """
        return {}

    @abc.abstractmethod
    def get_location_information(self, region):
        """Return location information

        :param string region: Region name

        :returns: Dict of location information

        :rtype: dict

        Example: {'name': 'Dallas',
                  'physical_location': 'DAL01',
                  'state': 'Texas',
                  'country': 'US',
                  'corridor': 'CR1'}
        """
        return {}

    @abc.abstractmethod
    def get_domain_name(self, region):
        """Return the Domain name

        :param string region: Region name

        :returns: Domain name

        :rtype: string

        Example: example.com
        """
        return ""

    def extract_baremetal_information(self):
        """Get baremetal information from plugin

        :returns: dict of baremetal nodes

        :rtype: dict

        Return dict should be in the format
        {
          'EXAMR06': {                 # rack name
            'examr06c036': {           # host name
              'host_profile': None,
              'ip': {
                'overlay': {},
                'oob': {},
                'calico': {},
                'oam': {},
                'storage': {},
                'pxe': {}
              },
              'rack': 'EXAMR06',
              'type': 'compute'
            }
          }
        }
        """
        LOG.info("Extract baremetal information from plugin")
        baremetal = {}
        hosts = self.get_hosts(self.region)

        # For each host list fill host profile and network IPs
        for host in hosts:
            host_name = host['name']
            rack_name = host['rack_name']

            if rack_name not in baremetal:
                baremetal[rack_name] = {}

            # Prepare temp dict for each host and append it to baremetal
            # at a rack level
            temp_host = {}
            if host['host_profile'] is None:
                temp_host['host_profile'] = "#CHANGE_ME"
            else:
                temp_host['host_profile'] = host['host_profile']

            # Get Host IPs from plugin
            temp_host_ips = self.get_ips(self.region, host_name)

            # Fill network IP for this host
            temp_host['ip'] = {}
            temp_host['ip']['oob'] = temp_host_ips[host_name].get(
                'oob', "#CHANGE_ME")
            temp_host['ip']['calico'] = temp_host_ips[host_name].get(
                'calico', "#CHANGE_ME")
            temp_host['ip']['oam'] = temp_host_ips[host_name].get(
                'oam', "#CHANGE_ME")
            temp_host['ip']['storage'] = temp_host_ips[host_name].get(
                'storage', "#CHANGE_ME")
            temp_host['ip']['overlay'] = temp_host_ips[host_name].get(
                'overlay', "#CHANGE_ME")
            temp_host['ip']['pxe'] = temp_host_ips[host_name].get(
                'pxe', "#CHANGE_ME")

            baremetal[rack_name][host_name] = temp_host
        LOG.debug("Baremetal information:\n{}".format(
            pprint.pformat(baremetal)))

        return baremetal

    def extract_site_information(self):
        """Get site information from plugin

        :returns: dict of site information

        :rtpe: dict

        Return dict should be in the format
        {
          'name': '',
          'country': '',
          'state': '',
          'corridor': '',
          'sitetype': '',
          'dns': [],
          'ntp': [],
          'ldap': {},
          'domain': None
        }
        """
        LOG.info("Extract site information from plugin")
        site_info = {}

        # Extract location information
        location_data = self.get_location_information(self.region)
        if location_data is not None:
            site_info = location_data

        dns_data = self.get_dns_servers(self.region)
        site_info['dns'] = dns_data

        ntp_data = self.get_ntp_servers(self.region)
        site_info['ntp'] = ntp_data

        ldap_data = self.get_ldap_information(self.region)
        site_info['ldap'] = ldap_data

        domain_data = self.get_domain_name(self.region)
        site_info['domain'] = domain_data

        LOG.debug("Extracted site information:\n{}".format(
            pprint.pformat(site_info)))

        return site_info

    def extract_network_information(self):
        """Get network information from plugin
        like Subnets, DNS, NTP, LDAP details.

        :returns: dict of baremetal nodes

        :rtype: dict

        Return dict should be in the format
        {
          'vlan_network_data': {
            'oam': {},
            'ingress': {},
            'oob': {}
            'calico': {},
            'storage': {},
            'pxe': {},
            'overlay': {}
          }
        }
        """
        LOG.info("Extract network information from plugin")
        network_data = {}
        networks = self.get_networks(self.region)

        # We are interested in only the below networks mentioned in
        # networks_to_scan, so look for these networks from the data
        # returned by plugin
        networks_to_scan = [
            'calico', 'overlay', 'pxe', 'storage', 'oam', 'oob', 'ingress'
        ]
        network_data['vlan_network_data'] = {}

        for net in networks:
            tmp_net = {}
            if net['name'] in networks_to_scan:
                tmp_net['subnet'] = net.get('subnet', '#CHANGE_ME')
                if ((net['name'] != 'ingress') and (net['name'] != 'oob')):
                    tmp_net['vlan'] = net.get('vlan', '#CHANGE_ME')

            network_data['vlan_network_data'][net['name']] = tmp_net

        LOG.debug("Extracted network data:\n{}".format(
            pprint.pformat(network_data)))
        return network_data

    def extract_data(self):
        """Extract data from plugin

        Gather data related to baremetal, networks, storage and other site
        related information from plugin
        """
        LOG.info("Extract data from plugin")
        site_data = {}
        site_data['baremetal'] = self.extract_baremetal_information()
        site_data['site_info'] = self.extract_site_information()
        site_data['network'] = self.extract_network_information()
        self.site_data = site_data
        return site_data

    def apply_additional_data(self, extra_data):
        """Apply any additional inputs from user

        In case plugin doesnot provide some data, user can specify
        the same as part of additional data in form of dict. The user
        provided dict will be merged recursively to site_data.
        If there is repetition of data then additional data supplied
        shall take precedence.
        """
        LOG.info("Update site data with additional input")
        tmp_site_data = utils.dict_merge(self.site_data, extra_data)
        self.site_data = tmp_site_data
        return self.site_data
