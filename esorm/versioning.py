from esorm.dao import elasticsearch_dao
from esorm.config import elasticsearch_config
from esorm.util import elasticsearch_query_builder_util


class Version(object):
    """
    Maintains the versions of the documents
    """

    def __init__(self):
        self.es_conn = elasticsearch_dao.ElasticsearchDao(
            elasticsearch_config.HOST,
            elasticsearch_config.PORT)

    def _exists(self, id):
        """
        Check if the document with "id" already exists or not
        :return: 
        """
        return self.es_conn.get_connection().exists(index=elasticsearch_config.INDEX,
                                                    doc_type=elasticsearch_config.TYPE,
                                                    id=id)

    def _get_doc_by_id(self, id):
        return self.es_conn.get_connection().get(index=elasticsearch_config.INDEX, id=id)

    def _insert_as_version(self, doc, upsert=True):
        return self.es_conn.insert_one(doc,
                                       elasticsearch_config.VERSIONING_INDEX,
                                       elasticsearch_config.VERSIONING_TYPE,
                                       id=doc.get('data').get('uid'),
                                       upsert=upsert)

    def insert(self, document):
        """
        Inserts and versions the document
        :param document: JSON document
        :return: Insertion response
        """
        uid = document.get('data', {}).get('uid')

        if not self._exists(uid):
            insertion_response = self.es_conn.insert_one(document,
                                                         elasticsearch_config.INDEX,
                                                         elasticsearch_config.TYPE,
                                                         document.get('data').get('uid'))
            version = insertion_response.get('_version')
            item = document.copy()
            item['_meta'].update({'_version': version})
            version_insert_response = self._insert_as_version(item, upsert=False)
            return True, version_insert_response
        else:
            doc = self._get_doc_by_id(uid).get('_source')
            if doc.get('data') == document.get('data'):
                return False, {'message': 'Document already exists with same ID and data'}
            else:
                insertion_response = self.es_conn.insert_one(document,
                                                             elasticsearch_config.INDEX,
                                                             elasticsearch_config.TYPE,
                                                             document.get('data').get('uid'))
                version = insertion_response.get('_version')
                document['_meta'].update({'_version': version})
                version_insert_response = self._insert_as_version(document, upsert=False)
                return True, version_insert_response

    def delete(self, uid):
        """
        Deletes the Entity as well it's all versions
        :param uid: uid of the Entity
        :return: Delete response
        """
        es_query = elasticsearch_query_builder_util.QueryBuilder.must_match({"uid": uid})
        res = self.es_conn.get_connection().search(elasticsearch_config.INDEX,
                                                   elasticsearch_config.TYPE,
                                                   body=es_query)
        result_doc_list = res.get('hits', {}).get('hits', [])
        if len(result_doc_list) == 0:
            raise Exception('No document found with uid: {}'.format(uid))
        doc = result_doc_list[0]
        item = doc.get('_source')
        item['_meta']['_deleted'] = True
        insertion_response = self.es_conn.insert_one(item,
                                                     elasticsearch_config.INDEX,
                                                     elasticsearch_config.TYPE,
                                                     item.get('data').get('uid'))

        version_res = self.es_conn.get_connection().search(elasticsearch_config.VERSIONING_INDEX,
                                                           elasticsearch_config.VERSIONING_TYPE,
                                                           body=es_query)

        if version_res and isinstance(version_res, dict):
            for doc in version_res.get('hits', {}).get('hits', []):
                item = doc.get('_source')
                item['_meta']['_deleted'] = True
                _id = doc.get('_id')
                version_insert_response = self.es_conn.insert_one(item,
                                                                  elasticsearch_config.VERSIONING_INDEX,
                                                                  elasticsearch_config.VERSIONING_TYPE,
                                                                  id=_id)
                if version_insert_response and isinstance(version_insert_response, dict):
                    pass
            return True
        else:
            return False

    def get_all_versions(self, id):
        """
        Get list of all version numbers
        :param id: Unique Id of the document
        :return: list of version numbers
        """
        res = self.es_conn.get_connection().search(elasticsearch_config.VERSIONING_INDEX,
                                                   elasticsearch_config.VERSIONING_TYPE,
                                                   body=elasticsearch_query_builder_util.QueryBuilder.match(
                                                       {'data.uid': id}))
        if res and isinstance(res, dict):
            return [d.get('_source').get('_meta').get('_version') for d in res.get('hits').get('hits')]
        else:
            return []

    def get_doc_by_version(self, id, version):
        """
        Find document by version number
        :param id: Unique ID of the document
        :param version: Version number of the document
        :return: document as JSON
        """
        es_query = elasticsearch_query_builder_util.QueryBuilder.must_match(
            {'uid': id, '_version': version})
        res = self.es_conn.get_connection().search(elasticsearch_config.VERSIONING_INDEX,
                                                   elasticsearch_config.VERSIONING_TYPE,
                                                   body=es_query)
        if res and isinstance(res, dict):
            doc_list = res.get('hits', {}).get('hits', [])
            if len(doc_list) == 0:
                return {}
            elif len(doc_list) > 1:
                raise IndexError("Too many values in the list, should be only 1")
            else:
                return doc_list[0]

    def delete_version(self, id, version):
        """
        Deletes a version of document
        :param id: document id 
        :param version: version number
        :return: ES Delete response <dict>
        """
        res = self.es_conn.get_connection().delete_by_query(index=elasticsearch_config.VERSIONING_INDEX,
                                                            doc_type=elasticsearch_config.VERSIONING_TYPE,
                                                            body=elasticsearch_query_builder_util. \
                                                            QueryBuilder.must_match({'uid': id, '_version': version}))
        return res


if __name__ == '__main__':
    # print(Version().insert({"data": {"uid": "person1", "name": "Mayank Chutani"},
    #                                 "_meta": {
    #                                     "_class": "Person"
    #                                 }}))
    # print(Version().get_all_versions('person1'))
    # print(Version().get_doc_by_version('person1', 2))
    # print(Version().delete_version('person1', 1))
    # print(Version().get_all_versions('person1'))
    print(Version().delete('2345'))
