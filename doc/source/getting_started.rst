..
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

===============
Getting Started
===============

What is Spyglass?
-----------------

Spyglass is a data extraction tool which can interface with
different input data sources to generate site manifest YAML files.
The data sources will provide all the configuration data needed
for a site deployment. These site manifest YAML files generated
by spyglass will be saved in a Git repository, from where Pegleg
can access and aggregate them. This aggregated file can then be
fed to Shipyard for site deployment / updates.
Reference: https://review.opendev.org/#/c/605227

Architecture
------------

::

        +-----------+           +-------------+
        |           |           |  +-------+  |
        |           |   +------>|  |Generic|  |
    +-----------+   |   |       |  |Object |  |
    |Tugboat(Xl)| I |   |       |  +-------+  |
    |Plugin     | N |   |       |     |       |
    +-----------+ T |   |       |     |       |
        |         E |   |       |  +------+   |
   +------------+ R |   |       |  |Parser|   +------> Intermediary YAML
   |Remote Data | F |---+       |  +------+   |
   |SourcePlugin| A |           |     |       |
   +------------+ C |           |     |(Intermediary YAML)
        |         E |           |     |       |
        |           |           |     |       |
        |         H |           |     v       |
        |         A |           |  +---------+|(templates)    +------------+
        |         N |           |  |Site     |+<--------------|Repository  |
        |         D |           |  |Processor||-------------->|Adapter     |
        |         L |           |  +---------+|(Generated     +------------+
        |         E |           |      ^      | Site Manifests)
        |         R |           |  +---|-----+|
        |           |           |  |  J2     ||
        |           |           |  |Templates||
        |           |           |  +---------+|
        +-----------+           +-------------+

--

Supported Features
------------------
1. Tugboat Plugin: Supports extracting site data from Excel files and
   then generate site manifests for sitetype:airship-seaworthy.
   Find more documentation for Tugboat, see :ref:`tugboatinfo`.

2. Remote Data Source Plugin: Supports extracting site data from a REST
   endpoint.

Future Work
-----------
1) Schema based manifest generation instead of Jinja2 templates. It shall
be possible to cleanly transition to this schema based generation keeping a unique
mapping between schema and generated manifests. Currently this is managed by
considering a mapping of j2 templates with schemas and site type.

List of Generated Site Manifests:
---------------------------------
The spyglass uses the plugin data source to generate the following site
manifests:

- site-definition.yaml
- profile/
- profile/region.yaml
- baremetal/
- baremetal/nodes.yaml
- networks/
- networks/common_addresses.yaml
- networks/control-plane-addresses.yaml
- networks/physical/
- networks/physical/networks.yaml
- software/
- software/charts/
- software/charts/osh/
- software/charts/osh/openstack-tenant-ceph/
- software/charts/osh/openstack-tenant-ceph/ceph-client.yaml
- software/charts/ucp/
- software/charts/ucp/divingbell/
- software/charts/ucp/divingbell/divingbell.yaml
- software/config/
- software/config/corridor.yaml
- software/config/common-software-config.yaml
- deployment/
- deployment/deployment-strategy.yaml
- pki/
- pki/kubelet-node-pkicatalog.yaml

Spyglass maintains corresponding J2 templates for these files
and then those are processed with site information obtained
from plugin data source.

In some cases, the site might require additional site
manifests containing static information independent of the
plugin data received. In such cases one can just place the
corresponding J2 templates in the appropriate folder.

Basic Usage
-----------

Before using Spyglass you must:


1. Clone the Spyglass repository:

   .. code-block:: console

    git clone https://opendev.org/airship/spyglass.git

2. Install the required packages in spyglass:

   .. code-block:: console

     pip3 install -r airship-spyglass/requirements.txt


CLI Options
-----------

Usage: spyglass [OPTIONS]

Options:
  -s, --site TEXT                 Specify the site for which manifests to be
                                  generated
  -t, --type TEXT                 Specify the plugin type formation or tugboat
  -f, --formation_url TEXT        Specify the formation url
  -u, --formation_user TEXT       Specify the formation user id
  -p, --formation_password TEXT   Specify the formation user password
  -i, --intermediary PATH         Intermediary file path  generate manifests,
                                  use -m also with this option
  -d, --additional_config PATH    Site specific configuraton details
  -g, --generate_intermediary     Dump intermediary file from passed excel and
                                  excel spec
  -idir, --intermediary_dir PATH  The path where intermediary file needs to be
                                  generated
  -m, --generate_manifests        Generate manifests from the generated
                                  intermediary file
  -mdir, --manifest_dir PATH      The path where manifest files needs to be
                                  generated
  -x, --excel PATH                Path to engineering excel file, to be passed
                                  with generate_intermediary
  -e, --excel_spec PATH           Path to excel spec, to be passed with
                                  generate_intermediary
  -l, --loglevel INTEGER          Loglevel NOTSET:0 ,DEBUG:10,     INFO:20,
                                  WARNING:30, ERROR:40, CRITICAL:50  [default:
                                  20]
  --help                          Show this message and exit.

--------
Examples
--------

1. Running Spyglass with  Remote Data Source Plugin

spyglass -mg --type formation -f <URL> -u <user_id> -p <password> -d <site_config> -s <sitetype> --template_dir=<j2 template dir>

2. Running Spyglass with Excel Plugin

spyglass -mg --type tugboat -x <Excel File> -e <Excel Spec> -d <Site Config> -s <Region> --template_dir=<j2 template dir>

for example:
  2.1 Generating intermediary and manifests
    spyglass -mg -t tugboat -x SiteDesignSpec_v1.1.xlsx -e excel_spec_upstream.yaml -d site_config.yaml -s airship-seaworthy --template_dir=<j2 template dir>

  2.2 Generating intermediary without manifests
    spyglass -g -t tugboat -x SiteDesignSpec_v1.1.xlsx -e excel_spec_upstream.yaml -d site_config.yaml -s airship-seaworthy

  2.3 Generating manifests without intermediary
    spyglass -m -t tugboat -x SiteDesignSpec_v1.1.xlsx -e excel_spec_upstream.yaml -d site_config.yaml -s airship-seaworthy --template_dir=<j2 template dir>

  2.4 Generating manifests using intermediary
    spyglass -mi <intermediary.yaml> --template_dir=<j2 template dir>

Where sample 'excel_spec_upstream.yaml', 'SiteDesignSpec_v0.1.xlsx'
'site_config.yaml' and J2 templates can be found under 'spyglass/examples'
folder
