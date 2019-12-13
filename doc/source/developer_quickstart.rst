==========================
Developer Quickstart Guide
==========================

1. Clone the Spyglass directory. (Perform the following steps from inside the
spyglass directory)

   .. code-block:: console

       git clone https://opendev.org/airship/spyglass.git

2. Install external dependencies if not already installed.

   .. code-block:: console

       sudo apt install -y python3-pip
       sudo apt install -y tox

3. Install Pipenv.

   .. code-block:: console

       pip3 install pipenv

4. Set up an environment with Pipenv

   .. code-block:: console

       pipenv install

5. Enter the Pipenv environment.

   .. code-block:: console

       pipenv shell

6. Install spyglass in the tox environment.

   .. code-block:: console

       pip3 install .

7. Run spyglass on the example files to generate an intermediate document.

   .. code-block:: console

       mkdir intermediate
       spyglass excel documents -s airship-seaworthy -d intermediate -i \
           --excel-spec ../spyglass-plugin-xls/spyglass_plugin_xls/examples/excel_spec.yaml \
           --excel-file ../spyglass-plugin-xls/spyglass_plugin_xls/examples/SiteDesignSpec_v0.1.xlsx \
           --site-configuration spyglass/examples/site_config.yaml \
           --template-dir spyglass/examples/templates/

8. Run spyglass on the intermediate document to generate manifests.

   .. code-block:: console

       mkdir manifest_dir
       spyglass mi intermediate/airship-seaworthy_intermediary.yaml \
                   -m manifest_dir/ -t spyglass/examples/templates/