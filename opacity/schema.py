import importlib

from collections import namedtuple


Schema = namedtuple("Schema", ["transform", "keyword_to_int", "keyword_from_int"])


# public functions


def minimal_ops(keyword_to_int, transform=None, context=None):
    context = context or globals()
    return {keyword_to_int[op]: context.get("op_%s" % op) for op in keyword_to_int.keys()}


def schema_for_name(schema_name):
    mod = importlib.import_module(schema_name)

    keyword_from_int = mod.KEYWORD_FROM_INT
    keyword_to_int = {v: k for k, v in enumerate(keyword_from_int)}

    return Schema(
        transform=mod.transform, keyword_to_int=keyword_to_int, keyword_from_int=keyword_from_int)
