# Copyright (c) 2022 Robert Bosch GmbH and Microsoft Corporation
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

FROM ubuntu:20.04

ENV DOCKER_BUILDKIT=1

# Fix for bug in devcontainer features
ADD https://raw.githubusercontent.com/devcontainers/features/7fa90110d762797cc0b1c2fe8fcc028c9b813d56/src/common-utils/install.sh /tmp/scripts/install-common.sh
RUN UID="4000" bash /tmp/scripts/install-common.sh

COPY scripts/*.sh /tmp/scripts/
RUN find /tmp/scripts/ -type f -iname "*.sh" -exec chmod +x {} \;
RUN /bin/bash /tmp/scripts/configure-proxies.sh
