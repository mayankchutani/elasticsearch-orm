import elasticsearch
import json


class ElasticsearchDao(object):
    """
    Elasticsearch Data Access Object for connection and insertion
    """

    def __init__(self, host, port):
        self.connection = elasticsearch.Elasticsearch(['http://{esHost}:{esPort}'.format(esHost=host, esPort=port)],
                                                      timeout=3000)

    def get_connection(self):
        """
        Returns the connection object
        """
        return self.connection

    def _bulk_insert(self, index, type, actionList):
        try:
            self.connection.index(index=index)
        except:
            pass
        res = self.connection.bulk(body=actionList, index=index, doc_type=type)
        self.connection.indices.refresh()
        return res

    def insert_bulk(self, doc_list, index, type, upsert=True, create_mapping=True):
        """
        Insertion of elasticsearch documents
        :param doc_list: list of JSON documents to be inserted
        :param index: name of the elasticsearch index
        :param type: name of the elasticsearch index type
        """
        actionList = []
        actionCount = 1

        # Create mappings
        if create_mapping:
            self.create_mapping(index, type)

        for doc in doc_list:
            item = doc.copy()
            id = item.get('data', {}).get('uid')

            if actionCount % 1000 == 0:
                self._bulk_insert(index, type, actionList[:])
                actionList = []

            if upsert:
                actionList.append({"index": {
                    "_index": index,
                    "_type": type,
                    "_id": id
                }})
            else:
                actionList.append({"index": {
                    "_index": index,
                    "_type": type
                }})
            actionList.append(item)
            actionCount += 1
        if len(actionList) > 0:
            self._bulk_insert(index, type, actionList[:])

    def insert_one(self, doc, index, type, id, upsert=True, create_mapping=True):
        # Create mappings
        if create_mapping:
            self.create_mapping(index, type)

        if not upsert:
            res = self.connection.index(index, type, doc)
        else:
            res = self.connection.index(index, type, doc, id)
        return res

    def create_mapping(self, index, type):
        mapping = {
            "mappings": {
                type: {
                    "properties": {
                        "data": {
                            "properties": {
                                "coordinates": {"type": "geo_point"}
                            }
                        }

                    }
                }
            }
        }
        return self.connection.indices.create(index=index, ignore=400, body=json.dumps(mapping))
