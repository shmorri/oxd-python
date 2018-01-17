import unittest

from oxdpython.utils import Resource, ResourceSet

class ResourceSetTestCase(unittest.TestCase):
    def test_len_of_resource_set(self):
        rset = ResourceSet()
        assert len(rset) == 0
        rset.add('/images')
        assert len(rset) == 1
        rset.add('/photos')
        assert len(rset) == 2

    def test_add_resource(self):
        rset = ResourceSet()
        rset.add('/api/photos/')
        assert len(rset) == 1

    def test_remove_resource(self):
        rset = ResourceSet()
        rset.add('/images')
        rset.add('/docs')
        rset.add('/files')
        assert len(rset) == 3
        rset.remove('/docs')
        assert len(rset) == 2

    def test_dump(self):
        rset = ResourceSet()
        assert rset.dump() == []
        rset.add('/api/photos/')
        assert rset.dump() == [{'path': '/api/photos/', 'conditions': []}]

    def test_str(self):
        rset = ResourceSet()
        assert str(rset) == '[]'
        rset.add('/api')
        assert str(rset) == '[{"path": "/api", "conditions": []}]'

    def test_repr(self):
        rs = ResourceSet()
        assert repr(rs) == "<ResourceSet []>"
        rs.add('/api')
        assert repr(rs) == "<ResourceSet [/api]>"
        rs.add('/files')
        assert repr(rs) == "<ResourceSet [/api,/files]>"

    def test_adding_resource_conditions(self):
        rset = ResourceSet()
        path = rset.add('/path')
        path.set_condition('GET', 'View Resource')
        assert rset.dump() == [{
            'path': '/path',
            'conditions': [{'httpMethod': ['GET'],
                            'scopes': ['View Resource']}]
        }]


class ResourceTestCase(unittest.TestCase):
    def test_dump_returns_dict(self):
        r = Resource('/api')
        assert r.dump() == {'path': '/api', 'conditions': []}

    def test_string_representation_of_resource(self):
        r = Resource('/api')
        assert str(r) == '{"path": "/api", "conditions": []}'

    def test_repr(self):
        r = Resource('/api')
        assert repr(r) == '<Resource /api>'

    def test_add_condition_to_a_resource(self):
        r = Resource('/api')
        r.set_condition(http_method='GET', scope='View')
        assert r.dump() == {'path': '/api', 'conditions': [
            {'httpMethod': ['GET'], 'scopes': ['View']}
        ]}

    def test_adding_another_scope_for_same_http_method_updates_condition(self):
        r = Resource('/api')
        r.set_condition('GET', 'View')
        r.set_condition('GET', 'All')
        assert r.dump() == {'path': '/api', 'conditions': [
            {'httpMethod': ['GET'], 'scopes': ['View', 'All']}
        ]}

    def test_adding_multiple_http_methods(self):
        r = Resource('/api')
        r.set_condition('GET', 'View')
        r.set_condition('POST', 'Add')
        assert r.dump() == {'path': '/api', 'conditions': [
            {'httpMethod': ['GET'], 'scopes': ['View']},
            {'httpMethod': ['POST'], 'scopes': ['Add']}
        ]}

