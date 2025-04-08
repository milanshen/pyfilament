# project filament
# import asyncio
import hashlib
import inspect
import json
import pickle


def dict_cache_key(func, parameters):
    return dict(func=inspect.getsource(func), parameters=parameters)


def json_cache_key(func, parameters):
    return json.dumps(dict_cache_key(func, parameters), sort_keys=True, separators=(',', ':'))


def pickle_cache_key(func, parameters):
    return pickle.dumps(dict_cache_key(func, parameters))


def hash_cache_key(func, parameters):
    return hashlib.md5(pickle_cache_key(func, parameters)).hexdigest()
