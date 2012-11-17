from moniker import storage
from moniker import moniker_plugin_base_v1
from moniker.openstack.common import cfg
from moniker.openstack.common import log as logging
from moniker import utils

LOG = logging.getLogger(__name__)


class MonikerPluginStorageV1(moniker_plugin_base_v1.MonikerPluginBaseV1):
    """Base Moniker plugin with DB Persistence"""

    def __init__(self):
        """Constructor for MonikerPluginStorageV1"""

        # Get a storage connection
        self.storage_conn = storage.get_connection(cfg.CONF)
        storage.setup_schema()

    def create_domain(self, context, domain):
        """
        Create a domain
        :param context:
        :param domain:
        :return:
        """
        LOG.info("Create Domain called")
        LOG.debug("Domain %s"% domain['domain'])
        # TODO convert the values in domain to what the storage API needs

        res = self.storage_conn.create_domain(context, domain['domain'])

        # TODO Should notification go out now ?
        utils.notify(context, 'moniker', 'domain.create', res)

        return res

    def get_domain(self, context, id, fields=None):
        pass

    def update_domain(self, context, id, domain):
        pass

    def delete_domain(self, context, id):
        """
        Delete a domain
        :param context:
        :param id:
        :return:
        """
        LOG.info("Delete Domain called")

        domain = self.storage_conn.get_domain(context, id)

        # TODO Should notification go out now ?
        utils.notify(context, 'moniker', 'domain.delete', domain)

        # TODO I don't know what exactly is returned or should be returned
        return self.storage_conn.delete_domain(context, id)

    def get_domains(self, context, filters=None, fields=None):
        """
        Get list of domains
        :param context:
        :param filters:
        :param fields:
        :return:
        """
        LOG.info("Get Domains called")

        # TODO map fields/filters to what the API needs
        criterion = None
        return self.storage_conn.get_domains(context, criterion)


    def create_record(self, context, record):
        pass

    def get_record(self, context, id, fields=None):
        pass

    def get_records(self, context, filters=None, fields=None):
        pass

    def delete_record(self, context, id):
        pass

    def update_record(self, context, id, domain):
        pass