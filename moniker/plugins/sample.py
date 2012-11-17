import logging

from moniker.storage import moniker_plugin_storage_v1

LOG = logging.getLogger(__name__)

class FakePlugin(moniker_plugin_storage_v1.MonikerPluginStorageV1):
    """"""

    def __init__(self):
        """Constructor for """
        super(FakePlugin, self).__init__()

    def create_domain(self, context, domain):
        """"""
        LOG.debug("Create Domain called")

        # record the creation in the DB first
        try:
            mdb = super(FakePlugin, self).create_domain(context,domain)
        except Exception as e:
            raise e

        # do something useful with mdb, for example calling a DNS server
        LOG.debug("Create Domain done : %s"% mdb)

        return mdb

    def delete_domain(self, context, id):
        """
        """
        LOG.info("Delete Domain called")

        # delete from the DNS server first ?

        # then delete from the DB
        try:
            mdb = super(FakePlugin, self).delete_domain(context,id)
        except Exception as e:
            raise e

        LOG.info("Delete Domain done")


    def get_domains(self, context, filters=None, fields=None):
        """"""
        LOG.info("Index Domains called")

        # Get the records from the DB first
        try:
            mdb = super(FakePlugin,self).get_domains(context, filters=None, fields=None)
        except Exception as e:
            raise e

        # then maybe check that they are actually in the remote servers.

        return mdb

