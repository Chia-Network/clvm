from .casts import limbs_for_int
from .EvalError import EvalError

QUOTE_COST = 1
SHIFT_COST_PER_LIMB = 1


def to_pre_eval_op(pre_eval_f):
    def my_pre_eval_op(op_stack, value_stack):
        v = value_stack[-1]
        context = pre_eval_f(v.first(), v.rest())
        if callable(context):

            def invoke_context_op(op_stack, value_stack):
                context(value_stack[-1])
                return 0

            op_stack.append(invoke_context_op)

    return my_pre_eval_op


def run_program(
    program,
    args,
    quote_kw,
    print_kw,
    operator_lookup,
    max_cost=None,
    pre_eval_op=None,
    pre_eval_f=None,
):
    if pre_eval_f:
        pre_eval_op = to_pre_eval_op(pre_eval_f)

    def eval_atom_op(op_stack, value_stack):
        pair = value_stack.pop()
        sexp = pair.first()
        env = pair.rest()
        node_index = sexp.as_int()
        cost = 1
        while node_index > 1:
            if node_index & 1:
                env = env.rest()
            else:
                env = env.first()
            cost += SHIFT_COST_PER_LIMB * limbs_for_int(node_index)
            node_index >>= 1
        value_stack.append(env)
        return cost

    def swap_op(op_stack, value_stack):
        v2 = value_stack.pop()
        v1 = value_stack.pop()
        value_stack.append(v2)
        value_stack.append(v1)
        return 0

    def cons_op(op_stack, value_stack):
        v1 = value_stack.pop()
        v2 = value_stack.pop()
        value_stack.append(v1.cons(v2))
        return 0

    def eval_op(op_stack, value_stack):
        if pre_eval_op:
            pre_eval_op(op_stack, value_stack)

        pair = value_stack.pop()
        sexp = pair.first()
        args = pair.rest()

        # put a bunch of ops on op_stack

        if not sexp.listp():
            # sexp is an atom
            op_stack.append(eval_atom_op)
            value_stack.append(pair)
            return 1

        operator = sexp.first()
        if operator.listp():
            value_stack.append(operator.cons(args))
            op_stack.append(eval_op)
            op_stack.append(eval_op)
            return 1

        op = operator.as_atom()
        operand_list = sexp.rest()

        if op == print_kw:
            print("sexp:", sexp)
            print("args:", args)
            print("argb:", args.as_bin())
            print("vals:", value_stack)
            print("--")

        if op == print_kw:
            op_stack.append(eval_op)
            value_stack.append(operand_list.first().cons(args))
            return 1

        if op == quote_kw:
            if operand_list.nullp() or not operand_list.rest().nullp():
                raise EvalError("quote requires exactly 1 parameter", sexp)
            value_stack.append(operand_list.first())
            return QUOTE_COST

        op_stack.append(apply_op)
        value_stack.append(operator)

        while not operand_list.nullp():
            _ = operand_list.first()
            value_stack.append(_.cons(args))
            op_stack.append(cons_op)
            op_stack.append(eval_op)
            op_stack.append(swap_op)
            operand_list = operand_list.rest()
        value_stack.append(operator.null())
        return 1

    def apply_op(op_stack, value_stack):
        operand_list = value_stack.pop()
        operator = value_stack.pop()
        if operator.listp():
            raise EvalError("internal error", operator)

        f = operator_lookup.get(operator.as_atom())
        if f is None:
            raise EvalError("unimplemented operator", operator)

        additional_cost, r = f(operand_list)
        value_stack.append(r)
        return additional_cost

    op_stack = [eval_op]
    value_stack = [program.cons(args)]
    cost = 0

    while op_stack:
        f = op_stack.pop()
        cost += f(op_stack, value_stack)
        if max_cost and cost > max_cost:
            raise EvalError("cost exceeded", value_stack[-1])
    return cost, value_stack[-1]
