#****************************************************************************
#* __ext__.py
#*
#* Copyright 2023-2025 Matthew Ballance and Contributors
#*
#* Licensed under the Apache License, Version 2.0 (the "License"); you may
#* not use this file except in compliance with the License.
#* You may obtain a copy of the License at:
#*
#*   http://www.apache.org/licenses/LICENSE-2.0
#*
#* Unless required by applicable law or agreed to in writing, software
#* distributed under the License is distributed on an "AS IS" BASIS,
#* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#* See the License for the specific language governing permissions and
#* limitations under the License.
#*
#****************************************************************************
import os

def dvfm_packages():
    # The directory layout mirrors the package names, so the file a reader
    # wants is where its dotted name says it is.
    pkg_dir = os.path.dirname(os.path.abspath(__file__))

    return {
        'project.dv':            os.path.join(pkg_dir, "dv", "flow.yaml"),
        'project.dv.uvm':        os.path.join(pkg_dir, "dv", "uvm", "flow.yaml"),
        'project.dv.uvm.utils':  os.path.join(pkg_dir, "dv", "uvm", "utils", "flow.yaml"),
    }
