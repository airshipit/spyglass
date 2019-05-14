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


class PathDoesNotExistError(OSError):
    """Exception that occurs when the document or schema path does not exist"""
    pass


class UnexpectedFileType(OSError):
    """Exception that occurs when an unexpected file type is given"""
    pass


class DirectoryEmptyError(OSError):
    """Exception for when a directory is empty

    This exception can occur when either a directory is empty or if a directory
    does not have any files with the correct file extension.
    """
    pass
