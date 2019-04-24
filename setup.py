# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import find_packages
from setuptools import setup

setup(
    name='spyglass',
    version='0.0.1',
    description='Generate Airship specific yaml manifests from data sources',
    url='http://github.com/openstack/airship-spyglass',
    python_requires='>=3.5.0',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=[
        'jsonschema',
        'Click',
        'openpyxl',
        'netaddr',
        'pyyaml',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'spyglass=spyglass.spyglass:main',
        ],
        'data_extractor_plugins': [
            'formation='
            'spyglass.data_extractor.plugins.formation:FormationPlugin',
            'tugboat='
            'spyglass.data_extractor.plugins.tugboat.tugboat:TugboatPlugin',
        ]
    },
    include_package_data=True,
)
