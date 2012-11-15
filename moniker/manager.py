
import logging

from moniker.openstack.common import cfg
from moniker.openstack.common import importutils


LOG = logging.getLogger(__name__)


class MonikerManager(object):

    _instance = None

    def __init__(self, options=None, config_file=None):
        # If no options have been provided, create an empty dict
        if not options:
            options = {}

        # NOTE(jkoelker) Testing for the subclass with the __subclasshook__
        #                breaks tach monitoring. It has been removed
        #                intentianally to allow v2 plugins to be monitored
        #                for performance metrics.
        plugin_provider = cfg.CONF.core_plugin
        LOG.debug("Plugin location:%s", plugin_provider)
        # If the plugin can't be found let them know gracefully
        try:
            LOG.info("Loading Plugin: %s" % plugin_provider)
            plugin_klass = importutils.import_class(plugin_provider)
        except ImportError:
            LOG.exception("Error loading plugin")
            raise Exception("Plugin not found.  You can install a "
                            "plugin with: pip install <plugin-name>\n"
                            "Example: pip install quantum-sample-plugin")
        self.plugin = plugin_klass()

    @classmethod
    def get_plugin(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance.plugin
