# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
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

import logging
import os
from tempfile import mkdtemp

from jinja2 import UndefinedError
import pytest

from spyglass.site_processors.site_processor import SiteProcessor

LOG = logging.getLogger(__name__)
LOG.level = logging.DEBUG

J2_TPL = """---
schema: pegleg/SiteDefinition/v1
metadata:
  schema: metadata/Document/v1
  layeringDefinition:
    abstract: false
    layer: site
  name: {{ data['region_name'] }}
  storagePolicy: cleartext
data:
  site_type:{{ data['site_info']['sitetype'] }}
..."""


def test_render_template():
    _tpl_parent_dir = mkdtemp()
    _tpl_dir = mkdtemp(dir=_tpl_parent_dir)
    _tpl_file = os.path.join(_tpl_dir, "test.yaml.j2")
    with open(_tpl_file, 'w') as f:
        f.write(J2_TPL)
        LOG.debug("Writing test template to %s", _tpl_file)
    _input_yaml = {
        "region_name": "test",
        "site_info": {
            "sitetype": "test_type"
        }
    }
    _out_dir = mkdtemp()
    site_processor = SiteProcessor(_input_yaml, _out_dir, force_write=False)
    site_processor.render_template(_tpl_parent_dir)

    expected_output = """---
schema: pegleg/SiteDefinition/v1
metadata:
  schema: metadata/Document/v1
  layeringDefinition:
    abstract: false
    layer: site
  name: test
  storagePolicy: cleartext
data:
  site_type:test_type
..."""

    output_file = os.path.join(
        _out_dir, "pegleg_manifests", "site", _input_yaml["region_name"],
        os.path.split(_tpl_dir)[1], "test.yaml")
    LOG.debug(output_file)
    assert (os.path.exists(output_file))
    with open(output_file, 'r') as f:
        content = f.read()
        assert (expected_output == content)


def test_render_template_missing_data():
    _tpl_parent_dir = mkdtemp()
    _tpl_dir = mkdtemp(dir=_tpl_parent_dir)
    _tpl_file = os.path.join(_tpl_dir, "test.yaml.j2")
    with open(_tpl_file, 'w') as f:
        f.write(J2_TPL)
        LOG.debug("Writing test template to %s", _tpl_file)
    _input_yaml = {"region_name": "test", "site_info": {}}
    _out_dir = mkdtemp()
    site_processor = SiteProcessor(_input_yaml, _out_dir, force_write=False)
    with pytest.raises(UndefinedError):
        site_processor.render_template(_tpl_parent_dir)

    output_file = os.path.join(
        _out_dir, "pegleg_manifests", "site", _input_yaml["region_name"],
        os.path.split(_tpl_dir)[1], "test.yaml")
    assert (not os.path.exists(output_file))


def test_render_template_missing_data_force():
    _tpl_parent_dir = mkdtemp()
    _tpl_dir = mkdtemp(dir=_tpl_parent_dir)
    _tpl_file = os.path.join(_tpl_dir, "test.yaml.j2")
    with open(_tpl_file, 'w') as f:
        f.write(J2_TPL)
        LOG.debug("Writing test template to %s", _tpl_file)
    _input_yaml = {"region_name": "test", "site_info": {}}
    _out_dir = mkdtemp()
    site_processor = SiteProcessor(_input_yaml, _out_dir, force_write=True)
    site_processor.render_template(_tpl_parent_dir)

    expected_output = """---
schema: pegleg/SiteDefinition/v1
metadata:
  schema: metadata/Document/v1
  layeringDefinition:
    abstract: false
    layer: site
  name: test
  storagePolicy: cleartext
data:
  site_type:
..."""

    output_file = os.path.join(
        _out_dir, "pegleg_manifests", "site", _input_yaml["region_name"],
        os.path.split(_tpl_dir)[1], "test.yaml")
    assert (os.path.exists(output_file))
    with open(output_file, 'r') as f:
        content = f.read()
        assert (expected_output == content)
