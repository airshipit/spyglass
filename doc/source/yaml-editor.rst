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

.. _yaml-editor-info:

===========
Yaml Editor
===========

What is Yaml Editor?
--------------------

Yaml Editor is a spyglass utility which lets user edit their generated
intermediary file in a browser window. It is a minimal flask app which is
invoked from the parser engine in order to let user edit fields which
could not be fetched via :ref:`tugboatinfo` plugin.


Yaml Editor Utility Inputs
--------------------------

a) Yaml File: Yaml file required to be edited (This is required field)
b) Port: Port on which app shall be running
c) Host: This is only used to form URL which can be followed to open file in browser
d) String: String which is required to be updated in the file (default is '#CHANGE_ME')

Yaml Editor Utility Usage
-------------------------

    With Spyglass (edit option is True by default):
    ::

        spyglass -mg --edit_intermediary -t tugboat -x SiteDesignSpec_v0.1.xlsx -e excel_spec_upstream.yaml -d site_config.yaml -s airship-seaworthy --template_dir=<relative path to '../examples/templates'

    As a stand-alone editor:
    ::

        yaml-editor -f <yaml-file>

    Help:
    ::

        > yaml-editor --help
        Usage: yaml-editor [OPTIONS]

        Options:
        -f, --file FILENAME  Path with file name to the intermediary yaml file.
                            [required]
        -h, --host TEXT      Optional host parameter to run Flask on.
        -p, --port INTEGER   Optional port parameter to run Flask on.
        -s, --string TEXT    Text which is required to be changed on yaml file.
        --help               Show this message and exit.
