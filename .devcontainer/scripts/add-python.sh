#!/bin/bash
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

echo "#######################################################"
echo "### Installing OS updates                           ###"
echo "#######################################################"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y wget ca-certificates

echo "#######################################################"
echo "### Installing python version 3                     ###"
echo "#######################################################"
PYTHON_VERSION=3.9
sudo apt-get install -y python3-distutils
sudo apt-get install -y python$PYTHON_VERSION
curl -fsSL https://bootstrap.pypa.io/get-pip.py | sudo python$PYTHON_VERSION

sudo update-alternatives --install /usr/bin/python python /usr/bin/python$PYTHON_VERSION 10
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python$PYTHON_VERSION 10
