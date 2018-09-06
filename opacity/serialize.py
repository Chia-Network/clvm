import enum
import msgpack

from dataclasses import dataclass


@dataclass
class Var:
    index: int

    def __repr__(self):
        return "x%d" % self.index


def msgpack_types_to_cs_types(t):
    if isinstance(t, list):
        return [msgpack_types_to_cs_types(_) for _ in t]

    if isinstance(t, int):
        if t >= 0:
            try:
                return t
            except Exception:
                return b''
        else:
            return Var(-t-1)

    return bytes(t)


def cs_types_to_msgpack_types(t):
    if isinstance(t, list):
        return [cs_types_to_msgpack_types(_) for _ in t]

    if isinstance(t, int):
        return int(t)

    if isinstance(t, Var):
        return - t.index - 1

    return bytes(t)


def unwrap_blob(blob):
    return msgpack_types_to_cs_types(msgpack.loads(blob))


def wrap_blobs(blob_list):
    return msgpack.dumps(cs_types_to_msgpack_types(blob_list))
