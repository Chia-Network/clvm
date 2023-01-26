def operators_for_dict(keyword_to_atom, op_dict, op_name_lookup={}):
    d = {}
    for op in keyword_to_atom.keys():
        op_name = "op_%s" % op_name_lookup.get(op, op)
        op_f = op_dict.get(op_name)
        if op_f:
            d[keyword_to_atom[op]] = op_f
    return d


def operators_for_module(keyword_to_atom, mod, op_name_lookup={}):
    return operators_for_dict(keyword_to_atom, mod.__dict__, op_name_lookup)
