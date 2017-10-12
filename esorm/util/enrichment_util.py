def inflate_json(value, BaseProperty):
    """
    Inflates JSON into BaseProperty type
    """
    for k, v in value.items():
        if isinstance(v, BaseProperty):
            value[k] = v.get_value()
        elif isinstance(v, list):
            value[k] = [q.get_value() if q.isinstance(BaseProperty) else q for q in v]
        elif isinstance(v, dict):
            inflate_json(v, BaseProperty)
    return value