from typing import Any, Callable, List, Tuple

from .casts import int_from_bytes
from .CLVMObject import CLVMObject
from .EvalError import EvalError
from .SExp import SExp

from .costs import (
    APPLY_COST,
    QUOTE_COST,
    PATH_LOOKUP_COST_PER_LEG
)

# the "Any" below should really be "OpStackType" but
# recursive types aren't supported by mypy

OpCallable = Callable[[Any, "ValStackType"], int]

ValStackType = List[SExp]
OpStackType = List[OpCallable]


def to_pre_eval_op(pre_eval_f, to_sexp_f):
    def my_pre_eval_op(op_stack: OpStackType, value_stack: ValStackType) -> None:
        v = to_sexp_f(value_stack[-1])
        context = pre_eval_f(v.first(), v.rest())
        if callable(context):

            def invoke_context_op(
                op_stack: OpStackType, value_stack: ValStackType
            ) -> int:
                context(to_sexp_f(value_stack[-1]))
                return 0

            op_stack.append(invoke_context_op)

    return my_pre_eval_op


def run_program(
    program: CLVMObject,
    args: CLVMObject,
    quote_kw: bytes,
    apply_kw: bytes,
    operator_lookup: Callable[[bytes, CLVMObject], Tuple[int, CLVMObject]],
    max_cost=None,
    pre_eval_f=None,
) -> Tuple[int, CLVMObject]:

    program = SExp.to(program)
    if pre_eval_f:
        pre_eval_op = to_pre_eval_op(pre_eval_f, program.to)
    else:
        pre_eval_op = None

    def traverse_path(sexp: SExp, env: SExp) -> Tuple[int, SExp]:
        cost = PATH_LOOKUP_COST_PER_LEG
        if sexp.nullp():
            return cost, sexp.null()
        node_index = int_from_bytes(sexp.atom)
        while node_index > 1:
            if env.pair is None:
                raise EvalError("path into atom", env)
            if node_index & 1:
                env = env.rest()
            else:
                env = env.first()
            cost += PATH_LOOKUP_COST_PER_LEG
            node_index >>= 1
        return cost, env

    def swap_op(op_stack: OpStackType, value_stack: ValStackType) -> int:
        v2 = value_stack.pop()
        v1 = value_stack.pop()
        value_stack.append(v2)
        value_stack.append(v1)
        return 0

    def cons_op(op_stack: OpStackType, value_stack: ValStackType) -> int:
        v1 = value_stack.pop()
        v2 = value_stack.pop()
        value_stack.append(v1.cons(v2))
        return 0

    def eval_op(op_stack: OpStackType, value_stack: ValStackType) -> int:
        if pre_eval_op:
            pre_eval_op(op_stack, value_stack)

        pair = value_stack.pop()
        sexp = pair.first()
        args = pair.rest()

        # put a bunch of ops on op_stack

        if sexp.pair is None:
            # sexp is an atom
            cost, r = traverse_path(sexp, args)
            value_stack.append(r)
            return cost

        operator = sexp.first()
        if operator.pair:
            value_stack.append(operator.cons(args))
            op_stack.append(eval_op)
            op_stack.append(eval_op)
            return 1

        op = operator.as_atom()
        operand_list = sexp.rest()
        if op == quote_kw:
            value_stack.append(operand_list)
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

    def apply_op(op_stack: OpStackType, value_stack: ValStackType) -> int:
        operand_list = value_stack.pop()
        operator = value_stack.pop()
        if operator.pair:
            raise EvalError("internal error", operator)

        op = operator.as_atom()
        if op == apply_kw:
            if operand_list.list_len() != 2:
                raise EvalError("apply requires exactly 2 parameters", operand_list)
            new_operator = operand_list.first()
            new_operand_list = operand_list.rest().first()
            if new_operator.pair:
                new_pair = new_operator.cons(new_operand_list)
                value_stack.append(new_pair)
                op_stack.append(eval_op)
            else:
                value_stack.append(new_operator)
                value_stack.append(new_operand_list)
                op_stack.append(apply_op)
            return APPLY_COST

        additional_cost, r = operator_lookup(op, operand_list)
        value_stack.append(r)
        return additional_cost

    op_stack: OpStackType = [eval_op]
    value_stack: ValStackType = [program.cons(args)]
    cost: int = 0

    while op_stack:
        f = op_stack.pop()
        cost += f(op_stack, value_stack)
        if max_cost and cost > max_cost:
            raise EvalError("cost exceeded", program.to(max_cost))
    return cost, value_stack[-1]
