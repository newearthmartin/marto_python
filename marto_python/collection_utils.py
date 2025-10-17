import json
import logging
from json import JSONEncoder
from decimal import Decimal
from typing import Any, Callable, Optional, Iterable
from .mypy import Predicate


logger = logging.getLogger(__name__)


def add_list_elem(dct, key, elem):
    if key in dct and dct[key] is not None:
        dct[key].append(elem)
    else:
        dct[key] = [elem]


def map_dict(map_fn: Callable, dct: dict) -> dict:
    return {k: map_fn(k, v) for k, v in dct.items()}


def flat_map(map_fn: Callable, iterable: Iterable) -> Iterable:
    return flatten(map_fn(e) for e in iterable)


def flatten(iterable: Iterable) -> Iterable:
    return (e2 for e1 in iterable for e2 in e1)


def to_list(dct: dict, sort_by_key: bool = False, sorting_key_fn: Optional[Callable] = None):
    lst = list(dct.items())
    if sort_by_key:
        lst.sort(key=lambda e: e[0])
    elif sorting_key_fn:
        lst.sort(key=sorting_key_fn)
    return lst


def split_chunks(lst: list, chunk_size: int) -> list[list]:
    chunks = []
    i = 0
    while i < len(lst):
        chunks.append(lst[i: i + chunk_size])
        i += chunk_size
    return chunks


def filter_map(dct: dict, predicate: Predicate) -> dict:
    return {k: dct[k] for k in dct if predicate(k)}


def filter_map_keys(dct: dict, keys: Iterable) -> dict:
    return filter_map(dct, lambda k: k in keys)


def get_or_add_new(dct: dict, key: Any, new_elem_func: Callable) -> Any:
    if key not in dct:
        dct[key] = new_elem_func()
    return dct[key]


def is_list_or_tuple(x: Any) -> bool:
    return isinstance(x, (list, tuple))


def list2comma_separated(lst: list) -> str:
    if not lst:
        return ''
    lst = [str(e) for e in lst]
    return ','.join(lst)


def dict_encode(obj, encoder: Callable = None):
    """
    Useful for serializing objects to JSON
    Use: json.dumps(dict_encode(obj, encoder=some_encoder_func))
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        rv = {}
        for k, v in obj.items():
            rv[k] = dict_encode(v, encoder)
        return rv
    if hasattr(obj, '__iter__'):
        return [dict_encode(e, encoder) for e in obj]
    if not hasattr(obj, '__dict__'):
        return obj
    if not encoder:
        raise Exception(f"Can't encode object of type {type(obj)} without an encoder")
    return dict_encode(encoder(obj), encoder)


def first(predicate: Predicate, iterable: Iterable) -> Optional[Any]:
    for item in iterable:
        if predicate(item): return item
    return None


def exists(predicate: Predicate, iterable: Iterable) -> bool:
    return first(predicate, iterable) is not None


def split(predicate: Predicate, iterable: Iterable) -> tuple[list, list]:
    true_list = []
    false_list = []
    for item in iterable:
        if predicate(item):
            true_list.append(item)
        else:
            false_list.append(item)
    return true_list, false_list


class DictJsonEncoder(JSONEncoder):
    def default(self, o):
        dictionary = getattr(o, '__dict__', None)
        if dictionary:
            return dictionary
        elif isinstance(o, Decimal):
            return float(o)
        else:
            try:
                return json.dumps(o)
            except TypeError:
                logger.warning(f"Don't know how to json encode {o} - using str")
                return str(o)


def filter_json_encodable(dct: dict) -> dict:
    rv = {}
    for k, v in dct.items():
        try:
            json.dumps(k)
            json.dumps(v)
            rv[k] = v
        except:
            pass
    return rv


def load_json(string: str, default: Optional[Any] = None) -> Any:
    """
    will load the json string if there is something in str
    otherwise will return the default object if set, otherwise {}
    """
    if string: return json.loads(string)
    if default is not None: return default
    return {}


def contains_non_empty(lst: list) -> bool:
    for e in lst:
        if e:
            return True
    return False
