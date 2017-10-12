import json
from functools import wraps

from esorm.exception import ValueNotInAllowedValuesError, InvalidTypeError
from esorm.util.enrichment_util import inflate_json


def type_check(data_type):
    """
    Validates the data type of the value and default value 
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # type check when called from a constructor of a property type
            if func.__name__ == '__init__':
                value = kwargs.get('default')
            # type check when being called from other functions which have "value" as the first argument
            else:
                value = args[1]
            if not isinstance(value, data_type):
                raise InvalidTypeError(value, data_type)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_json(BaseProperty=None):
    def decorator(func):
        """
        Validates if the value argument is a valid JSON or not
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if func.__name__ == '__init__':
                value = kwargs.get('default', {})
            else:
                value = args[1]

            if BaseProperty:
                for k, v in value.items():
                    if not isinstance(v, BaseProperty):
                        raise TypeError("Expected one of the property or a JSON object, found {}".format(repr(type(v))))

            value = inflate_json(value, BaseProperty)
            if isinstance(value, dict):
                json.dumps(value)
            elif isinstance(value, str):
                json.loads(value)
            else:
                raise TypeError("Expected JSON Object, found {}".format(repr(type(value))))
            func(*args, **kwargs)
        return wrapper
    return decorator
