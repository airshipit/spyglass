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

import itertools
import logging
import pprint
import re
from spyglass.data_extractor.base import BaseDataSourcePlugin
from spyglass.data_extractor.plugins.tugboat.excel_parser import ExcelParser

LOG = logging.getLogger(__name__)


class TugboatPlugin(BaseDataSourcePlugin):
    def __init__(self, region):
        LOG.info("Tugboat Initializing")
        self.source_type = 'excel'
        self.source_name = 'tugboat'

        # Configuration parameters
        self.excel_path = None
        self.excel_spec = None

        # Site related data
        self.region = region

        # Raw data from excel
        self.parsed_xl_data = None

        LOG.info("Initiated data extractor plugin:{}".format(self.source_name))

    def set_config_opts(self, conf):
        """
        Placeholder to set configuration options
        specific to each plugin.

        :param dict conf: Configuration options as dict

        Example: conf = { 'excel_spec': 'spec1.yaml',
                          'excel_path': 'excel.xls' }

        Each plugin will have their own config opts.
        """
        self.excel_path = conf['excel_path']
        self.excel_spec = conf['excel_spec']

        # Extract raw data from excel sheets
        self._get_excel_obj()
        self._extract_raw_data_from_excel()
        return

    def get_plugin_conf(self, kwargs):
        """ Validates the plugin param from CLI and return if correct


        Ideally the CLICK module shall report an error if excel file
        and excel specs are not specified. The below code has been
        written as an additional safeguard.
        """
        try:
            assert (len(
                kwargs['excel'])), "Engineering Spec file not specified"
            excel_file_info = kwargs['excel']
            assert (kwargs['excel_spec']
                    ) is not None, "Excel Spec file not specified"
            excel_spec_info = kwargs['excel_spec']
        except AssertionError as e:
            LOG.error("{}:Spyglass exited!".format(e))
            exit()
        plugin_conf = {
            'excel_path': excel_file_info,
            'excel_spec': excel_spec_info
        }
        return plugin_conf

    def get_hosts(self, region, rack=None):
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
        LOG.info("Get Host Information")
        ipmi_data = self.parsed_xl_data['ipmi_data'][0]
        rackwise_hosts = self._get_rackwise_hosts()
        host_list = []
        for rack in rackwise_hosts.keys():
            for host in rackwise_hosts[rack]:
                host_list.append({
                    'rack_name':
                    rack,
                    'name':
                    host,
                    'host_profile':
                    ipmi_data[host]['host_profile']
                })
        return host_list

    def get_networks(self, region):
        """ Extracts vlan network info from raw network data from excel"""
        vlan_list = []
        # Network data extracted from xl is formatted to have a predictable
        # data type. For e.g VlAN 45 extracted from xl is formatted as 45
        vlan_pattern = r'\d+'
        private_net = self.parsed_xl_data['network_data']['private']
        public_net = self.parsed_xl_data['network_data']['public']
        # Extract network information from private and public network data
        for net_type, net_val in itertools.chain(private_net.items(),
                                                 public_net.items()):
            tmp_vlan = {}
            # Ingress is special network that has no vlan, only a subnet string
            # So treatment for ingress is different
            if net_type is not 'ingress':
                # standardize the network name as net_type may ne different.
                # For e.g insteas of pxe it may be PXE or instead of calico
                # it may be ksn. Valid network names are pxe, calico, oob, oam,
                # overlay, storage, ingress
                tmp_vlan['name'] = self._get_network_name_from_vlan_name(
                    net_type)

                # extract vlan tag. It was extracted from xl file as 'VlAN 45'
                # The code below extracts the numeric data fron net_val['vlan']
                if net_val.get('vlan', "") is not "":
                    value = re.findall(vlan_pattern, net_val['vlan'])
                    tmp_vlan['vlan'] = value[0]
                else:
                    tmp_vlan['vlan'] = "#CHANGE_ME"

                tmp_vlan['subnet'] = net_val.get('subnet', "#CHANGE_ME")
                tmp_vlan['gateway'] = net_val.get('gateway', "#CHANGE_ME")
            else:
                tmp_vlan['name'] = 'ingress'
                tmp_vlan['subnet'] = net_val
            vlan_list.append(tmp_vlan)
        LOG.debug("vlan list extracted from tugboat:\n{}".format(
            pprint.pformat(vlan_list)))
        return vlan_list

    def get_ips(self, region, host=None):
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

        ip_ = {}
        ipmi_data = self.parsed_xl_data['ipmi_data'][0]
        ip_[host] = {
            'oob': ipmi_data[host].get('ipmi_address', '#CHANGE_ME'),
            'oam': ipmi_data[host].get('oam', '#CHANGE_ME'),
            'calico': ipmi_data[host].get('calico', '#CHANGE_ME'),
            'overlay': ipmi_data[host].get('overlay', '#CHANGE_ME'),
            'pxe': ipmi_data[host].get('pxe', '#CHANGE_ME'),
            'storage': ipmi_data[host].get('storage', '#CHANGE_ME')
        }
        return ip_

    def get_ldap_information(self, region):
        """ Extract ldap information from excel"""

        ldap_raw_data = self.parsed_xl_data['site_info']['ldap']
        ldap_info = {}
        # raw url is 'url: ldap://example.com' so we are converting to
        # 'ldap://example.com'
        url = ldap_raw_data.get('url', '#CHANGE_ME')
        try:
            ldap_info['url'] = url.split(' ')[1]
            ldap_info['domain'] = url.split('.')[1]
        except IndexError as e:
            LOG.error("url.split:{}".format(e))
        ldap_info['common_name'] = ldap_raw_data.get('common_name',
                                                     '#CHANGE_ME')
        ldap_info['subdomain'] = ldap_raw_data.get('subdomain', '#CHANGE_ME')

        return ldap_info

    def get_ntp_servers(self, region):
        """ Returns a comma separated list of ntp ip addresses"""

        ntp_server_list = self._get_formatted_server_list(
            self.parsed_xl_data['site_info']['ntp'])
        return ntp_server_list

    def get_dns_servers(self, region):
        """ Returns a comma separated list of dns ip addresses"""
        dns_server_list = self._get_formatted_server_list(
            self.parsed_xl_data['site_info']['dns'])
        return dns_server_list

    def get_domain_name(self, region):
        """ Returns domain name extracted from excel file"""

        return self.parsed_xl_data['site_info']['domain']

    def get_location_information(self, region):
        """
        Prepare location data from information extracted
        by ExcelParser(i.e raw data)
        """
        location_data = self.parsed_xl_data['site_info']['location']

        corridor_pattern = r'\d+'
        corridor_number = re.findall(corridor_pattern,
                                     location_data['corridor'])[0]
        name = location_data.get('name', '#CHANGE_ME')
        state = location_data.get('state', '#CHANGE_ME')
        country = location_data.get('country', '#CHANGE_ME')
        physical_location_id = location_data.get('physical_location', '')

        return {
            'name': name,
            'physical_location_id': physical_location_id,
            'state': state,
            'country': country,
            'corridor': 'c{}'.format(corridor_number),
        }

    def get_racks(self, region):
        # This function is not required since the excel plugin
        # already provide rack information.
        pass

    def _get_excel_obj(self):
        """ Creation of an ExcelParser object to store site information.

        The information is obtained based on a excel spec yaml file.
        This spec contains row, column and sheet information of
        the excel file from where site specific data can be extracted.
        """
        self.excel_obj = ExcelParser(self.excel_path, self.excel_spec)

    def _extract_raw_data_from_excel(self):
        """ Extracts raw information from excel file based on excel spec"""
        self.parsed_xl_data = self.excel_obj.get_data()

    def _get_network_name_from_vlan_name(self, vlan_name):
        """ network names are ksn, oam, oob, overlay, storage, pxe


        This is a utility function to determine the vlan acceptable
        vlan from the name extracted from excel file

        The following mapping rules apply:
            vlan_name contains "ksn or calico"  the network name is "calico"
            vlan_name contains "storage" the network name is "storage"
            vlan_name contains "server"  the network name is "oam"
            vlan_name contains "ovs"  the network name is "overlay"
            vlan_name contains "oob" the network name is "oob"
            vlan_name contains "pxe" the network name is "pxe"
        """
        network_names = [
            'ksn|calico', 'storage', 'oam|server', 'ovs|overlay', 'oob', 'pxe'
        ]
        for name in network_names:
            # Make a pattern that would ignore case.
            # if name is 'ksn' pattern name is '(?i)(ksn)'
            name_pattern = "(?i)({})".format(name)
            if re.search(name_pattern, vlan_name):
                if name is 'ksn|calico':
                    return 'calico'
                if name is 'storage':
                    return 'storage'
                if name is 'oam|server':
                    return 'oam'
                if name is 'ovs|overlay':
                    return 'overlay'
                if name is 'oob':
                    return 'oob'
                if name is 'pxe':
                    return 'pxe'
        # if nothing matches
        LOG.error(
            "Unable to recognize VLAN name extracted from Plugin data source")
        return ("")

    def _get_formatted_server_list(self, server_list):
        """ Format dns and ntp server list as comma separated string """

        # dns/ntp server info from excel is of the format
        # 'xxx.xxx.xxx.xxx, (aaa.bbb.ccc.com)'
        # The function returns a list of comma separated dns ip addresses
        servers = []
        for data in server_list:
            if '(' not in data:
                servers.append(data)
        formatted_server_list = ','.join(servers)
        return formatted_server_list

    def _get_rack(self, host):
        """
        Get rack id  from the rack string extracted
        from xl
        """
        rack_pattern = r'\w.*(r\d+)\w.*'
        rack = re.findall(rack_pattern, host)[0]
        if not self.region:
            self.region = host.split(rack)[0]
        return rack

    def _get_rackwise_hosts(self):
        """ Mapping hosts with rack ids """
        rackwise_hosts = {}
        hostnames = self.parsed_xl_data['ipmi_data'][1]
        racks = self._get_rack_data()
        for rack in racks:
            if rack not in rackwise_hosts:
                rackwise_hosts[racks[rack]] = []
            for host in hostnames:
                if rack in host:
                    rackwise_hosts[racks[rack]].append(host)
        LOG.debug("rackwise hosts:\n%s", pprint.pformat(rackwise_hosts))
        return rackwise_hosts

    def _get_rack_data(self):
        """ Format rack name """
        LOG.info("Getting rack data")
        racks = {}
        hostnames = self.parsed_xl_data['ipmi_data'][1]
        for host in hostnames:
            rack = self._get_rack(host)
            racks[rack] = rack.replace('r', 'rack')
        return racks
