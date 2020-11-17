def as_python(sexp):
    def _roll(op_stack, val_stack):
        v1 = val_stack.pop()
        v2 = val_stack.pop()
        val_stack.append(v1)
        val_stack.append(v2)

    def _make_tuple(op_stack, val_stack):
        left = val_stack.pop()
        right = val_stack.pop()
        if right == b"":
            val_stack.append([left])
        else:
            val_stack.append((left, right))

    def _extend_list(op_stack, val_stack):
        left = [val_stack.pop()]
        right = val_stack.pop()
        left.extend(right)
        val_stack.append(left)

    def _as_python(op_stack, val_stack):
        t = val_stack.pop()
        pair = t.as_pair()
        if pair:
            left, right = pair
            if right.listp():
                op_stack.append(_extend_list)
            else:
                op_stack.append(_make_tuple)
            op_stack.append(_as_python)
            op_stack.append(_roll)
            op_stack.append(_as_python)
            val_stack.append(left)
            val_stack.append(right)
        else:
            val_stack.append(t.as_atom())

    op_stack = [_as_python]
    val_stack = [sexp]
    while op_stack:
        op_f = op_stack.pop()
        op_f(op_stack, val_stack)
    return val_stack[-1]
