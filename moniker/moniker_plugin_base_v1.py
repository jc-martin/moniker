from abc import ABCMeta, abstractmethod


class MonikerPluginBaseV1(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def create_domain(self, context, domain):
        pass

    @abstractmethod
    def get_domain(self, context, id, fields=None):
        pass

    @abstractmethod
    def update_domain(self, context, id, domain):
        pass

    @abstractmethod
    def delete_domain(self, context, id):
        pass

    @abstractmethod
    def get_domains(self, context, filters=None, fields=None):
        pass


    @abstractmethod
    def create_record(self, context, record):
        pass

    @abstractmethod
    def get_record(self, context, id, fields=None):
        pass

    @abstractmethod
    def update_record(self, context, id, domain):
        pass

    @abstractmethod
    def delete_record(self, context, id):
        pass

    @abstractmethod
    def get_records(self, context, filters=None, fields=None):
        pass

