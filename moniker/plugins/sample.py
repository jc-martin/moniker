import logging

from moniker import moniker_plugin_base_v1

LOG = logging.getLogger(__name__)

class FakePlugin(moniker_plugin_base_v1.MonikerPluginBaseV1):
    """"""

    def __init__(self, ):
        """Constructor for """
        super(FakePlugin, self).__init__()

    def create_domain(self, context, domain):
        """"""
        LOG.info("Create Domain called")

        pass

    def get_domains(self, context, filters=None, fields=None):
        """"""
        LOG.info("Index Domains called")

        return []

