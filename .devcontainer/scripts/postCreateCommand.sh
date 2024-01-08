# Copyright (c) 2022-2023 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

sudo chmod +x .devcontainer/scripts/*.sh
sudo chown -R $(whoami) $HOME

echo "#######################################################"
echo "### Executing add-python.sh                         ###"
echo "#######################################################"
.devcontainer/scripts/add-python.sh 2>&1 | tee -a $HOME/add-python.log

pip3 install -r ./requirements.txt
pip3 install -r ./requirements-vss.txt

# add repo to git safe.directory
REPO=$(pwd)
git config --global --add safe.directory $REPO
