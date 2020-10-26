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

print()

from clvm import SExp


def try_it(code, args="0"):

    from clvm_tools import binutils

    program = SExp.to(binutils.assemble(code))
    args = SExp.to(binutils.assemble(args))
    err, r, cost = test_run_program(program, args)
    print(f"ERR= {err}")
    print(f"code = {code}")
    print(f"cost = {cost}")
    print(f"result = {binutils.disassemble(SExp.to(r))}")
    print()


try_it("(q (foo bar)))")
try_it("(f (q (foo bar))))")
try_it("(r (q (foo bar))))")
try_it("(f (r (q (foo bar)))))")
try_it("(sha256 (q foo)))")
try_it('(c (q 100) (q (200 300 400)))')
try_it('(+ 2 5)', '(500 600)')
try_it('(sha256 (f 1))', '("hello.there.my.dear.friend")')
try_it('(x (q 2000))')
try_it('(c (q (c (f 1) (q (105 200)))) (q (100 200)))')
try_it('((c (q (c (f 1) (q (105 200)))) (q (100 200))))')
try_it('((c (q ((c 2 (c 2 (c 5 (q ())))))) (c (q ((c (i (= 5 (q 1)) (q (q 1)) (q (* 5 ((c 2 (c 2 (c (- 5 (q 1)) (q ())))))))) 1))) 1)))', '(50)')
try_it('(q 2000 1))')
try_it('(q))')
