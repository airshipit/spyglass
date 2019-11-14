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

==========================
Developer Quickstart Guide
==========================

To run your first spyglass job, follow these steps from inside the
airship-spyglass directory.

1. Install external dependencies if not already installed.

   .. code-block:: console

       sudo apt install -y python3-pip
       sudo apt install -y tox

2. Install Pipenv.

    .. code-block:: console

        pip3 install pipenv

2. Set up an environment with Pipenv

   .. code-block:: console

       pipenv install

3. Enter the Pipenv environment.

   .. code-block:: console

       pipenv shell

4. Install spyglass in the tox environment.

   .. code-block:: console

       pip3 install .

5. Run spyglass on the example files to generate an intermediate document.

   .. code-block:: console

       mkdir intermediate
       spyglass excel documents -s airship-seaworthy -d intermediate -i \
                  --excel-spec spyglass/examples/excel_spec.yaml \
                  --excel-file spyglass/examples/SiteDesignSpec_v0.1.xlsx \
                  --site-configuration spyglass/examples/site_config.yaml \
                  --template-dir spyglass/examples/templates/

6. Run spyglass on the intermediate document to generate manifests.

   .. code-block:: console

       mkdir manifest_dir
       spyglass mi intermediate/airship-seaworthy_intermediary.yaml \
                   -m manifest_dir/ -t spyglass/examples/templates/