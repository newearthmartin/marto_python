import json


def add_list_elem(d, key, elem):
    if key in d and d[key] is not None:
        d[key].append(elem)
    else:
        d[key] = [elem]


def to_dict(lst, map_func):
    dct = {}
    for elem in lst:
        kv = map_func(elem)
        if kv:
            k = kv[0]
            v = kv[1]
            if k is not None: dct[k] = v
    return dct


def map_dict(dct, map_fn):
    rv = {}
    for k,v in dct.items():
        rv[k] = map_fn(k, v)
    return rv


def to_list(dct, sorting_key_fn=None):
    lst = list(dct.items())
    if sorting_key_fn:
        lst.sort(key=sorting_key_fn)
    return lst


def filter_map(old_map, keys):
    return {k: old_map[k] for k in old_map if k in keys}


def get_or_add_new(dct, key, new_elem_func):
    if key not in dct:
        dct[key] = new_elem_func()
    return dct[key]


def is_list_or_tuple(x):
    return isinstance(x, (list, tuple))


def list2comma_separated(the_list):
    if not the_list:
        return ''
    s = ''
    i = 0
    for e in the_list:
        if i != 0:
            s += ','
        i += 1
        s += str(e)
    return s


def dict_encode(obj, encoder=None):
    """
    useful for serializing objects to JSON
    use: json.dumps(dict_encode(obj,encoder=some_encoder_func))
    """
    if obj is None:
        return None
    elif isinstance(obj, str):
        return obj
    elif type(obj) == dict:
        rv = {}
        for k, v in obj.items():
            rv[k] = dict_encode(v, encoder)
        return rv
    elif hasattr(obj, '__iter__'):
        rv = []
        for elem in obj:
            rv.append(dict_encode(elem, encoder))
        return rv
    elif not hasattr(obj, '__dict__'):
        return obj
    else:
        # is object
        if not encoder:
            raise Exception(f"Can't encode object of type {type(obj)} without an encoder")
        return dict_encode(encoder(obj), encoder)


def first(condition, iterable):
    for item in iterable:
        if condition(item): return item
    return None


def filter_json_encodable(dct):
    rv = {}
    for k,v in dct.items():
        try:
            json.dumps(k)
            json.dumps(v)
            rv[k] = v
        except:
            pass
    return rv


def load_json(str, default=None):
    """
    will load the json string if there is something in str
    otherwise will return the default object if set, otherwise {}
    """
    if str:
        return json.loads(str)
    elif default is not None:
        return default
    else:
        return {}


def contains_non_empty(lst):
    filtered = list(filter(lambda e: e, lst))
    return len(filtered) > 0