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

============
Spyglass CLI
============

The Spyglass CLI is used in conjunction with the script ``tools/spyglass.sh``.

.. note::

  The default workspace for the ``spyglass.sh`` script is ``/workspace``. The
  examples below require that this workspace be used.

CLI Options
===========

**-v / \\-\\-verbose** (Optional). False by default.

Enable debug logging.

Excel Plugin
************

Commands available under the Excel plugin package.

Generate Intermediary
---------------------

Generates an intermediary file from passed Excel data.

.. code-block:: bash

    ./spyglass.sh excel intermediary -x <engineering_excel_file> \
                    -e <excel_spec> \
                    -c <additional_site_config> \
                    -s <site_name>

Options
^^^^^^^

**-d / \\-\\-intermediary-dir** (Optional).

Path where the intermediary file will be created. Must be a writeable
directory.

**-x / \\-\\-excel-file** (Required for Excel plugin).

Path to the engineering Excel file. Multiple files can be included, provided
they follow the same specification. Must be readable file(s) in a Microsoft
Excel supported format (.xls, .xslx, etc...).

**-e / \\-\\-excel-spec** (Required for Excel plugin).

Path to the specification YAML that defines the content of the provided
engineering Excel files. Must be a readable file in YAML format.

**-c / \\-\\-site-configuration** (Optional).

Path to site specific configuration YAML. Must be a readable file.

**\\-\\-intermediary-schema** (Optional).

Path to the intermediary schema to be used for validation.

**\\-\\-no-validation** (Optional).

Skips validation on generated intermediary data.

**-s / \\-\\-site-name** (Optional).

Name of the site for which the intermediary is generated.

Generate Manifests
------------------

Generates manifests from intermediary file created from passed Excel data.
Intermediary data is always generated, but will not be saved unless specified.

.. code-block:: bash

    ./spyglass.sh excel documents -x <engineering_excel_file> \
                    -e <excel_spec> -c <additional_site_config> \
                    -s <site_name> -t <j2_template_directory>

Options
^^^^^^^

**-i / \\-\\-generate-intermediary** (Optional). False by default.

Saves the intermediary file used to make the manifests created by the command.

**-d / \\-\\-intermediary-dir** (Optional).

Path where the intermediary file will be created. Must be a writeable
directory.

**-x / \\-\\-excel-file** (Required for Excel plugin).

Path to the engineering Excel file. Multiple files can be included, provided
they follow the same specification. Must be readable file(s) in a Microsoft
Excel supported format (.xls, .xslx, etc...).

**-e / \\-\\-excel-spec** (Required for Excel plugin).

Path to the specification YAML that defines the content of the provided
engineering Excel files. Must be a readable file in YAML format.

**-c / \\-\\-site-configuration** (Optional).

Path to site specific configuration YAML. Must be a readable file.

**\\-\\-intermediary-schema** (Optional).

Path to the intermediary schema to be used for validation.

**\\-\\-no-validation** (Optional).

Skips validation on generated intermediary data.

**-s / \\-\\-site-name** (Optional).

Name of the site for which the intermediary is generated.

**-t / \\-\\-template-dir** (Required).

Path to the Jinja2 template files that will be used to generate manifest files.
Must be a readable directory with Jinja2 files using the .j2 extension.

**-m / \\-\\-manifest-dir** (Optional).

Path where generated manifest files should be written. Must be a writeable
directory.

General
*******

Generate Manifests from Intermediary
------------------------------------

Generates manifests using an existing intermediary file. This is a shortcut to
skip intermediary generation if it has already been completed.

.. code-block:: bash

    ./spyglass.sh mi <intermediary_file> -t <j2_template_directory>

Arguments
^^^^^^^^^

**INTERMEDIARY_FILE** (Required).

Path to an existing intermediary YAML file that can be used to generate
manifests.

Options
^^^^^^^

**-t / \\-\\-template-dir** (Required).

Path to the Jinja2 template files that will be used to generate manifest files.
Must be a readable directory with Jinja2 files using the .j2 extension.

**-m / \\-\\-manifest-dir** (Optional).

Path where generated manifest files should be written. Must be a writeable
directory.

**\\-\\-force** (Optional).

Forces manifests to be written, regardless of undefined data.

Validate Documents
------------------

Validates pegleg documents against their schema.

.. code-block:: bash

    spyglass validate -d <DOCUMENT_PATH> -p <SCHEMA_PATH>

Options
^^^^^^^

**-d / \\-\\-document-path**

Path to the document(s) to validate.

**-p / \\-\\-schema-path**

Path to a schema or directory of schema files used to validate documents in
document path.

Examples
========

Running Spyglass with Excel Plugin
**********************************

.. code-block:: bash

    spyglass excel documents -i -x <Excel File> -e <Excel Spec> \
               -c <Site Config> -s <Site Name> -t <j2 template dir>

Generating intermediary and manifests
-------------------------------------

.. code-block:: bash

    spyglass excel documents -i \
           -x ../spyglass-plugin-xls/spyglass_plugin_xls/examples/SiteDesignSpec_v0.1.xlsx \
           -e ../spyglass-plugin-xls/spyglass_plugin_xls/examples/excel_spec.yaml \
           -c spyglass/examples/site_config.yaml \
           -s airship-seaworthy -t spyglass/examples/templates/

Generating intermediary without manifests
-----------------------------------------

.. code-block:: bash

    spyglass excel intermediary \
           -x ../spyglass-plugin-xls/spyglass_plugin_xls/examples/SiteDesignSpec_v0.1.xlsx \
           -e ../spyglass-plugin-xls/spyglass_plugin_xls/examples/excel_spec.yaml \
           -c spyglass/examples/site_config.yaml \
           -s airship-seaworthy

Generating manifests without intermediary
-----------------------------------------

.. code-block:: bash

    spyglass excel documents \
           -x ../spyglass-plugin-xls/spyglass_plugin_xls/examples/SiteDesignSpec_v0.1.xlsx \
           -e ../spyglass-plugin-xls/spyglass_plugin_xls/examples/excel_spec.yaml \
           -c spyglass/examples/site_config.yaml \
           -s airship-seaworthy -t spyglass/examples/templates/

Generating manifests using intermediary
***************************************

.. code-block:: bash

    spyglass mi <intermediary.yaml> -t <j2 template dir>

Where sample `excel_spec.yaml` and `SiteDesignSpec_v0.1.xlsx` can be found in
spyglass-plugin-xls in the `spyglass_plugin_xls/examples` folder. The Jinja2
templates and `site_config.yaml` can be found in the `spyglass/examples`
folder.

Validate Documents
******************

.. code-block:: bash

    spyglass validate -d <DOCUMENT_PATH> -p <SCHEMA_PATH>
