
      Copyright 2018 AT&T Intellectual Property.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

.. _tugboatinfo:

=======
Tugboat
=======

What is Tugboat?
----------------

Tugboat is a Spyglass plugin to generate airship-seaworthy site manifest files
from an excel based engineering spec. The plugin is configured with an Excel
sheet and its corresponding excel specification as inputs. Spyglass uses this
plugin to construct an intermediary yaml which is processed further using J2
templates to generate site manifests.

Excel specification
-------------------
Excel Spec is like an index to the Excel sheet to look for the data to be
collected by the tool. Excel Spec Sample specifies all the details that
need to be filled by the Deployment Engineer.

Below is the definition for each key in the Excel spec

::


     ipmi_sheet_name - name of the sheet from where IPMI and host profile information is to be read
     start_row - row number from where the IPMI and host profile information starts
     end_row - row number from where the IPMI and host profile information ends
     hostname_col - column number where the hostnames are to be read from
     ipmi_address_col - column number from where the ipmi addresses are to be read
     host_profile_col - column number from where the host profiles are to be read
     ipmi_gateway_col - column number from where the ipmi gateways are to be read
     private_ip_sheet - name of the sheet which has the private IP information
     net_type_col - column number from where the network type is to be read
     vlan_col - column number from where the network vlan is to be read
     vlan_start_row - row number from where the vlan information starts
     vlan_end_row - row number from where the vlan information ends
     net_start_row - row number from where the network information starts
     net_end_row - row number from where the network information ends
     net_col - column number where the IP ranges for network is to be read
     net_vlan_col - column number where the vlan information is present in the pod wise network section
     public_ip_sheet - name of the sheet which has the public IP information
     oam_vlan_col - column number from where the OAM vlan information is to be read from
     oam_ip_row - row number from where the OAM network information is to be read from
     oam_ip_col - column number from where the OAM network information is to be read from
     oob_net_row - row number which has the OOB network subnet ranges
     oob_net_start_col - column number from where the OOB network ranges start
     oob_net_end_col - column number from where the OOB network ranges end
     ingress_ip_row - row number from where the Ingress network information is to be read from
     dns_ntp_ldap_sheet - name of the sheet which has the DNS, NTP and LDAP information
     login_domain_row - row number which has the ldap login domain
     ldap_col - column number which has the all ldap related information
     global_group - row number which has the ldap group information
     ldap_search_url_row - row number which has the ldap url
     ntp_row - row number which has the ntp information
     ntp_col - column number which has the ntp information
     dns_row - row number which has the dns information
     dns_col - column number which has the dns information
     domain_row - row number which has the domain information
     domain_col - column number which has the domain information
     location_sheet - name of the sheet which has the location information
     column - column number which has all the information
     corridor_row - row number which has the corridor information
     site_name_row - row number which has the site name
     state_name_row - row number which has the state name
     country_name_row - row number which has the country name
     clli_name_row - row number which has CLLI information

Example: Tugboat Plugin Usage
-----------------------------
1. Required Input(Refer to 'spyglass/examples' folder to get these inputs)
   a) Excel File: SiteDesignSpec_v0.1.xlsx
   b) Excel Spec: excel_spec_upstream.yaml
   c) Site Config: site_config.yaml
   d) Template_dir: '../examples/templates'
   c) Site name: airship-seaworthy

2. Spyglass CLI Command:
   spyglass -mg -t tugboat -x SiteDesignSpec_v0.1.xlsx -e excel_spec_upstream.yaml -d site_config.yaml -s airship-seaworthy --template_dir=<relative path to '../examples/templates'

