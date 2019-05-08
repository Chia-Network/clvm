
class Node:
    def __init__(self, index=0):
        self._index = index

    @classmethod
    def node_for_list_index(class_, index, base_node=None):
        base_node = base_node or Node()
        return base_node.list_index(index)

    def list_index(self, index):
        node = self
        while index > 0:
            node = node.rest()
            index -= 1
        return node.first()

    def path_iter(self):
        """
        Yields 0s and 1s where 1 means "first" and 0 means "rest"
        """

        def iter(n):
            if n == 0:
                return
            yield from iter((n-1) >> 1)
            yield n & 1

        return iter(self._index)

    @classmethod
    def path_for_iter(class_, iter, base=None):
        base = base or ["args"]
        for direction in iter:
            if direction:
                base = ["first", base]
            else:
                base = ["rest", base]
        return base

    def path(self, base=None):
        """
        Generate code that drills down to correct args node.
        n: a path, where 0 means "here", 1 means "first", 2 mean "rest", 3 means "first first", etc.
        """
        return self.path_for_iter(self.path_iter(), base)

    def first(self):
        return self.__class__(self._index * 2 + 1)

    def rest(self):
        return self.__class__(self._index * 2 + 2)

    def up(self):
        return self.__class__((self._index - 1) >> 1)

    def reset_base(self, new_base):
        """
        Tweak node index where we assume the root node is now pushed down to the
        new_base node location.
        """
        r = new_base
        for d in self.path_iter():
            if d:
                r = r.first()
            else:
                r = r.rest()
        return r

    def __repr__(self):
        return "Node(%d)" % self._index
