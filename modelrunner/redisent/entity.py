# -*- coding: utf-8 -*-
import json
import datetime
import re


class RedisEntityMeta(type):
    """
    Meta class for RedisEntity

    Meta class was needed to implement class level 'magic' methods
    """
    def __setitem__(cls, key, entity):
        json_entity = json.dumps(entity, cls=cls.json_encoder())
        cls._db.hset(cls.hash_name(), key, json_entity)

    def __delitem__(cls, key):
        cls._db.hdel(cls.hash_name(), key)

    def __getitem__(cls, key):
        json_entity = cls._db.hget(cls.hash_name(), key)
        if json_entity is None:
            raise KeyError(
                "Key {} does not exist in {}".
                format(key, cls.hash_name()))
        else:
            return json.loads(json_entity, object_hook=cls.json_decode)

    def keys(cls):
        return cls._db.hkeys(cls.hash_name())

    def __len__(cls):
        return cls._db.hlen(cls.hash_name())

    def items(cls):
        items = cls._db.hgetall(cls.hash_name()).items()
        items = [(key, json.loads(entity, object_hook=cls.json_decode))
                 for key, entity in items]
        return items

    def values(cls):
        values = cls._db.hgetall(cls.hash_name()).values()
        values = [json.loads(entity, object_hook=cls.json_decode)
                  for entity in values]
        return values

    def hash_name(cls):
        if cls._custom_hash_name is not None:
            return cls._custom_hash_name

        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        entity_snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        # poor man's pluralize
        if not re.search(r's$', entity_snake_case):
            entity_snake_case = "{}s".format(entity_snake_case)

        if cls._prefix:
            return "{}:{}".format(cls._prefix, entity_snake_case)
        else:
            return entity_snake_case

    def json_encoder(cls):
        """
        Return a JSONEncoder that supports encoding classes of this object
        Mainly done for datetime to isoformat conversion

        override as needed
        """
        if hasattr(cls, '_json_encoder'):
            return cls._json_encoder
        else:
            class RedisEntityEncoder(json.JSONEncoder):
                """
                Encode Entity as something that can be json serialized
                """
                def default(self, obj):
                    if isinstance(obj, cls):
                        return obj.__dict__
                    if isinstance(obj, datetime.datetime):
                        return obj.isoformat()
                    return json.JSONEncoder.default(self, obj)

            cls._json_encoder = RedisEntityEncoder
            return RedisEntityEncoder

    def json_decode(cls, entity_dict):
        """
        Decode an entity from a dict (useful for JSON decoding)

        Assumes that each entity has an init that supports kwargs for setting
        its attributes
        """
        return cls(**entity_dict)


class RedisEntity(metaclass=RedisEntityMeta):
    """
    Class implementing base read/write of python objects from/to Redis

    Exposes a mutable container interface for an entity

    The class itself maps to a redis hash

    TODO:  Examples!

    See testing/test_redisent.py
    """
    # __metaclass__ = RedisEntityMeta

    # the redis db connection
    _db = None

    # the prefix of the hash (to be prepended to the class name)
    _prefix = None

    # allow subclasses to override the hash_name
    _custom_hash_name = None
