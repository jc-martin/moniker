# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# merge of the code from original API to a plugin model

from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker.openstack.common.rpc.proxy import RpcProxy
from moniker import moniker_plugin_base_v1

DEFAULT_VERSION = '1.0'

LOG = logging.getLogger(__name__)
RPC = RpcProxy(cfg.CONF.central_topic, DEFAULT_VERSION)

class RpcPlugin(moniker_plugin_base_v1.MonikerPluginBaseV1):
    """RPC based plugin"""

    def __init__(self):
        """Constructor for RpcPlugin"""
        super(RpcPlugin, self).__init__()



    def create_server(self, context, server):
        #TODO map server to values
        msg = {
            'method': 'create_server',
            'args': {
                'values': server,
                },
            }

        return RPC.call(context, msg)


    def get_servers(self, context, filters=None, fields=None):
        #TODO map fields/filters to criterion
        criterion = None
        msg = {
            'method': 'get_servers',
            'args': {
                'criterion': criterion,
                },
            }

        return RPC.call(context, msg)


    def get_server(self, context, id):
        msg = {
            'method': 'get_server',
            'args': {
                'server_id': id,
                },
            }

        return RPC.call(context, msg)


    def update_server(self, context, id, server):
        #TODO map server to values
        values = []
        msg = {
            'method': 'update_server',
            'args': {
                'server_id': id,
                'values': values,
                },
            }

        return RPC.call(context, msg)


    def delete_server(self, context, id):
        msg = {
            'method': 'delete_server',
            'args': {
                'server_id': id,
                },
            }

        return RPC.call(context, msg)


    # Domain Methods
    def create_domain(self, context, domain):
    #TODO map domain to values
        msg = {
            'method': 'create_domain',
            'args': {
                'values': domain,
                },
            }

        return RPC.call(context, msg)


    def get_domains(self, context, filters=None, fields=None):
        #TODO map fields/filters to criterion
        criterion = None
        msg = {
            'method': 'get_domains',
            'args': {
                'criterion': criterion,
                },
            }

        return RPC.call(context, msg)


    def get_domain(self, context, id, fields=None):
        msg = {
            'method': 'get_domain',
            'args': {
                'domain_id': id,
                },
            }

        return RPC.call(context, msg)


    def update_domain(self, context, id, domain):
        #TODO map domain to values
        values = []
        msg = {
            'method': 'update_domain',
            'args': {
                'domain_id': id,
                'values': values,
                },
            }

        return RPC.call(context, msg)


    def delete_domain(self, context, id):
        msg = {
            'method': 'delete_domain',
            'args': {
                'domain_id': id,
                },
            }

        return RPC.call(context, msg)


    # Record Methods
    def create_record(self, context, record):
        #TODO map record to domain id and values
        msg = {
            'method': 'create_record',
            'args': {
                'domain_id': domain_id,
                'values': values,
                },
            }

        return RPC.call(context, msg)


    def get_records(self, context, filters=None, fields=None):
        #TODO map filters to domain_id and criterion
        criterion = None
        domain_id = None
        msg = {
            'method': 'get_records',
            'args': {
                'domain_id': domain_id,
                'criterion': criterion,
                },
            }

        return RPC.call(context, msg)


    def get_record(self, context, id, fields=None):
        #TODO domain_id is not required if ID is unique
        domain_id = None
        msg = {
            'method': 'get_record',
            'args': {
                'domain_id': domain_id,
                'record_id': id,
                },
            }

        return RPC.call(context, msg)


    def update_record(self, context, id, record):
        #TODO domain_id is not required if ID is unique
        #TODO map the values
        values = None
        msg = {
            'method': 'update_record',
            'args': {
                'domain_id': None,
                'record_id': id,
                'values': values,
                },
            }

        return RPC.call(context, msg)


    def delete_record(self, context, id):
        #TODO domain_id is not required if ID is unique
        msg = {
            'method': 'delete_record',
            'args': {
                'domain_id': None,
                'record_id': id,
                },
            }

        return RPC.call(context, msg)
