
# Stolen from Quantum API framework

import logging
import urlparse

import routes as routes_mapper
import webob
import webob.dec
import webob.exc
from moniker.api.v2 import attributes
from moniker.api.v2 import base
from moniker import manager
from moniker.openstack.common import wsgi
from moniker.openstack.common import exception
from moniker.openstack.common import cfg

LOG = logging.getLogger(__name__)

COLLECTION_ACTIONS = ['index', 'create']
MEMBER_ACTIONS = ['show', 'update', 'delete']
REQUIREMENTS = {'id': attributes.UUID_PATTERN, 'format': 'xml|json'}

# scaffolding from Quantum.wsgi. Will need to be reformulated. Is there just to make the router work
class Serializer(object):
    """Serializes and deserializes dictionaries to certain MIME types."""

    def __init__(self, metadata=None, default_xmlns=None):
        """Create a serializer based on the given WSGI environment.

        'metadata' is an optional dict mapping MIME types to information
        needed to serialize a dictionary to that type.

        """
        self.metadata = metadata or {}
        self.default_xmlns = default_xmlns

    def _get_serialize_handler(self, content_type):
        handlers = {
            'application/json': wsgi.JSONDictSerializer,
            'application/xml': wsgi.XMLDictSerializer,
            }

        try:
            return handlers[content_type]
        except Exception:
            raise exception.InvalidContentType(content_type=content_type)

    def serialize(self, data, content_type):
        """Serialize a dictionary into the specified content type."""
        return self._get_serialize_handler(content_type)(data)

    def deserialize(self, datastring, content_type):
        """Deserialize a string to a dictionary.

        The string must be in the format of a supported MIME type.

        """
        try:
            return self.get_deserialize_handler(content_type)(datastring)
        except Exception:
            raise webob.exc.HTTPBadRequest("Could not deserialize data")

    def get_deserialize_handler(self, content_type):
        handlers = {
            'application/json': wsgi.JSONDeserializer,
            'application/xml': wsgi.XMLDeserializer,
            }

        try:
            return handlers[content_type]
        except Exception:
            raise exception.InvalidContentType(content_type=content_type)


class Index(object):
    def __init__(self, resources):
        self.resources = resources

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        metadata = {'application/xml': {'attributes': {
            'resource': ['name', 'collection'],
            'link': ['href', 'rel']}}}

        layout = []
        for name, collection in self.resources.iteritems():
            href = urlparse.urljoin(req.path_url, collection)
            resource = {'name': name,
                        'collection': collection,
                        'links': [{'rel': 'self',
                                   'href': href}]}
            layout.append(resource)
        response = dict(resources=layout)
        content_type = req.best_match_content_type()
        body = Serializer(metadata=metadata).serialize(response,
                content_type)

        return webob.Response(body=body, content_type=content_type)


class APIRouter(wsgi.Router):

    @classmethod
    def factory(cls, global_config, **local_config):
        return cls(**local_config)

    def __init__(self, **local_config):
        mapper = routes_mapper.Mapper()
        plugin = manager.MonikerManager.get_plugin()
        #TODO Add back extensions support
#        ext_mgr = extensions.PluginAwareExtensionManager.get_instance()
#        ext_mgr.extend_resources("2.0", attributes.RESOURCE_ATTRIBUTE_MAP)

        col_kwargs = dict(collection_actions=COLLECTION_ACTIONS,
            member_actions=MEMBER_ACTIONS)

        resources = {'domain': 'domains',
                     'record': 'records'}

        def _map_resource(collection, resource, params):
            allow_bulk = cfg.CONF.allow_bulk
            controller = base.create_resource(collection, resource,
                plugin, params,
                allow_bulk=allow_bulk)
            mapper_kwargs = dict(controller=controller,
                requirements=REQUIREMENTS,
                **col_kwargs)
            return mapper.collection(collection, resource,
                **mapper_kwargs)

        mapper.connect('index', '/', controller=Index(resources))
        for resource in resources:
            _map_resource(resources[resource], resource,
                attributes.RESOURCE_ATTRIBUTE_MAP.get(
                    resources[resource], dict()))

        super(APIRouter, self).__init__(mapper)
