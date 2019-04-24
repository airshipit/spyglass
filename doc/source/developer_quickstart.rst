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

==========================
Developer Quickstart Guide
==========================

To run your first spyglass job, follow these steps from inside the
airship-spyglass directory.

1. Install external dependencies if not already installed.

   .. code-block:: console

   sudo apt install -y python3-pip
   sudo apt install -y tox

2. Set up an environment with tox.

   .. code-block:: console

   tox -e py36 --notest

3. Enter the tox environment.

   .. code-block:: console

   source .tox/py36/bin/activate

4. Install spyglass in the tox environment.

   .. code-block:: console

   pip install -e .

5. Run spyglass on the example files to generate an intermediate document.

   .. code-block:: console

   mkdir intermediate
   spyglass -g -s airship-seaworthy -t tugboat \
   -idir intermediate \
   --excel_spec spyglass/examples/excel_spec.yaml \
   --excel spyglass/examples/SiteDesignSpec_v0.1.xlsx \
   --additional_config spyglass/examples/site_config.yaml \
   --template_dir spyglass/examples/templates/

6. Run spyglass on the intermediate document to generate manifests.

   .. code-block:: console

   mkdir manifest_dir
   spyglass -m -i intermediate/airship-seaworthy_intermediary.yaml \
   -mdir manifest_dir/ -tdir spyglass/examples/templates/
