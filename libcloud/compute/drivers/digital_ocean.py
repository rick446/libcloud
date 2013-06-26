# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Dummy Driver

@note: This driver is out of date
"""
import uuid
import socket
import struct

from libcloud.common.base import ConnectionUserAndKey
from libcloud.common.base import JsonResponse
from libcloud.compute.base import NodeImage, NodeSize, Node
from libcloud.compute.base import NodeDriver, NodeLocation
from libcloud.compute.types import Provider, NodeState, LibcloudError


class DigitalOceanConnection(ConnectionUserAndKey):
    """
    DigitalOcean connection class
    """
    host='api.digitalocean.com'
    port=443
    responseCls = JsonResponse
    def pre_connect_hook(self, params, headers):
        params.setdefault('client_id', self.user_id)
        params.setdefault('api_key', self.key)
        return params, headers


class DigitalOceanNodeDriver(NodeDriver):
    """
    DigitalOcean node driver
    """

    name = "DigitalOcean Node Provider"
    website = 'http://digitalocean.com'
    type = Provider.DIGITAL_OCEAN
    api_base = 'https://api.digitalocean.com/'
    connectionCls = DigitalOceanConnection
    NODE_STATE_MAP = {
        'new': NodeState.PENDING,
        'active': NodeState.RUNNING,
        'shutting-down': NodeState.TERMINATED,
        'terminated': NodeState.TERMINATED
    }
        
    def list_nodes(self):
        elem = self.connection.request('/droplets/').object
        return self._to_nodes(elem['droplets'])

    def list_images(self):
        elem = self.connection.request('/images/').object
        return self._to_images(elem['images'])

    def list_sizes(self):
        elem = self.connection.request('/sizes/').object
        return self._to_sizes(elem['sizes'])

    def list_locations(self):
        elem = self.connection.request('/regions/').object
        return self._to_locations(elem['regions'])

    def ex_list_ssh_keys(self):
        elem = self.connection.request('/ssh_keys/').object
        return elem['ssh_keys']

    def create_node(self, name, size, image, location=None, ex_ssh_key_ids=None):
        if location is None:
            location = NodeLocation(
                id=1, name='New York 1', country=None, driver=self)
        params=dict(
            name=name,
            size_id=size.id,
            image_id=image.id,
            region_id=location.id)
        if ex_ssh_key_ids:
            params['ssh_key_ids'] = ','.join(map(str,ex_ssh_key_ids))
        elem = self.connection.request(
            '/droplets/new',
            params=params).object
        if elem['status'] == 'ERROR':
            raise LibcloudError, elem['error_message']
        n = Node(
            id=elem['droplet']['id'],
            name=elem['droplet']['name'],
            state=NodeState.PENDING,
            public_ips=[],
            private_ips=[],
            driver=self,
            size=size,
            image=image,
            extra=elem['droplet'])
        return n

    def reboot_node(self, node, ex_power_cycle=False):
        node.state = NodeState.REBOOTING
        if ex_power_cycle:
            resp = self.connection.request('/droplets/%s/power_cycle/' % node.id).object
        else:
            resp = self.connection.request('/droplets/%s/reboot/' % node.id).object
        return True

    def destroy_node(self, node):
        node.state = NodeState.TERMINATED
        resp = self.connection.request('/droplets/%s/destroy/' % node.id).object
        return True

    def _to_node(self, element):
        state = self.NODE_STATE_MAP.get(element['status'], NodeState.UNKNOWN)
        return Node(
            id=element['id'],
            name=element['name'],
            state=state,
            public_ips=[element['ip_address']],
            private_ips=[],
            driver=self,
            extra=element)

    def _to_image(self, element):
        return NodeImage(
            id=element['id'], name=element['name'], driver=self, extra=element)

    def _to_size(self, element):
        return NodeSize(
            id=element['id'],
            name=element['name'],
            ram=element['name'],
            disk=None, 
            bandwidth=None,
            price=0.0,
            driver=self)

    def _to_location(self, element):
        return NodeLocation(
            id=element['id'],
            name=element['name'],
            country=None,
            driver=self)

    def _to_nodes(self, elements):
        return map(self._to_node, elements)

    def _to_images(self, elements):
        return map(self._to_image, elements)

    def _to_sizes(self, elements):
        return map(self._to_size, elements)

    def _to_locations(self, elements):
        return map(self._to_location, elements)


