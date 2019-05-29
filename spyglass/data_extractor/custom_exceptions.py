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

import logging
import sys

LOG = logging.getLogger(__name__)


class BaseError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def display_error(self):
        LOG.info(self.msg)
        sys.exit(1)


class NoSpecMatched(BaseError):

    def __init__(self, excel_specs):
        self.specs = excel_specs

    def display_error(self):
        # FIXME (Ian Pittwood): use log instead of print
        print(
            "No spec matched. Following are the available specs:\n".format(
                self.specs))
        sys.exit(1)


class MissingAttributeError(BaseError):
    pass


class MissingValueError(BaseError):
    pass


class ApiClientError(BaseError):
    pass


class TokenGenerationError(BaseError):
    pass


class FormationConnectionError(BaseError):
    pass
