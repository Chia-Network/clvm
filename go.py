from clvm_rust import PySExp as Node, test_run_program

if 1:
    n = Node(b"foo")
    print(n)
    print(n.as_atom())

    n0 = Node((n, n))
    print(n0)
    print(n0.as_pair())


class MyNode(Node):
    def __new__(cls, *args, **kwargs):
        return super(MyNode, cls).__new__(cls, *args)

    def __str__(self):
        return "OH YEAH?"

    def __repr__(self):
        return "OH YEAH"


m = MyNode(b"foo")
assert str(m) == "OH YEAH?"


for _ in [50, 38947474]:
    s = Node(b"foo")
    print(s)
    print(s.as_atom())

s0 = Node(b"left")
s1 = MyNode(b"right")
s2 = Node((s0, s1))
print(f"s1 = {s1}")
print(s2)

t1 = s2.as_pair()
print(t1)
print(t1[0].as_atom())
print(t1[1].as_atom())

prog = Node(bytes([4]))
args = Node((Node(b"hi"), Node(b"hello")))
t = test_run_program(prog, args)
print(t)
n = t[1]
print(n.as_atom())
print()
tree = Node((args, args))
t = test_run_program(prog, tree)
print(t)
n = t[1]
print(n.as_atom())
