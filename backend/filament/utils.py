import inspect
import math
import time
import traceback
from collections import defaultdict
from dataclasses import fields as dataclasses_fields
from dataclasses import is_dataclass
from datetime import datetime

from pandas import DataFrame as PandasDataFrame
from polars import DataFrame as PolarsDataFrame
from pydantic import BaseModel


def get_arg_name(*args, **kwargs):
    args_name_parts = []
    args_name_parts += [f'{arg}' for arg in args]
    args_name_parts += [f'{key}={value}' for key, value in kwargs.items()]
    return ', '.join(args_name_parts)


def now(ceil=False, places=1):
    divisor = 10**places
    if not ceil:
        return math.floor(time.time() * divisor) / divisor
    return math.ceil(time.time() * divisor) / divisor


def get_function_type(func):
    if inspect.isasyncgenfunction(func):
        return 'async generator function'
    elif inspect.isasyncgen(func):
        return 'async generator'
    elif inspect.iscoroutinefunction(func):
        return 'coroutine function'
    elif inspect.iscoroutine(func):
        return 'coroutine'
    elif inspect.isgenerator(func):
        return 'generator'
    elif inspect.ismethod(func):
        return 'method'
    elif inspect.isfunction(func):
        return 'function'
    else:
        return 'unknown: {}'.format(type(func))


def json_encode_safe(obj, max_list_size=32, max_dict_size=64, max_bytes_size=1024):
    if obj is None:
        return None
    elif isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, bool):
        return obj
    elif isinstance(obj, list):
        should_trim = len(obj) > max_list_size * 2
        if should_trim:
            return [json_encode_safe(i) for i in obj[:max_list_size]] + [f'... (+{len(obj) - max_list_size})']
        return [json_encode_safe(i) for i in obj]
    elif isinstance(obj, dict):
        keys = list(obj.keys())
        should_trim = len(obj) > max_dict_size * 2
        if should_trim:
            keys = keys[:max_dict_size]
        results = {json_encode_safe(k): json_encode_safe(obj[k]) for k in keys}
        if should_trim:
            results['...'] = f'(+{len(obj) - max_dict_size})'
        return results
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, set) or isinstance(obj, tuple) or isinstance(obj, frozenset):
        return json_encode_safe(list(obj))
    elif isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, defaultdict):
        return json_encode_safe(dict(obj))
    elif isinstance(obj, PandasDataFrame):
        return json_encode_safe(obj.to_dict(orient='records'))
    elif isinstance(obj, PolarsDataFrame):
        return json_encode_safe(obj.to_dicts())
    elif isinstance(obj, bytes):
        content = f'0x{obj.hex()}'
        should_trim = len(obj) > max_bytes_size * 2
        if should_trim:
            return content[:max_bytes_size] + f'... (+{len(obj) - max_bytes_size})'
        return content
    elif isinstance(obj, str):
        should_trim = len(obj) > max_bytes_size * 2
        if should_trim:
            return obj[:max_bytes_size] + f'... (+{len(obj) - max_bytes_size})'
        return obj
    elif isinstance(obj, object) and is_dataclass(obj):
        attr_names = [field.name for field in dataclasses_fields(obj)]
        return {json_encode_safe(attr): json_encode_safe(getattr(obj, attr)) for attr in attr_names}
    elif isinstance(obj, Exception):
        result = {
            'type': type(obj).__name__,
            'value': str(obj),
        }
        if hasattr(obj, '__traceback__'):
            tb = obj.__traceback__
            frames = traceback.extract_tb(tb)
            serialized = [
                {
                    'filename': frame.filename,
                    'lineno': frame.lineno,
                }
                for frame in frames
            ]
            result['traceback'] = serialized
        return result
    else:
        return {
            'type': type(obj).__name__,
            'value': str(obj),
        }
