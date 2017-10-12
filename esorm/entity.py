import time

from esorm.base import Base
from esorm.exception import *
from esorm import versioning
from esorm.util import elasticsearch_query_builder_util
from esorm.dao import elasticsearch_dao
from esorm.config import elasticsearch_config


class StructuredEntity(Base):
    data_type = Base

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        argument_list = [k for k, v in kwargs.items()]
        class_property_list = [k for k, v in vars(self.__class__).items() if isinstance(v, Base)]
        extra_args = list(set(argument_list) - set(class_property_list))
        for arg in extra_args:
            raise InvalidArgumentError(arg, self.__class__)

        self.value_dict = {}

        for key, value in kwargs.items():
            # target_obj = self.__class__.__dict__[key]
            self.value_dict[key] = value

            #
            # if isinstance(target_obj, BaseProperty):
            #     # if isinstance(value, list):
            #     #     value = [d.get_value_as_json() for d in value]
            #     if not isinstance(value, target_obj.data_type):
            #         raise TypeError(
            #             "Attribute \"{}\" has invalid type. Expected {}, got {}".format(key, target_obj.data_type,
            #                                                                             type(value)))
            #     self.set_value(key, value)
            # elif isinstance(target_obj, Entity):
            #     if not isinstance(value, target_obj.__class__):
            #         raise TypeError('Attribute \"{}\" has invalid type. Expected {}, got {}'.format(key,
            #                                                                                         target_obj.__class__,
            #                                                                                         type(value)))
            #     self.value_dict[key] = value.get_value_as_json()
        pass

    def __str__(self):
        return '<class {}: {}'.format(self.__class__.__name__, repr(self.value_dict))

    def _validate_allowed_values(self, value=None, **kwargs):
        if value is None:
            value = {}
        for k, v in value.items():
            if 'validate_allowed_value' in dir(self.__class__.__dict__[k]):
                if self.__class__.__dict__[k].validate_allowed_value(v):
                    self.__dict__[k] = v
                else:
                    raise ValueError('Value "{}" not in allowed_values of attribute "{}"'.format(str(v), str(k)))

        for k, v in kwargs.items():
            if 'validate_allowed_value' in dir(self.__class__.__dict__[k]):
                if self.__class__.__dict__[k].validate_allowed_value(v):
                    self.__dict__[k] = v
                else:
                    raise ValueError('Value "{}" not in allowed_values of attribute "{}"'.format(str(v), str(k)))

    @classmethod
    def _deflate_all_properties(cls, properties):
        item = {}
        for key, value in properties.items():
            if key.startswith('_'):
                continue
            item[key] = cls.__dict__[key].deflate(value)
        return item

    @classmethod
    def entities(cls):
        return EntitySet(cls)

    def deflate(self, value):
        if isinstance(value, StructuredEntity):
            return value.get_value_as_json()
        return value

    def inflate(self, value):
        if isinstance(self, StructuredEntity):
            return self.__class__(**value)
        return value

    def get_value_as_json(self):
        json_item = {}
        for key, value in self.value_dict.items():
            if isinstance(value, list):
                json_item[key] = [d.get_value_as_json() if isinstance(d, StructuredEntity) else d for d in value]
            elif isinstance(value, StructuredEntity):
                json_item[key] = value.get_value_as_json()
            else:
                json_item[key] = value
        return json_item

    def set_value(self, item, value):
        self._validate_allowed_values(value={item: value})
        self.__class__.__dict__[item].set_value(value)
        self.value_dict[item] = self.__class__.__dict__[item].get_value()

    def get_value(self, item):
        if isinstance(self.value_dict[item], list):
            return [d.get_value_as_json() if isinstance(d, StructuredEntity) else d for d in self.value_dict[item]]
        elif isinstance(self.value_dict[item], StructuredEntity):
            return self.value_dict[item].get_value_as_json()
        else:
            return self.value_dict[item]

    def save(self):
        """
        Saves the Entity object into elasticsearch
        """
        meta_item = {
            '_class': self.__class__.__name__,
            '_last_modified': time.time(),
            '_deleted': False
        }
        deflated_properties = self._deflate_all_properties(self.value_dict)
        item = {'_meta': meta_item, 'data': deflated_properties}
        is_saved, res = versioning.Version().insert(item)
        # Adding sleep time to provide elasticsearch buffer time to index the insert document
        time.sleep(2)
        return is_saved

    def delete(self):
        """
        Deletes the entity
        :return:
        """
        return versioning.Version().delete(self.get_value('uid'))


    def get_all_versions(self):
        """
        Retrieve a list of all versions of an entity
        :return: <list> of version numbers
        """
        return versioning.Version().get_all_versions(self.get_value('uid'))

    def load_version(self, version):
        """
        Load a version into an Entity object
        :param version: version number
        """
        params = versioning. \
            Version().get_doc_by_version(self.get_value('uid'), version).get('_source', {}).get('data', {})
        self.__dict__ = self.__class__(**params).__dict__
        return self

    def delete_version(self, version):
        """
        Delete a version of an entity
        :param version: version number
        :return: delete response
        """
        return versioning.Version().delete_version(self.get_value('uid'), version)


class EntitySet(object):
    """
    EntitySet class to inflate objects while searching in elasticsearch
    """

    def __init__(self, cls):
        self.query_builder = elasticsearch_query_builder_util.QueryBuilder()
        self.cls = cls

    def _inflate(self, doc):
        inflated_params = {}
        data_item = doc.get('data', {})
        for param in data_item.keys():
            inflated_property = self.cls.__dict__[param].inflate(data_item[param])
            inflated_params[param] = inflated_property
        instance = self.cls(**inflated_params)
        return instance

    def get(self, **kwargs):
        """
        Method to search elasticsearch for specified keyword arguments
        :return: List of matching documents
        """
        params = kwargs.copy()
        params_json = {key: value.get_value_as_json() if isinstance(value, StructuredEntity)
        else value
                       for key, value in params.items()}

        # Searching only on calling class name
        params_json['_class'] = self.cls.__name__

        # Searching only for "_meta._deleted: False"
        params_json['_deleted'] = False

        # TODO: Support search by Entity type
        match_query = self.query_builder.must_match(params_json)
        es_conn = elasticsearch_dao.ElasticsearchDao(elasticsearch_config.HOST, elasticsearch_config.PORT)
        search_res = es_conn.get_connection().search(elasticsearch_config.INDEX, elasticsearch_config.TYPE, match_query)
        doc_list = [self._inflate(d.get('_source')) for d in search_res.get('hits').get('hits')]
        return doc_list

    def filter(self):
        pass
