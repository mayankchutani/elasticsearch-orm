class QueryBuilder(object):
    """
    Elasticsearch query builder module
    """

    def __init__(self):
        pass

    @staticmethod
    def must_match(kwargs):
        """
        Creates a "must" query to match all kwargs
        :return: ES DSL query
        """
        meta_fields = {}
        data_fields = {}
        for key, value in kwargs.items():
            if key.startswith('_'):
                meta_fields[key] = value
            else:
                data_fields[key] = value

        item = {"query": {
            "bool": {
                "must": []
            }
        }}
        for key, value in meta_fields.items():
            item['query']['bool']['must'].append({"match": {'_meta.' + key: value}})
        for key, value in data_fields.items():
            # Adding geonear query
            if key == 'geo_near':
                item['query']['bool'].update(QueryBuilder._create_geo_near_query(kwargs[key]))
            else:
                item['query']['bool']['must'].append({"match": {'data.' + key: value}})
        return item

    @staticmethod
    def match(doc_dict):
        return {"query": {"match": doc_dict}}

    @staticmethod
    def _create_geo_near_query(item):
        coordinates, distance_km = item
        return {
            "filter": {
                "geo_distance": {
                    "distance": str(distance_km) + 'km',
                    "data.coordinates": coordinates
                }
            }}


if __name__ == '__main__':
    print(QueryBuilder.must_match({"abc": 10}))