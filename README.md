
What is Spyglass?
----------------

Spyglass is the data extractor tool which can interface with
different input data sources to generate site manifest YAML files.
The data sources will provide all the configuration data needed
for a site deployment. These site manifest YAML files generated
by spyglass will be saved in a Git repository, from where Pegleg
can access and aggregate them. This aggregated file can then be
fed to shipyard for site deployment / updates.

Spyglass follows plugin model to support multiple input data sources.
Current supported plugins are formation-plugin and Tugboat. Formation
is a rest API based service which will be the source of information
related to hardware, networking, site data. Formation plugin will
interact with Formation API to gather necessary configuration.
Similarly Tugboat accepts engineering spec which is in the form of
spreadsheet and an index file to read spreadsheet as inputs and
generates the site level manifests.
As an optional step it can generate an intermediary yaml which contain
all the information that will be rendered to generate Airship site
manifests. This optional step will help the deployment engineer to
modify any data if required.

Getting Started
---------------
For more detailed installation and setup information, please refer to the
`Getting Started`_ guide.


.. _`Getting Started`: ./doc/source/getting_started.rst
