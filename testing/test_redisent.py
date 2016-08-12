# -*- coding: utf-8 -*-

from modelrunner import settings
from modelrunner.redisent import RedisEntity

import datetime

RedisEntity._prefix = "test"
RedisEntity._db = settings.redis_connection()


class User(RedisEntity):

    def __init__(self, id=None, name=None, created=None):
        self.id = int(id)
        self.name = name
        self.created = self._init_created(created)

    def _init_created(self, created):
        if isinstance(created, basestring):
            return datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%S")
        elif isinstance(created, datetime.datetime):
            return created
        else:
            raise ValueError(
                "Invalid type {} for created attribute".
                format(type(created)))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


def test_redisent():

    users = {"0": User(0, "user0", "2000-01-01T00:00:00"),
             "1": User(1, "user1", "2000-01-02T00:00:00"),
             "2": User(2, "user2", "2000-01-03T00:00:00")}

    # populate "test:users" hash
    for user in users:
        User[user] = users[user]

    assert len(User) == len(users), "length test fails"

    assert all(
        [User[key] == users[key] for key in User.keys()]),\
        "keys test fails"

    assert all(
        [entity == users[key] for key, entity in User.items()]),\
        "items test fails"

    # delete users
    for user in users:
        del User[user]

    assert len(User) == 0, "del test fails"
