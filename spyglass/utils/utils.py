# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Merge two dictionaries
def dict_merge(dictA, dictB, path=None):
    """ Recursively  Merge dictionary dictB  into dictA


    DictA represents the data extracted by a  plugin and DictB
    represents the additional site config dictionary that is passed
    to CLI. The merge process compares the dictionary keys and if they
    are same and the values they point to are different , then
    dictB object's value is copied to dictA. If a key is unique
    to dictB, then it is copied to dictA.
    """
    if path is None:
        path = []

    for key in dictB:
        if key in dictA:
            if isinstance(dictA[key], dict) and isinstance(dictB[key], dict):
                dict_merge(dictA[key], dictB[key], path + [str(key)])
            elif dictA[key] == dictB[key]:
                pass  # values are same, so no processing here
            else:
                dictA[key] = dictB[key]
        else:
            dictA[key] = dictB[key]
    return dictA
