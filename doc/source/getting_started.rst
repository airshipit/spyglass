..
      Copyright 2019 AT&T Intellectual Property.
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
Reference: https://airshipit.readthedocs.io/projects/specs/en/latest/specs/approved/data_config_generator.html

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
1. Spyglass XLS Plugin: https://opendev.org/airship/spyglass-plugin-xls

Future Work
-----------
1) Schema based manifest generation instead of Jinja2 templates. It shall
be possible to cleanly transition to this schema based generation keeping a
unique mapping between schema and generated manifests. Currently this is
managed by considering a mapping of j2 templates with schemas and site type.

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

        pip3 install -r spyglass/requirements.txt
