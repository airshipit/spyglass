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
import textwrap
import unittest
from unittest import mock

from jinja2 import UndefinedError
import pytest

from spyglass.data_extractor import models
from spyglass.site_processors.site_processor import SiteProcessor

LOG = logging.getLogger(__name__)
LOG.level = logging.DEBUG


class TestSiteProcessor(unittest.TestCase):

    J2_TPL = textwrap.dedent(
        """
    ---
    schema: pegleg/SiteDefinition/v1
    metadata:
      schema: metadata/Document/v1
      layeringDefinition:
        abstract: false
        layer: site
      name: {{ data.site_info.region_name }}
      storagePolicy: cleartext
    data:
      site_type:{{ data.site_info.sitetype }}
    ...""")

    J2_TPL_UNDEFINED = textwrap.dedent(
        """
    ---
    schema: pegleg/SiteDefinition/v1
    metadata:
      schema: metadata/Document/v1
      layeringDefinition:
        abstract: false
        layer: site
      name: {{ data.site_info.region_name }}
      storagePolicy: cleartext
    data:
      site_type:{{ undefined_param }}
    ...""")

    @mock.patch(
        'spyglass.data_extractor.models.SiteDocumentData',
        spec=models.SiteDocumentData)
    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.ServerList')
    def test_render_template(self, ServerList, SiteInfo, SiteDocumentData):
        _tpl_parent_dir = mkdtemp()
        _tpl_dir = mkdtemp(dir=_tpl_parent_dir)
        _tpl_file = os.path.join(_tpl_dir, "test.yaml.j2")
        with open(_tpl_file, 'w') as f:
            f.write(self.J2_TPL)
            LOG.debug("Writing test template to %s", _tpl_file)

        site_data = SiteDocumentData()
        type(SiteDocumentData()).site_info = SiteInfo()
        region_name = 'test'
        type(SiteInfo()).region_name = mock.PropertyMock(
            return_value=region_name)
        site_type = 'test_type'
        type(SiteInfo()).sitetype = mock.PropertyMock(return_value=site_type)

        _out_dir = mkdtemp()
        site_processor = SiteProcessor(site_data, _out_dir, force_write=False)
        site_processor.render_template(_tpl_parent_dir)

        expected_output = textwrap.dedent(
            """
        ---
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
        ...""")

        output_file = os.path.join(
            _out_dir, "pegleg_manifests", "site", region_name,
            os.path.split(_tpl_dir)[1], "test.yaml")
        LOG.debug(output_file)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertEqual(expected_output, content)

    @mock.patch(
        'spyglass.data_extractor.models.SiteDocumentData',
        spec=models.SiteDocumentData)
    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.ServerList')
    def test_render_template_missing_data(
            self, ServerList, SiteInfo, SiteDocumentData):
        _tpl_parent_dir = mkdtemp()
        _tpl_dir = mkdtemp(dir=_tpl_parent_dir)
        _tpl_file = os.path.join(_tpl_dir, "test.yaml.j2")
        with open(_tpl_file, 'w') as f:
            f.write(self.J2_TPL_UNDEFINED)
            LOG.debug("Writing test template to %s", _tpl_file)

        site_data = SiteDocumentData()
        type(SiteDocumentData()).site_info = SiteInfo()
        region_name = 'test'
        type(SiteInfo()).region_name = mock.PropertyMock(
            return_value=region_name)
        site_type = 'test_type'
        type(SiteInfo()).sitetype = mock.PropertyMock(return_value=site_type)

        _out_dir = mkdtemp()
        site_processor = SiteProcessor(site_data, _out_dir, force_write=False)
        with pytest.raises(UndefinedError):
            site_processor.render_template(_tpl_parent_dir)

        output_file = os.path.join(
            _out_dir, "pegleg_manifests", "site", region_name,
            os.path.split(_tpl_dir)[1], "test.yaml")
        self.assertFalse(os.path.exists(output_file))

    @mock.patch(
        'spyglass.data_extractor.models.SiteDocumentData',
        spec=models.SiteDocumentData)
    @mock.patch('spyglass.data_extractor.models.SiteInfo')
    @mock.patch('spyglass.data_extractor.models.ServerList')
    def test_render_template_missing_data_force(
            self, ServerList, SiteInfo, SiteDocumentData):
        _tpl_parent_dir = mkdtemp()
        _tpl_dir = mkdtemp(dir=_tpl_parent_dir)
        _tpl_file = os.path.join(_tpl_dir, "test.yaml.j2")
        with open(_tpl_file, 'w') as f:
            f.write(self.J2_TPL_UNDEFINED)
            LOG.debug("Writing test template to %s", _tpl_file)

        site_data = SiteDocumentData()
        type(SiteDocumentData()).site_info = SiteInfo()
        region_name = 'test'
        type(SiteInfo()).region_name = mock.PropertyMock(
            return_value=region_name)
        site_type = 'test_type'
        type(SiteInfo()).sitetype = mock.PropertyMock(return_value=site_type)

        _out_dir = mkdtemp()
        site_processor = SiteProcessor(site_data, _out_dir, force_write=True)
        site_processor.render_template(_tpl_parent_dir)

        expected_output = textwrap.dedent(
            """
        ---
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
        ...""")

        output_file = os.path.join(
            _out_dir, "pegleg_manifests", "site", region_name,
            os.path.split(_tpl_dir)[1], "test.yaml")
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertEqual(expected_output, content)
