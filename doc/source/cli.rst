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

**-v / --verbose** (Optional). False by default.

Enable debug logging.

Generate Intermediary
---------------------

Generates an intermediary file from passed excel data.

.. code-block:: bash

    ./spyglass.sh i -p <plugin_type> -x <engineering_excel_file> \
                    -e <excel_spec> -c <additional_site_config> -s <site_name>

Options
^^^^^^^

**-p / --plugin-type** "tugboat" by default.

The plugin to use to open engineering data. Two plugins are available by
default: "tugboat" and "formation". Tugboat can be used for reading Excel data.
Formation can be used to read data from remote sources.

**-f / --formation-target** (Required for "formation" plugin).

Target remote for the formation plugin. Accepts a url and a username and
password to access the url.

::

  -f <remote_url> <username> <password>

**-d / --intermediary-dir** (Optional).

Path where the intermediary file will be created. Must be a writeable
directory.

**-x / --excel-file** (Required for "tugboat" plugin).

Path to the engineering excel file. Multiple files can be included, provided
they follow the same specification. Must be readable file(s) in a Microsoft
Excel supported format (.xls, .xslx, etc...).

**-e / --excel-spec** (Required for "tugboat" plugin).

Path to the specification YAML that defines the content of the provided
engineering excel files. Must be a readable file in YAML format.

**-c / --site-configuration** (Optional).

Path to site specific configuration YAML. Must be a readable file.

**-s / --site-name** (Optional).

Name of the site for which the intermediary is generated.

Generate Manifests
------------------

Generates manifests from intermediary file created from passed excel data.
Intermediary data is always generated, but will not be saved unless specified.

.. code-block:: bash

    ./spyglass.sh m -t <plugin_type> -x <engineering_excel_file> \
                    -e <excel_spec> -c <additional_site_config> \
                    -s <site_name> -t <j2_template_directory>

Options
^^^^^^^

**-i / --save-intermediary** (Optional). False by default.

Saves the intermediary file used to make the manifests created by the command.

**-p / --plugin-type** "tugboat" by default.

The plugin to use to open engineering data. Two plugins are available by
default: "tugboat" and "formation". Tugboat can be used for reading Excel data.
Formation can be used to read data from remote sources.

**-f / --formation-target** (Required for "formation" plugin).

Target remote for the formation plugin. Requires a url, a username, and a
password to access the url.

::

  -f <remote_url> <username> <password>

**-d / --intermediary-dir** (Optional).

Path where the intermediary file will be created. Must be a writeable
directory.

**-x / --excel-file** (Required for "tugboat" plugin).

Path to the engineering excel file. Multiple files can be included, provided
they follow the same specification. Must be readable file(s) in a Microsoft
Excel supported format (.xls, .xslx, etc...).

**-e / --excel-spec** (Required for "tugboat" plugin).

Path to the specification YAML that defines the content of the provided
engineering excel files. Must be a readable file in YAML format.

**-c / --site-configuration** (Optional).

Path to site specific configuration YAML. Must be a readable file.

**-s / --site-name** (Optional).

Name of the site for which the intermediary is generated.

**-t / --template-dir** (Required).

Path to the Jinja2 template files that will be used to generate manifest files.
Must be a readable directory with Jinja2 files using the .j2 extension.

**-m / --manifest-dir** (Optional).

Path where generated manifest files should be written. Must be a writeable
directory.

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

**-t / --template-dir** (Required).

Path to the Jinja2 template files that will be used to generate manifest files.
Must be a readable directory with Jinja2 files using the .j2 extension.

**-m / --manifest-dir** (Optional).

Path where generated manifest files should be written. Must be a writeable directory.

Examples
========

Running Spyglass with Excel Plugin
----------------------------------

.. code-block:: bash

    spyglass m -i -p tugboat -x <Excel File> -e <Excel Spec> -c <Site Config> \
               -s <Region> -t <j2 template dir>

Generating intermediary and manifests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    spyglass m -i -p tugboat -x SiteDesignSpec_v0.1.xlsx \
               -e excel_spec_upstream.yaml -c site_config.yaml \
               -s airship-seaworthy -t <j2 template dir>

Generating intermediary without manifests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    spyglass i -p tugboat -x SiteDesignSpec_v0.1.xlsx \
               -e excel_spec_upstream.yaml -c site_config.yaml \
               -s airship-seaworthy

Generating manifests without intermediary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    spyglass m -p tugboat -x SiteDesignSpec_v0.1.xlsx \
               -e excel_spec_upstream.yaml -c site_config.yaml \
               -s airship-seaworthy --template_dir=<j2 template dir>

Generating manifests using intermediary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    spyglass mi <intermediary.yaml> -t <j2 template dir>

Where sample 'excel_spec_upstream.yaml', 'SiteDesignSpec_v0.1.xlsx'
'site_config.yaml' and J2 templates can be found under 'spyglass/examples'
folder.