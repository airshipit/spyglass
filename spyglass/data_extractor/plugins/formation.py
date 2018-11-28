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

import logging
import pprint
import re
import requests
import formation_client
import urllib3

from spyglass.data_extractor.base import BaseDataSourcePlugin

from spyglass.data_extractor.custom_exceptions import (
    ApiClientError, ConnectionError, MissingAttributeError,
    TokenGenerationError)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOG = logging.getLogger(__name__)


class FormationPlugin(BaseDataSourcePlugin):
    def __init__(self, region):
        # Save site name is valid
        try:
            assert region is not None
            super().__init__(region)
        except AssertionError:
            LOG.error("Site: None! Spyglass exited!")
            LOG.info("Check spyglass --help for details")
            exit()

        self.source_type = 'rest'
        self.source_name = 'formation'

        # Configuration parameters
        self.formation_api_url = None
        self.user = None
        self.password = None
        self.token = None

        # Formation objects
        self.client_config = None
        self.formation_api_client = None

        # Site related data
        self.region_zone_map = {}
        self.site_name_id_mapping = {}
        self.zone_name_id_mapping = {}
        self.region_name_id_mapping = {}
        self.rack_name_id_mapping = {}
        self.device_name_id_mapping = {}
        LOG.info("Initiated data extractor plugin:{}".format(self.source_name))

    def set_config_opts(self, conf):
        """ Sets the config params passed by CLI"""
        LOG.info("Plugin params passed:\n{}".format(pprint.pformat(conf)))
        self._validate_config_options(conf)
        self.formation_api_url = conf['url']
        self.user = conf['user']
        self.password = conf['password']
        self.token = conf.get('token', None)

        self._get_formation_client()
        self._update_site_and_zone(self.region)

    def get_plugin_conf(self, kwargs):
        """ Validates the plugin param and return if success"""
        try:
            assert (kwargs['formation_url']
                    ) is not None, "formation_url is Not Specified"
            url = kwargs['formation_url']
            assert (kwargs['formation_user']
                    ) is not None, "formation_user is Not Specified"
            user = kwargs['formation_user']
            assert (kwargs['formation_password']
                    ) is not None, "formation_password is Not Specified"
            password = kwargs['formation_password']
        except AssertionError:
            LOG.error("Insufficient plugin parameter! Spyglass exited!")
            raise
            exit()

        plugin_conf = {'url': url, 'user': user, 'password': password}
        return plugin_conf

    def _validate_config_options(self, conf):
        """Validate the CLI params passed

        The method checks for missing parameters and terminates
        Spyglass execution if found so.
        """

        missing_params = []
        for key in conf.keys():
            if conf[key] is None:
                missing_params.append(key)
        if len(missing_params) != 0:
            LOG.error("Missing Plugin Params{}:".format(missing_params))
            exit()

    # Implement helper classes

    def _generate_token(self):
        """Generate token for Formation
        Formation API does not provide separate resource to generate
        token. This is a workaround to call directly Formation API
        to get token instead of using Formation client.
        """
        # Create formation client config object
        self.client_config = formation_client.Configuration()
        self.client_config.host = self.formation_api_url
        self.client_config.username = self.user
        self.client_config.password = self.password
        self.client_config.verify_ssl = False

        # Assumes token is never expired in the execution of this tool
        if self.token:
            return self.token

        url = self.formation_api_url + '/zones'
        try:
            token_response = requests.get(
                url,
                auth=(self.user, self.password),
                verify=self.client_config.verify_ssl)
        except requests.exceptions.ConnectionError:
            raise ConnectionError('Incorrect URL: {}'.format(url))

        if token_response.status_code == 200:
            self.token = token_response.json().get('X-Subject-Token', None)
        else:
            raise TokenGenerationError(
                'Unable to generate token because {}'.format(
                    token_response.reason))

        return self.token

    def _get_formation_client(self):
        """Create formation client object

        Formation uses X-Auth-Token for authentication and should be in
        format "user|token".
        Generate the token and add it formation config object.
        """
        token = self._generate_token()
        self.client_config.api_key = {'X-Auth-Token': self.user + '|' + token}
        self.formation_api_client = formation_client.ApiClient(
            self.client_config)

    def _update_site_and_zone(self, region):
        """Get Zone name and Site name from region"""

        zone = self._get_zone_by_region_name(region)
        site = self._get_site_by_zone_name(zone)

        # zone = region[:-1]
        # site = zone[:-1]

        self.region_zone_map[region] = {}
        self.region_zone_map[region]['zone'] = zone
        self.region_zone_map[region]['site'] = site

    def _get_zone_by_region_name(self, region_name):
        zone_api = formation_client.ZonesApi(self.formation_api_client)
        zones = zone_api.zones_get()

        # Walk through each zone and get regions
        # Return when region name matches
        for zone in zones:
            self.zone_name_id_mapping[zone.name] = zone.id
            zone_regions = self.get_regions(zone.name)
            if region_name in zone_regions:
                return zone.name

        return None

    def _get_site_by_zone_name(self, zone_name):
        site_api = formation_client.SitesApi(self.formation_api_client)
        sites = site_api.sites_get()

        # Walk through each site and get zones
        # Return when site name matches
        for site in sites:
            self.site_name_id_mapping[site.name] = site.id
            site_zones = self.get_zones(site.name)
            if zone_name in site_zones:
                return site.name

        return None

    def _get_site_id_by_name(self, site_name):
        if site_name in self.site_name_id_mapping:
            return self.site_name_id_mapping.get(site_name)

        site_api = formation_client.SitesApi(self.formation_api_client)
        sites = site_api.sites_get()
        for site in sites:
            self.site_name_id_mapping[site.name] = site.id
            if site.name == site_name:
                return site.id

    def _get_zone_id_by_name(self, zone_name):
        if zone_name in self.zone_name_id_mapping:
            return self.zone_name_id_mapping.get(zone_name)

        zone_api = formation_client.ZonesApi(self.formation_api_client)
        zones = zone_api.zones_get()
        for zone in zones:
            if zone.name == zone_name:
                self.zone_name_id_mapping[zone.name] = zone.id
                return zone.id

    def _get_region_id_by_name(self, region_name):
        if region_name in self.region_name_id_mapping:
            return self.region_name_id_mapping.get(region_name)

        for zone in self.zone_name_id_mapping:
            self.get_regions(zone)

        return self.region_name_id_mapping.get(region_name, None)

    def _get_rack_id_by_name(self, rack_name):
        if rack_name in self.rack_name_id_mapping:
            return self.rack_name_id_mapping.get(rack_name)

        for zone in self.zone_name_id_mapping:
            self.get_racks(zone)

        return self.rack_name_id_mapping.get(rack_name, None)

    def _get_device_id_by_name(self, device_name):
        if device_name in self.device_name_id_mapping:
            return self.device_name_id_mapping.get(device_name)

        self.get_hosts(self.zone)

        return self.device_name_id_mapping.get(device_name, None)

    def _get_racks(self, zone, rack_type='compute'):
        zone_id = self._get_zone_id_by_name(zone)
        rack_api = formation_client.RacksApi(self.formation_api_client)
        racks = rack_api.zones_zone_id_racks_get(zone_id)

        racks_list = []
        for rack in racks:
            rack_name = rack.name
            self.rack_name_id_mapping[rack_name] = rack.id
            if rack.rack_type.name == rack_type:
                racks_list.append(rack_name)

        return racks_list

    # Functions that will be used internally within this plugin

    def get_zones(self, site=None):
        zone_api = formation_client.ZonesApi(self.formation_api_client)

        if site is None:
            zones = zone_api.zones_get()
        else:
            site_id = self._get_site_id_by_name(site)
            zones = zone_api.sites_site_id_zones_get(site_id)

        zones_list = []
        for zone in zones:
            zone_name = zone.name
            self.zone_name_id_mapping[zone_name] = zone.id
            zones_list.append(zone_name)

        return zones_list

    def get_regions(self, zone):
        zone_id = self._get_zone_id_by_name(zone)
        region_api = formation_client.RegionApi(self.formation_api_client)
        regions = region_api.zones_zone_id_regions_get(zone_id)
        regions_list = []
        for region in regions:
            region_name = region.name
            self.region_name_id_mapping[region_name] = region.id
            regions_list.append(region_name)

        return regions_list

    # Implement Abstract functions

    def get_racks(self, region):
        zone = self.region_zone_map[region]['zone']
        return self._get_racks(zone, rack_type='compute')

    def get_hosts(self, region, rack=None):
        zone = self.region_zone_map[region]['zone']
        zone_id = self._get_zone_id_by_name(zone)
        device_api = formation_client.DevicesApi(self.formation_api_client)
        control_hosts = device_api.zones_zone_id_control_nodes_get(zone_id)
        compute_hosts = device_api.zones_zone_id_devices_get(
            zone_id, type='KVM')

        hosts_list = []
        for host in control_hosts:
            self.device_name_id_mapping[host.aic_standard_name] = host.id
            hosts_list.append({
                'name': host.aic_standard_name,
                'type': 'controller',
                'rack_name': host.rack_name,
                'host_profile': host.host_profile_name
            })

        for host in compute_hosts:
            self.device_name_id_mapping[host.aic_standard_name] = host.id
            hosts_list.append({
                'name': host.aic_standard_name,
                'type': 'compute',
                'rack_name': host.rack_name,
                'host_profile': host.host_profile_name
            })
        """
        for host in itertools.chain(control_hosts, compute_hosts):
            self.device_name_id_mapping[host.aic_standard_name] = host.id
            hosts_list.append({
            'name': host.aic_standard_name,
            'type': host.categories[0],
            'rack_name': host.rack_name,
            'host_profile': host.host_profile_name
            })
        """

        return hosts_list

    def get_networks(self, region):
        zone = self.region_zone_map[region]['zone']
        zone_id = self._get_zone_id_by_name(zone)
        region_id = self._get_region_id_by_name(region)
        vlan_api = formation_client.VlansApi(self.formation_api_client)
        vlans = vlan_api.zones_zone_id_regions_region_id_vlans_get(
            zone_id, region_id)

        # Case when vlans list is empty from
        # zones_zone_id_regions_region_id_vlans_get
        if len(vlans) is 0:
            # get device-id from the first host and get the network details
            hosts = self.get_hosts(self.region)
            host = hosts[0]['name']
            device_id = self._get_device_id_by_name(host)
            vlans = vlan_api.zones_zone_id_devices_device_id_vlans_get(
                zone_id, device_id)

        LOG.debug("Extracted region network information\n{}".format(vlans))
        vlans_list = []
        for vlan_ in vlans:
            if len(vlan_.vlan.ipv4) is not 0:
                tmp_vlan = {}
                tmp_vlan['name'] = self._get_network_name_from_vlan_name(
                    vlan_.vlan.name)
                tmp_vlan['vlan'] = vlan_.vlan.vlan_id
                tmp_vlan['subnet'] = vlan_.vlan.subnet_range
                tmp_vlan['gateway'] = vlan_.ipv4_gateway
                tmp_vlan['subnet_level'] = vlan_.vlan.subnet_level
                vlans_list.append(tmp_vlan)

        return vlans_list

    def get_ips(self, region, host=None):
        zone = self.region_zone_map[region]['zone']
        zone_id = self._get_zone_id_by_name(zone)

        if host:
            hosts = [host]
        else:
            hosts = []
            hosts_dict = self.get_hosts(zone)
            for host in hosts_dict:
                hosts.append(host['name'])

        vlan_api = formation_client.VlansApi(self.formation_api_client)
        ip_ = {}

        for host in hosts:
            device_id = self._get_device_id_by_name(host)
            vlans = vlan_api.zones_zone_id_devices_device_id_vlans_get(
                zone_id, device_id)
            LOG.debug("Received VLAN Network Information\n{}".format(vlans))
            ip_[host] = {}
            for vlan_ in vlans:
                # TODO(pg710r) We need to handle the case when incoming ipv4
                # list is empty
                if len(vlan_.vlan.ipv4) is not 0:
                    name = self._get_network_name_from_vlan_name(
                        vlan_.vlan.name)
                    ipv4 = vlan_.vlan.ipv4[0].ip
                    LOG.debug("vlan:{},name:{},ip:{},vlan_name:{}".format(
                        vlan_.vlan.vlan_id, name, ipv4, vlan_.vlan.name))
                    # TODD(pg710r) This code needs to extended to support ipv4
                    # and ipv6
                    # ip_[host][name] = {'ipv4': ipv4}
                    ip_[host][name] = ipv4

        return ip_

    def _get_network_name_from_vlan_name(self, vlan_name):
        """ network names are ksn, oam, oob, overlay, storage, pxe

        The following mapping rules apply:
            vlan_name contains "ksn"  the network name is "calico"
            vlan_name contains "storage" the network name is "storage"
            vlan_name contains "server"  the network name is "oam"
            vlan_name contains "ovs"  the network name is "overlay"
            vlan_name contains "ILO" the network name is "oob"
        """
        network_names = {
            'ksn': 'calico',
            'storage': 'storage',
            'server': 'oam',
            'ovs': 'overlay',
            'ILO': 'oob',
            'pxe': 'pxe'
        }

        for name in network_names:
            # Make a pattern that would ignore case.
            # if name is 'ksn' pattern name is '(?i)(ksn)'
            name_pattern = "(?i)({})".format(name)
            if re.search(name_pattern, vlan_name):
                return network_names[name]
        # Return empty string is vlan_name is not matched with network_names
        return ""

    def get_dns_servers(self, region):
        try:
            zone = self.region_zone_map[region]['zone']
            zone_id = self._get_zone_id_by_name(zone)
            zone_api = formation_client.ZonesApi(self.formation_api_client)
            zone_ = zone_api.zones_zone_id_get(zone_id)
        except formation_client.rest.ApiException as e:
            raise ApiClientError(e.msg)

        if not zone_.ipv4_dns:
            LOG.warn("No dns server")
            return []

        dns_list = []
        for dns in zone_.ipv4_dns:
            dns_list.append(dns.ip)

        return dns_list

    def get_ntp_servers(self, region):
        return []

    def get_ldap_information(self, region):
        return {}

    def get_location_information(self, region):
        """ get location information for a zone and return """
        site = self.region_zone_map[region]['site']
        site_id = self._get_site_id_by_name(site)
        site_api = formation_client.SitesApi(self.formation_api_client)
        site_info = site_api.sites_site_id_get(site_id)

        try:
            return {
                # 'corridor': site_info.corridor,
                'name': site_info.city,
                'state': site_info.state,
                'country': site_info.country,
                'physical_location_id': site_info.clli,
            }
        except AttributeError as e:
            raise MissingAttributeError('Missing {} information in {}'.format(
                e, site_info.city))

    def get_domain_name(self, region):
        try:
            zone = self.region_zone_map[region]['zone']
            zone_id = self._get_zone_id_by_name(zone)
            zone_api = formation_client.ZonesApi(self.formation_api_client)
            zone_ = zone_api.zones_zone_id_get(zone_id)
        except formation_client.rest.ApiException as e:
            raise ApiClientError(e.msg)

        if not zone_.dns:
            LOG.warn('Got None while running get domain name')
            return None

        return zone_.dns
