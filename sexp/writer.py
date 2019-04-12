# writer

import binascii


class bytes_as_hex(bytes):
    def as_hex(self):
        return binascii.hexlify(self).decode("utf8")

    def __str__(self):
        return "0x%s" % self.as_hex()

    def __repr__(self):
        return "0x%s" % self.as_hex()


# TODO: rewrite to take dump_atom, dump_list

def dump(form, keyword_from_int=[], is_first_element=False):
    if form.is_list():
        return "(%s)" % ' '.join(str(dump(f, keyword_from_int, _ == 0)) for _, f in enumerate(form))

    if form.is_var():
        return "x%d" % form.var_index()

    if is_first_element and 0 <= form.as_int() < len(keyword_from_int):
        v = keyword_from_int[form.as_int()]
        if v != '.':
            return v

    if len(form.as_bytes()) > 4:
        return bytes_as_hex(form.as_bytes())

    return str(form.as_int())


disassemble = dump
