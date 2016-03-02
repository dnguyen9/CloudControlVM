#!/usr/bin/env python

# Copyright 2014 PerfKitBenchmarker Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from perfkitbenchmarker.providers.aws import vm_lifecycle_util

def main(argv):

  if len(argv) < 2:
    print("Valid parameters are: pkb [cloudname] [stop, list]")
    return 1

vm_lifecycle_util.ExecuteAction(sys.argv[1],sys.argv[2])

#from perfkitbenchmarker.pkb import Main

if __name__ == "__main__":
    sys.exit(main(sys.argv))