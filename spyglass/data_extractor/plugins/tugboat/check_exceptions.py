# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class BaseError(Exception):
    pass


class NotEnoughIp(BaseError):
    def __init__(self, cidr, total_nodes):
        self.cidr = cidr
        self.total_nodes = total_nodes

    def display_error(self):
        print('{} can not handle {} nodes'.format(self.cidr, self.total_nodes))


class NoSpecMatched(BaseError):
    def __init__(self, excel_specs):
        self.specs = excel_specs

    def display_error(self):
        print('No spec matched. Following are the available specs:\n'.format(
            self.specs))
