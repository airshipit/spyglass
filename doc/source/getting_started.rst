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
----------------

Spyglass is a data extraction tool which can interface with
different input data sources to generate site manifest YAML files.
The data sources will provide all the configuration data needed
for a site deployment. These site manifest YAML files generated
by spyglass will be saved in a Git repository, from where Pegleg
can access and aggregate them. This aggregated file can then be
fed to Shipyard for site deployment / updates.

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

Basic Usage
-----------

Before using Spyglass you must:


1. Clone the Spyglass repository:

   .. code-block:: console

    git clone https://github.com/att-comdev/tugboat/tree/spyglass

2. Install the required packages in spyglass:

   .. code-block:: console

     pip3 install -r tugboat/requirements.txt


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
  -e, --edit_intermediary / -nedit, --no_edit_intermediary
                                  Flag to let user edit intermediary
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


1. Running Spyglass with  Remote Data Source Plugin

spyglass -mg --type formation -f <URL> -u <user_id> -p <password> -d <site_config> -s <sitetype> --template_dir=<j2 template dir>

2. Running Spyglass with Excel Plugin

spyglass -mg --type tugboat -x <Excel File> -e <Excel Spec> -d <Site Config> -s <Region> --template_dir=<j2 template dir>

for example:
spyglass -mg -t tugboat -x SiteDesignSpec_v0.1.xlsx -e excel_spec_upstream.yaml -d site_config.yaml -s airship-seaworthy --template_dir=<j2 template dir>
Where sample 'excel_spec_upstream.yaml', 'SiteDesignSpec_v0.1.xlsx'
'site_config.yaml' and J2 templates can be found under 'spyglass/examples'
folder

