======================
Spyglass Documentation
======================

Overview
--------
Spyglass is a data extraction tool which can interface with
different input data sources to generate site manifest YAML files.
The data sources will provide all the configuration data needed
for a site deployment. These site manifest YAML files generated
by spyglass will be saved in a Git repository, from where Pegleg
can access and aggregate them. This aggregated file can then be
fed to Shipyard for site deployment / updates.

Spyglass follows a plugin model to support multiple input data sources.
The currently supported plugin is the Spyglass Excel plugin
(`spyglass-plugin-xls`_).

The Spyglass Excel plugin accepts an engineering spec in the form of a
spreadsheet and an index file to read the spreadsheet as inputs and
generates site level manifests. As an optional step, it can generate an
intermediary YAML which contains all the information that will be rendered to
generate Airship site manifests. This optional step will help the deployment
engineer modify any data if required.

.. toctree::
   :maxdepth: 2

   getting_started
   developer_quickstart
   cli
   docker_guide

.. _spyglass-plugin-xls: https://opendev.org/airship/spyglass-plugin-xls