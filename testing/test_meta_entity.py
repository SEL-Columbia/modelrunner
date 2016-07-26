"""
Test whether metaclass-based implementation of magic methods works
"""

class MetaEntity(type):

    def __getitem__(cls, k):
        return cls.data[k]

    def __setitem__(cls, k, entity):
        cls.data[k] = entity


class Entity:
    __metaclass__ = MetaEntity
    data = {}

class User(Entity):
    
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name


def test_meta_entity():

    users = [User(0, '0'), User(1, '1')]
    for u in users:
        User[u.id] = u

    assert User[0] == users[0]
