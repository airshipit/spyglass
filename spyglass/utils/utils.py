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


# Merge two dictionaries
def dict_merge(dict_a, dict_b, path=None):
    """Recursively Merge dictionary dictB  into dictA

    DictA represents the data extracted by a  plugin and DictB
    represents the additional site config dictionary that is passed
    to CLI. The merge process compares the dictionary keys and if they
    are same and the values they point to are different , then
    dictB object's value is copied to dictA. If a key is unique
    to dictB, then it is copied to dictA.
    """
    if path is None:
        path = []

    for key in dict_b:
        if key in dict_a:
            if isinstance(dict_a[key], dict) and isinstance(dict_b[key], dict):
                dict_merge(dict_a[key], dict_b[key], path + [str(key)])
            elif dict_a[key] == dict_b[key]:
                pass  # values are same, so no processing here
            else:
                dict_a[key] = dict_b[key]
        else:
            dict_a[key] = dict_b[key]
    return dict_a
