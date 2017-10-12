
__all__ = ["ValueNotInAllowedValuesError", "InvalidArgumentError", "InvalidTypeError"]


class ValueNotInAllowedValuesError(ValueError):

    def __init__(self, value, allowed_values):
        super().__init__('Value {} not in {}'.format(repr(value), repr(allowed_values)))


class InvalidTypeError(TypeError):

    def __init__(self, value, data_type):
        super().__init__('Expected {}, found {}'.format(repr(data_type), repr(type(value))))


class InvalidArgumentError(ValueError):

    def __init__(self, value, cls):
        super().__init__('Argument "{}" not defined in {}'.format(value, cls))

