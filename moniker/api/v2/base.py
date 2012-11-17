# Stolen from Quantum API framework


import logging
import socket

import webob.exc

from moniker.api.v2 import attributes
from moniker.api.v2 import resource as wsgi_resource
from moniker.openstack.common import exception
from moniker.openstack.common import cfg
from moniker.openstack.common.gettextutils import _
from moniker.openstack.common.notifier import api as notifier_api

LOG = logging.getLogger(__name__)
XML_NS_V20 = 'http://openstack.org/moniker/api/v2.0'


def _get_hostname():
    return socket.gethostname()


# Register the configuration options
#cfg.CONF.register_opt(cfg.StrOpt('host', default=_get_hostname()))


def _fields(request):
    """
    Extracts the list of fields to return
    """
    return [v for v in request.GET.getall('fields') if v]


def _filters(request, attr_info):
    """
    Extracts the filters from the request string

    Returns a dict of lists for the filters:

    check=a&check=b&name=Bob&

    becomes

    {'check': [u'a', u'b'], 'name': [u'Bob']}
    """
    res = {}
    for key in set(request.GET):
        if key == 'fields':
            continue
        values = [v for v in request.GET.getall(key) if v]
        key_attr_info = attr_info.get(key, {})
        if not key_attr_info and values:
            res[key] = values
            continue
        convert_list_to = key_attr_info.get('convert_list_to')
        if not convert_list_to:
            convert_to = key_attr_info.get('convert_to')
            if convert_to:
                convert_list_to = lambda values_: [convert_to(x)
                                                   for x in values_]
        if convert_list_to:
            try:
                result_values = convert_list_to(values)
            except exception.BadInputError as e:
                raise webob.exc.HTTPBadRequest(str(e))
        else:
            result_values = values
        if result_values:
            res[key] = result_values
    return res


class Controller(object):

    def __init__(self, plugin, collection, resource, attr_info,
                 allow_bulk=False, member_actions=None):
        if member_actions is None:
            member_actions = []
        self._plugin = plugin
        self._collection = collection
        self._resource = resource
        self._attr_info = attr_info
        self._allow_bulk = allow_bulk
        self._native_bulk = self._is_native_bulk_supported()
        self._policy_attrs = [name for (name, info) in self._attr_info.items()
                              if info.get('required_by_policy')]
        self._publisher_id = notifier_api.publisher_id('network')
        self._member_actions = member_actions

    def _is_native_bulk_supported(self):
        native_bulk_attr_name = ("_%s__native_bulk_support"
                                 % self._plugin.__class__.__name__)
        return getattr(self._plugin, native_bulk_attr_name, False)

    def _is_visible(self, attr):
        attr_val = self._attr_info.get(attr)
        return attr_val and attr_val['is_visible']

    def _view(self, data, fields_to_strip=None):
        # make sure fields_to_strip is iterable
        if not fields_to_strip:
            fields_to_strip = []

        return dict(item for item in data.iteritems()
            if self._is_visible(item[0])
        and not item[0] in fields_to_strip)

    def _do_field_list(self, original_fields):
        fields_to_add = None
        # don't do anything if fields were not specified in the request
        if original_fields:
            fields_to_add = [attr for attr in self._policy_attrs
                             if attr not in original_fields]
            original_fields.extend(self._policy_attrs)
        return original_fields, fields_to_add

    def __getattr__(self, name):
        if name in self._member_actions:
            def _handle_action(request, id, body=None):
                return getattr(self._plugin, name)(request.context, id, body)
            return _handle_action
        else:
            raise AttributeError

    def _items(self, request, do_authz=False):
        """Retrieves and formats a list of elements of the requested entity"""
        # NOTE(salvatore-orlando): The following ensures that fields which
        # are needed for authZ policy validation are not stripped away by the
        # plugin before returning.
        original_fields, fields_to_add = self._do_field_list(_fields(request))
        kwargs = {'filters': _filters(request, self._attr_info),
                  'fields': original_fields}
        obj_getter = getattr(self._plugin, "get_%s" % self._collection)
        obj_list = obj_getter(request.context, **kwargs)
        return {self._collection: [self._view(obj,
            fields_to_strip=fields_to_add)
                                   for obj in obj_list]}

    def _item(self, request, id, do_authz=False, field_list=None):
        """Retrieves and formats a single element of the requested entity"""
        kwargs = {'fields': field_list}
        action = "get_%s" % self._resource
        obj_getter = getattr(self._plugin, action)
        obj = obj_getter(request.context, id, **kwargs)
        return obj

    def index(self, request):
        """Returns a list of the requested entity"""
        return self._items(request, True)

    def show(self, request, id):
        """Returns detailed information about the requested entity"""

        field_list, added_fields = self._do_field_list(_fields(request))
        return {self._resource:
                    self._view(self._item(request,
                        id,
                        do_authz=True,
                        field_list=field_list),
                        fields_to_strip=added_fields)}

    def _emulate_bulk_create(self, obj_creator, request, body):
        objs = []
        try:
            for item in body[self._collection]:
                kwargs = {self._resource: item}
                objs.append(self._view(obj_creator(request.context,
                    **kwargs)))
            return objs
        # Note(salvatore-orlando): broad catch as in theory a plugin
        # could raise any kind of exception
        except Exception as ex:
            for obj in objs:
                delete_action = "delete_%s" % self._resource
                obj_deleter = getattr(self._plugin, delete_action)
                try:
                    obj_deleter(request.context, obj['id'])
                except Exception:
                    # broad catch as our only purpose is to log the exception
                    LOG.exception("Unable to undo add for %s %s",
                        self._resource, obj['id'])
                # TODO(salvatore-orlando): The object being processed when the
            # plugin raised might have been created or not in the db.
            # We need a way for ensuring that if it has been created,
            # it is then deleted
            raise

    def create(self, request, body=None):
        """Creates a new instance of the requested entity"""
        notifier_api.notify(request.context,
            self._publisher_id,
            self._resource + '.create.start',
            notifier_api.INFO,
            body)
        body = Controller.prepare_request_body(request.context, body, True,
            self._resource, self._attr_info,
            allow_bulk=self._allow_bulk)
        action = "create_%s" % self._resource

        def notify(create_result):
            notifier_api.notify(request.context,
                self._publisher_id,
                self._resource + '.create.end',
                notifier_api.INFO,
                create_result)
            return create_result

        if self._collection in body and self._native_bulk:
            # plugin does atomic bulk create operations
            obj_creator = getattr(self._plugin, "%s_bulk" % action)
            objs = obj_creator(request.context, body)
            return notify({self._collection: [self._view(obj)
                                              for obj in objs]})
        else:
            obj_creator = getattr(self._plugin, action)
            if self._collection in body:
                # Emulate atomic bulk behavior
                objs = self._emulate_bulk_create(obj_creator, request, body)
                return notify({self._collection: objs})
            else:
                kwargs = {self._resource: body}
                obj = obj_creator(request.context, **kwargs)
                return notify({self._resource: self._view(obj)})

    def delete(self, request, id):
        """Deletes the specified entity"""
        notifier_api.notify(request.context,
            self._publisher_id,
            self._resource + '.delete.start',
            notifier_api.INFO,
            {self._resource + '_id': id})
        action = "delete_%s" % self._resource


        obj_deleter = getattr(self._plugin, action)
        obj_deleter(request.context, id)
        notifier_api.notify(request.context,
            self._publisher_id,
            self._resource + '.delete.end',
            notifier_api.INFO,
            {self._resource + '_id': id})

    def update(self, request, id, body=None):
        """Updates the specified entity's attributes"""
        payload = body.copy()
        payload['id'] = id
        notifier_api.notify(request.context,
            self._publisher_id,
            self._resource + '.update.start',
            notifier_api.INFO,
            payload)
        body = Controller.prepare_request_body(request.context, body, False,
            self._resource, self._attr_info,
            allow_bulk=self._allow_bulk)
        action = "update_%s" % self._resource
        # Load object to check authz
        # but pass only attributes in the original body and required
        # by the policy engine to the policy 'brain'
        field_list = [name for (name, value) in self._attr_info.iteritems()
                      if ('required_by_policy' in value and
                          value['required_by_policy'] or
                          not 'default' in value)]
        orig_obj = self._item(request, id, field_list=field_list)
        orig_obj.update(body[self._resource])
        try:
            policy.enforce(request.context,
                action,
                orig_obj,
                plugin=self._plugin)
        except exceptions.PolicyNotAuthorized:
            # To avoid giving away information, pretend that it
            # doesn't exist
            raise webob.exc.HTTPNotFound()

        obj_updater = getattr(self._plugin, action)
        kwargs = {self._resource: body}
        obj = obj_updater(request.context, id, **kwargs)
        result = {self._resource: self._view(obj)}
        notifier_api.notify(request.context,
            self._publisher_id,
            self._resource + '.update.end',
            notifier_api.INFO,
            result)
        return result

    @staticmethod
    def _populate_tenant_id(context, res_dict, is_create):

        LOG.debug("res_dict: %s", res_dict)
        if (('tenant_id' in res_dict and
             res_dict['tenant_id'] != context.tenant and
             not context.is_admin)):
            msg = _("Specifying 'tenant' other than authenticated "
                    "tenant in request requires admin privileges")
            raise webob.exc.HTTPBadRequest(msg)

        if is_create and 'tenant_id' not in res_dict:
            if context.tenant:
                res_dict['tenant_id'] = context.tenant
            else:
                msg = _("Running without keystyone AuthN requires "
                        " that tenant is specified")
                raise webob.exc.HTTPBadRequest(msg)

    @staticmethod
    def prepare_request_body(context, body, is_create, resource, attr_info,
                             allow_bulk=False):
        """ verifies required attributes are in request body, and that
            an attribute is only specified if it is allowed for the given
            operation (create/update).
            Attribute with default values are considered to be
            optional.

            body argument must be the deserialized body
        """
        collection = resource + "s"
        if not body:
            raise webob.exc.HTTPBadRequest(_("Resource body required"))

        body = body or {resource: {}}
        if collection in body and allow_bulk:
            bulk_body = [Controller.prepare_request_body(
                context, {resource: b}, is_create, resource, attr_info,
                allow_bulk) if resource not in b
                         else Controller.prepare_request_body(
                context, b, is_create, resource, attr_info, allow_bulk)
                         for b in body[collection]]

            if not bulk_body:
                raise webob.exc.HTTPBadRequest(_("Resources required"))

            return {collection: bulk_body}

        elif collection in body and not allow_bulk:
            raise webob.exc.HTTPBadRequest("Bulk operation not supported")

        res_dict = body.get(resource)
        if res_dict is None:
            msg = _("Unable to find '%s' in request body") % resource
            raise webob.exc.HTTPBadRequest(msg)

        Controller._populate_tenant_id(context, res_dict, is_create)

        if is_create:  # POST
            for attr, attr_vals in attr_info.iteritems():
                is_required = ('default' not in attr_vals and
                               attr_vals['allow_post'])
                if is_required and attr not in res_dict:
                    msg = _("Failed to parse request. Required "
                            " attribute '%s' not specified") % attr
                    raise webob.exc.HTTPBadRequest(msg)

                if not attr_vals['allow_post'] and attr in res_dict:
                    msg = _("Attribute '%s' not allowed in POST" % attr)
                    raise webob.exc.HTTPBadRequest(msg)

                if attr_vals['allow_post']:
                    res_dict[attr] = res_dict.get(attr,
                        attr_vals.get('default'))
        else:  # PUT
            for attr, attr_vals in attr_info.iteritems():
                if attr in res_dict and not attr_vals['allow_put']:
                    msg = _("Cannot update read-only attribute %s") % attr
                    raise webob.exc.HTTPBadRequest(msg)

        for attr, attr_vals in attr_info.iteritems():
            # Convert values if necessary
            if ('convert_to' in attr_vals and
                attr in res_dict and
                res_dict[attr] != attributes.ATTR_NOT_SPECIFIED):
                res_dict[attr] = attr_vals['convert_to'](res_dict[attr])

            # Check that configured values are correct
            if not ('validate' in attr_vals and
                    attr in res_dict and
                    res_dict[attr] != attributes.ATTR_NOT_SPECIFIED):
                continue
            for rule in attr_vals['validate']:
                res = attributes.validators[rule](res_dict[attr],
                    attr_vals['validate'][rule])
                if res:
                    msg_dict = dict(attr=attr, reason=res)
                    msg = _("Invalid input for %(attr)s. "
                            "Reason: %(reason)s.") % msg_dict
                    raise webob.exc.HTTPBadRequest(msg)
        return body

def create_resource(collection, resource, plugin, params, allow_bulk=False,
                    member_actions=None):
    controller = Controller(plugin, collection, resource, params, allow_bulk,
        member_actions=member_actions)

    # NOTE(jkoelker) To anyone wishing to add "proper" xml support
    #                this is where you do it
    serializers = {}
    #    'application/xml': wsgi.XMLDictSerializer(metadata, XML_NS_V20),

    deserializers = {}
    #    'application/xml': wsgi.XMLDeserializer(metadata),

    return wsgi_resource.Resource(controller, {}, deserializers,
        serializers)
