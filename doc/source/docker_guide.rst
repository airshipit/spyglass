==================================
Running Spyglass in a Docker Image
==================================

This is a guide to creating a docker image locally and running Spyglass in the
docker image.

1. Before creating the Spyglass image, ensure you have cloned Spyglass_,
`Spyglass Excel plugin`_, and that you have installed `Docker CE`_.

2. Update the Makefile with desired Linux distribution::

    DISTRO=(ubuntu_xenial or ubuntu_bionic or opensuse_15)

3. If necessary, change the PROXY variable to your proxy and change the
USE_PROXY to true in the Makefile.

4. Go to the Spyglass directory in Terminal and run ``make images``. When the
build is done, you will see ``Successfully built <DOCKER_IMAGE>``

5. From your home directory, create a new directory to store the output from
docker with the following command:

.. code-block:: bash

    mkdir -p ~/tmp/spyglass

6. Run Spyglass with the following command. The -v tag is used to mount the
necessary local folders to the docker image . You must use the full path to the
local folders you are mounting to. The path following the ':' is a path inside
the docker container. These folders will be made automatically by docker. (The
directory you are mounting to must be 'mnt' or another directory owned by
airship user in the docker image)

.. code-block:: bash

    docker run -v /path/to/input/files:/mnt/input \
    -v ~/tmp/spyglass:/mnt/output \
    <DOCKER_IMAGE> spyglass excel documents -i \
    -x /mnt/input/<excel_file_name> \
    -e /mnt/input/<excel_spec_name> \
    -c /mnt/input/<site_config_name> \
    -s <site_name> -t /mnt/input/<templates_folder> \
    -d /mnt/output -m /mnt/output

Example
^^^^^^^
The following shows the command used to create the site manifest and
intermediary in the docker container using the example files provided in
Spyglass and the Spyglass Excel Plugin. (``/root/path/`` is the path to
spyglass in your directory)

.. code-block:: bash

    docker run \
    -v /root/path/spyglass/spyglass/examples/:/mnt/examples \
    -v /root/path/spyglass-plugin-xls/spyglass_plugin_xls/examples:/mnt/examples_xls \
    -v ~/tmp/spyglass:/mnt/output \
    <DOCKER_IMAGE> spyglass excel documents -i \
    -x /mnt/examples_xls/SiteDesignSpec_v0.1.xlsx \
    -e /mnt/examples_xls/excel_spec.yaml \
    -c /mnt/examples/site_config.yaml \
    -s airship-seaworthy \
    -t /mnt/examples/templates \
    -d /mnt/output/ \
    -m /mnt/output/

.. _Spyglass: getting_started.html#basic-usage
.. _`Spyglass Excel Plugin`: https://opendev.org/airship/spyglass-plugin-xls/src/branch/master/doc/source/getting_started.rst
.. _`Docker CE`: https://docs.docker.com/install/