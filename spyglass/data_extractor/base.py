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

import abc
import logging

from spyglass.data_extractor import models

LOG = logging.getLogger(__name__)


class BaseDataSourcePlugin(metaclass=abc.ABCMeta):
    """Provide basic hooks for data source plugins"""

    def __init__(self, region, **kwargs):
        self.source_type = None
        self.source_name = None
        self.region = region
        self.site_data = None

    @abc.abstractmethod
    def get_racks(self, region):
        """Return list of racks in the region

        :param string region: Region name
        :returns: list of Rack objects
        :rtype: list
        """

        return []

    @abc.abstractmethod
    def get_hosts(self, region, rack=None):
        """Return list of hosts in the region

        :param string region: Region name
        :param string rack: Rack name
        :returns: list of Host objects containing a rack's host data
        :rtype: list of models.Host
        """

        return []

    @abc.abstractmethod
    def get_networks(self, region):
        """Return list of networks in the region

        :param string region: Region name
        :returns: list of network data
        :rtype: list of models.VLANNetworkData
        """

        # TODO(nh863p): Expand the return type if they are rack level subnets
        # TODO(nh863p): Is ingress information can be provided here?
        return []

    @abc.abstractmethod
    def get_ips(self, region, host):
        """Return list of IPs on the host

        :param string region: Region name
        :param string host: Host name
        :returns: IPs per network on the host
        :rtype: models.IPList

        The network name from get_networks is expected to be the keys of this
        dict. In case some networks are missed, they are expected to be either
        DHCP or internally generated n the next steps by the design rules.
        """

        return {}

    @abc.abstractmethod
    def get_dns_servers(self, region):
        """Return the DNS servers

        :param string region: Region name
        :returns: DNS servers to be configured on host
        :rtype: models.ServerList
        """

        return []

    @abc.abstractmethod
    def get_ntp_servers(self, region):
        """Return the NTP servers

        :param string region: Region name
        :returns: NTP servers to be configured on host
        :rtype: models.ServerList
        """

        return []

    @abc.abstractmethod
    def get_ldap_information(self, region):
        """Return the LDAP server information

        :param string region: Region name
        :returns: LDAP server information
        :rtype: dict

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
        :rtype: str

        Example: example.com
        """

        return ""

    @abc.abstractmethod
    def get_site_info(self, region):
        """Return site data as a SiteInfo object

        :param region: Region name
        :return: general site data including location, domain, name, LDAP, NTP,
            DNS, and site type
        :rtype: models.SiteInfo
        """

        return None

    def extract_baremetal_information(self):
        """Get baremetal information from plugin

        :returns: racks and hosts as a list of Rack objects containing Host
                  data
        :rtype: list of models.Rack
        """

        LOG.info("Extract baremetal information from plugin")
        return self.get_racks(self.region)

    def extract_site_information(self):
        """Get site information from plugin

        :returns: site information including location, dns servers, ntp servers
                  ldap, and domain name
        :rtpe: models.SiteInfo
        """

        LOG.info("Extract site information from plugin")

        # Extract location information
        data = {
            'region_name': self.region,
            'dns': self.get_dns_servers(self.region),
            'ntp': self.get_ntp_servers(self.region),
            'ldap': self.get_ldap_information(self.region),
            'domain': self.get_domain_name(self.region)
        }
        data.update(self.get_location_information(self.region) or {})

        site_info = models.SiteInfo(**data)

        return site_info

    def extract_network_information(self):
        """Get network details from plugin like Subnets, DNS, NTP and LDAP

        :returns: networking data as a Network object
        :rtype: models.Network
        """

        LOG.info("Extract network information from plugin")
        networks = self.get_networks(self.region)

        # We are interested in only the below networks mentioned in
        # networks_to_scan, so look for these networks from the data
        # returned by plugin
        networks_to_scan = [
            "calico",
            "overlay",
            "pxe",
            "storage",
            "oam",
            "oob",
            "ingress",
        ]
        desired_networks = []
        for network in networks:
            if network.name in networks_to_scan:
                desired_networks.append(network)

        return models.Network(desired_networks)

    def extract_data(self):
        """Extract data from plugin

        Gather data related to baremetal, networks, storage and other site
        related information from plugin
        """

        LOG.info("Extract data from plugin")
        self.site_data = models.SiteDocumentData(
            self.extract_site_information(),
            self.extract_network_information(),
            self.extract_baremetal_information())
        return self.site_data

    def apply_additional_data(self, extra_data):
        """Apply any additional inputs from user

        In case plugin does not provide some data, user can specify
        the same as part of additional data in form of dict. The user
        provided dict will be merged recursively to site_data.
        If there is repetition of data then additional data supplied
        shall take precedence.
        """

        LOG.info("Update site data with additional input")
        self.site_data.merge_additional_data(extra_data)
