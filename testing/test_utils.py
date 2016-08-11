# -*- coding: utf-8 -*-
from modelrunner import utils
from datetime import datetime

def test_json_datetime():
    d = {'num_val': 1.23, 'str_val': 'hello', 'datetime_val': datetime.now()}
    dump = utils.json_dumps_datetime(d)
    loaded = utils.json_loads_datetime(dump)
    assert d == loaded
