===============
Getting Started
===============

What is Spyglass?
-----------------

Spyglass is a data extraction tool which can interface with
different input data sources to generate site manifest YAML files.
The data sources will provide all the configuration data needed
for a site deployment. These site manifest YAML files generated
by Spyglass will be saved in a Git repository, from where Pegleg
can access and aggregate them. This aggregated file can then be
fed to Shipyard for site deployment / updates.
Reference: `airship-specs`_

Architecture
------------

::

        +-----------+           +-------------+
        |           |           |  +-------+  |
        |           |   +------>|  |Generic|  |
    +-----------+   |   |       |  |Object |  |
    |Excel      | I |   |       |  +-------+  |
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
1. `Spyglass Excel Plugin <https://opendev.org/airship/spyglass-plugin-xls>`_

Future Work
-----------
1. Schema based manifest generation instead of Jinja2 templates. It shall
be possible to cleanly transition to this schema based generation keeping a
unique mapping between schema and generated manifests. Currently this is
managed by considering a mapping of j2 templates with schemas and site type.

List of Generated Site Manifests:
---------------------------------
The Spyglass uses the plugin data source to generate the following site
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


1. Clone the Spyglass repository::

    git clone https://opendev.org/airship/spyglass.git

2. Install the required packages in Spyglass::

    pip3 install pipenv && pipenv install

3. Launch the pipenv from your Spyglass directory::

    pipenv shell

4. Install Spyglass into the pipenv::

    pip3 install .

.. _airship-specs: https://airshipit.readthedocs.io/projects/specs/en/latest/specs/1.x/approved/data_config_generator.html