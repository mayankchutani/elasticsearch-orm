import uuid
from datetime import datetime
import pytz
import json
from abc import abstractmethod

from esorm.validator import type_check, validate_json
from esorm.util import http_request_util
from esorm.base import Base
from esorm.entity import StructuredEntity


__all__ = ["StringProperty",
           "UniqueIdProperty",
           "IntegerProperty",
           "FloatProperty",
           "ArrayProperty",
           "JsonObjectProperty",
           "DateTimeProperty",
           "GeocoordinateProperty"]


class BaseProperty(Base):
    """
    Base class for all property types
    """
    data_type = None

    def __init__(self, default=None, allowed_values=None, allowed_values_from_url=None, **kwargs):
        super().__init__(default=None, allowed_values=None, allowed_values_from_url=None, **kwargs)
        # If type is not in base types, check for presence of "uid" in kwargs
        if self.__class__.__name__ not in __all__:
            self._check_for_uid(**kwargs)

        self.has_default = True if default else False
        self.default = default

        if allowed_values is None:
            self.allowed_values = []
        elif allowed_values_from_url is not None:
            self.allowed_values = self._get_allowed_values_from_url(allowed_values_from_url)
        else:
            self.allowed_values = allowed_values

        self.set_value(default)

    def _check_for_uid(self, **kwargs):
        if 'uid' not in kwargs.keys():
            raise ValueError('"uid" not found in {}'.format(self.__class__))
        else:
            return True

    @staticmethod
    def _get_allowed_values_from_url(url):
        try:
            res = http_request_util.make_get_request(url=url)
            if res.status_code == 200:
                json_response = json.loads(res.content)
                return json_response.get('allowed_values', [])
            else:
                return []
        except Exception as e:
            raise e

    def __str__(self):
        return repr(self.value)

    @abstractmethod
    def get_value(self):
        return self.value

    def get_value_as_json(self):
        return {"value": self.get_value()}

    @abstractmethod
    def inflate(self, value):
        return value

    @abstractmethod
    def deflate(self, value):
        return value

    @abstractmethod
    def validate_allowed_value(self, value):
        pass

    @abstractmethod
    def set_value(self, value):
        self.value = value


class StringProperty(BaseProperty):
    """
    Stores Strings
    """
    data_type = str

    def __init__(self, default=None, allowed_values=None, **kwargs):
        if default is None:
            default = ''
        if allowed_values is None:
            allowed_values = []
        super().__init__(default=default, allowed_values=allowed_values, **kwargs)

    @type_check(data_type)
    def inflate(self, value):
        """
        From pythonic datatypes to ORM properties
        """
        return value

    @type_check(data_type)
    def deflate(self, value):
        return value

    @type_check(data_type)
    def set_value(self, value):
        self.value = value

    @type_check(data_type)
    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        elif value in self.allowed_values:
            return True
        elif value == self.default_value():
            return True
        else:
            return False

    def default_value(self):
        return self.default if self.has_default else ''

    def get_value(self):
        return self.value


class IntegerProperty(BaseProperty):
    """
    Stores Integers
    """
    data_type = int

    def __init__(self, default=None, allowed_values=None, **kwargs):
        if allowed_values is None:
            allowed_values = []
        super().__init__(default=default, allowed_values=allowed_values, **kwargs)

    @type_check(data_type)
    def inflate(self, value):
        return value

    @type_check(data_type)
    def deflate(self, value):
        return value

    def default_value(self):
        return self.default if self.has_default else -1

    @type_check(data_type)
    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        if value in self.allowed_values:
            return True
        elif value == self.default_value():
            return True
        else:
            for item in self.allowed_values:
                if isinstance(item, tuple):
                    lower_range = item[0]
                    upper_range = item[1]
                    if lower_range <= value <= upper_range:
                        return True
        return False


class FloatProperty(BaseProperty):
    """
    Store Float
    """
    data_type = float

    def __init__(self, default=None, allowed_values=None, **kwargs):
        super().__init__(default=default, allowed_values=allowed_values, **kwargs)

    @type_check(data_type)
    def inflate(self, value):
        return value

    @type_check(data_type)
    def deflate(self, value):
        return value

    def default_value(self):
        return self.default if self.has_default else float('inf')

    @type_check(data_type)
    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        if value in self.allowed_values:
            return True
        elif value == self.default_value():
            return True
        else:
            for item in self.allowed_values:
                if isinstance(item, tuple):
                    lower_range = item[0]
                    upper_range = item[1]
                    if lower_range <= value <= upper_range:
                        return True
        return False


class ArrayProperty(BaseProperty):
    """
    Store Array
    """
    data_type = list

    def __init__(self, default=None, base_property=None, **kwargs):
        if default is None:
            default = []

        if base_property is not None:
            if not isinstance(base_property, Base):
                raise TypeError('Expecting model property, got {}'.format(repr(type(base_property))))

            if isinstance(base_property, ArrayProperty):
                raise TypeError('ArrayProperty cannot have nested ArrayProperty')

        self.base_property = base_property
        super().__init__(default, **kwargs)

    def add(self, value):
        self.value.append(value)

    def get_value(self):
        return self.value

    def default_value(self):
        return self.default if self.has_default else []

    def inflate(self, value):
        if self.base_property:
            return [self.base_property.inflate(item) for item in value]
        return list(value)

    def deflate(self, value):
        if self.base_property:
            return [self.base_property.deflate(item) for item in value]
        return list(value)

    @type_check(data_type)
    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        if sorted(value) == sorted(self.allowed_values):
            return True
        elif value == self.default_value():
            return True
        else:
            return False

    @type_check(data_type)
    def set_value(self, value):
        deflated_value = self.deflate(value)
        if len(value) == 0:
            self.value = value
        elif isinstance(value[0], self.base_property.__class__.data_type):
            self.value = value
        else:
            raise TypeError('Value {} is expected to be of type {}, got {}'.format(
                str(value[0]), self.base_property.__class__, type(value[0])
            ))


class JsonObjectProperty(BaseProperty):
    """
    Store JSON
    """
    data_type = dict

    @validate_json(BaseProperty)
    def __init__(self, default=None, allowed_values=None, **kwargs):
        if default is None:
            default = {}
        super().__init__(default=default, allowed_values=allowed_values, **kwargs)

    @validate_json(BaseProperty)
    def set_value(self, value):
        self.value = value

    def _inflate_json(self, value):
        for k, v in value.items():
            if isinstance(v, BaseProperty):
                value[k] = v.get_value()
            elif isinstance(v, list):
                value[k] = [q.get_value() if isinstance(q, BaseProperty) else q for q in v]
            elif isinstance(v, dict):
                self._inflate_json(v)
        return value

    def get_value_as_json(self):
        return self._inflate_json(self.value)

    def default_value(self):
        return self.default if self.has_default else {}

    @type_check(data_type)
    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        elif value == self.default_value():
            return True
        raise NotImplementedError()


class UniqueIdProperty(BaseProperty):
    """
    Store UniqueID as String
    """
    data_type = str

    def __init__(self, default=None, **kwargs):
        if default is None:
            default = str(uuid.uuid4())
        super().__init__(default=default, **kwargs)

    def default_value(self):
        return self.default if self.has_default else str(uuid.uuid4())

    @type_check(str)
    def set_value(self, value):
        self.value = value

    @type_check(data_type)
    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        elif value == self.default_value():
            return True
        raise NotImplementedError()


class DateTimeProperty(BaseProperty):
    """
    Store datetime object
    """

    def __init__(self, default_now=False, **kwargs):
        if default_now:
            if 'default' in kwargs:
                raise ValueError('Too many default values')
        kwargs['default'] = datetime.utcnow().replace(tzinfo=pytz.utc)
        super().__init__(**kwargs)

    @type_check(datetime)
    def deflate(self, value):
        if not isinstance(value, datetime):
            raise ValueError('datetime object expected, got {0}'.format(value))
        if value.tzinfo:
            value = value.astimezone(pytz.utc)
            epoch_date = datetime(1970, 1, 1, tzinfo=pytz.utc)
        # elif config.FORCE_TIMEZONE:
        #     raise ValueError("Error deflating {} no timezone provided".format(value))
        else:
            # No timezone specified on datetime object.. assuming UTC
            epoch_date = datetime(1970, 1, 1)
        return float((value - epoch_date).total_seconds())

    @type_check(float)
    def inflate(self, value):
        try:
            epoch = float(value)
        except ValueError:
            raise ValueError('float or integer expected, got {0} cant inflate to datetime'.format(value))
        return datetime.utcfromtimestamp(epoch).replace(tzinfo=pytz.utc)

    def default_value(self):
        return self.default if self.has_default else datetime.utcnow()

    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        elif value == self.default_value():
            return True
        raise NotImplementedError()


class GeocoordinateProperty(BaseProperty):
    """
    Store Coordinates {"lat": <>, "lon": <>}
    """
    data_type = dict

    def __init__(self, default=None, **kwargs):
        if default:
            if not isinstance(default, dict):
                raise TypeError('default value needs to be <dict>, found {}'.format(str(type(default))))
            if 'lat' not in default or 'lon' not in default:
                raise ValueError('Geocoordinate value must have "lat" and "lon" as fields')
        elif default is None:
            default = {}
        super().__init__(default, **kwargs)

    @type_check(data_type)
    def set_value(self, value):
        self.value = value

    def default_value(self):
        return self.default if self.has_default else {"lat": -1.0, "lon": -1.0}

    @type_check(data_type)
    def validate_allowed_value(self, value):
        if self.allowed_values is None or self.allowed_values == []:
            return True
        elif value == self.default_value():
            return True
        raise NotImplementedError()


if __name__ == '__main__':
    # c = StringPropertyperty()
    # c.set_value()
    # j = JsonObjectProperty()
    # j.set_value({"a": c})
    # print(j.get_value_as_json())

    class Person(StructuredEntity):
        name = StringProperty()
        uid = UniqueIdProperty()
        age = IntegerProperty()
        coordinates = GeocoordinateProperty()
        phone = ArrayProperty()


    class New(StructuredEntity):
        uid = UniqueIdProperty()
        user = Person()
        des = StringProperty()
        user_list = ArrayProperty(base_property=Person())


    p = Person(uid='234')
    p.set_value('name', 'mayank12')
    print(p)
    print(p.save())

    n = New(uid="2342", user=p, user_list=[p])
    print(n)
    print(n.get_value('user_list'))
    print(n.save())

    new = New.entities().get(uid='2342')[0]
    print(new)
    print(new.get_value_as_json())
    print(new.get_all_versions())

    # n = Person.entities().get(name='person2')[0]
    # print(n.get_all_versions())
