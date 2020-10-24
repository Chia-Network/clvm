use super::node::{Node, SExp};
use super::number::Number;
use super::operators::default_operator_lookup;
use super::types::OperatorLookup;

use super::types::{EvalErr, OperatorF, Reduction};

/*
#[derive(Debug, Clone)]
pub struct EvalErr(pub Node, pub String);

pub struct Reduction(pub Node, pub u32);

pub type OperatorF = fn(&Node) -> Result<Reduction, EvalErr>;

*/

// `run_program` has two stacks: the operand stack (of `Node` objects) and the
// operator stack (of RPOperators)
const QUOTE_COST: u32 = 1;

type RPCOperator = dyn FnOnce(&mut RunProgramContext) -> Result<u32, EvalErr>;

pub struct RunProgramContext {
    quote_kw: u8,
    operator_lookup: OperatorLookup,
    val_stack: Vec<Node>,
    op_stack: Vec<Box<RPCOperator>>,
}

impl RunProgramContext {
    pub fn pop(&mut self) -> Result<Node, EvalErr> {
        let v = self.val_stack.pop();
        match v {
            None => Node::null().node_err("runtime error: value stack empty"),
            Some(k) => Ok(k),
        }
    }
    pub fn push(&mut self, node: Node) {
        self.val_stack.push(node);
    }
}

pub fn traverse_path(path_node: &Node, args: &Node) -> Result<Reduction, EvalErr> {
    /*
    Follow integer `NodePath` down a tree.
    */
    let node_index: Option<Number> = path_node.into();
    let mut node_index: Number = node_index.unwrap();
    let one: Number = (1).into();
    let mut cost = 1;
    let mut arg_list: &Node = args;
    loop {
        println!("node_index = {:?}", node_index);
        println!("arg_list = {:?}", arg_list);
        if node_index <= one {
            break;
        }
        match arg_list.sexp() {
            SExp::Atom(_) => {
                println!("GOT AN ATOM");
                return Err(EvalErr(arg_list.clone(), "path into atom".into()));
            }
            SExp::Pair(left, right) => {
                if node_index & one == one {
                    println!("RIGHT")
                } else {
                    println!("LEFT")
                };
                arg_list = if node_index & one == one { right } else { left };
            }
        };
        cost = cost + 1; // SHIFT_COST_PER_LIMB * limbs_for_int(node_index)
        node_index >>= 1;
    }
    Ok(Reduction(arg_list.clone(), cost))
}

pub fn swap_op(rpc: &mut RunProgramContext) -> Result<u32, EvalErr> {
    /* Swap the top two operands. */
    let v2 = rpc.pop()?;
    let v1 = rpc.pop()?;
    rpc.push(v2);
    rpc.push(v1);
    Ok(0)
}

pub fn cons_op(rpc: &mut RunProgramContext) -> Result<u32, EvalErr> {
    /* Join the top two operands. */
    let v1 = rpc.pop()?;
    let v2 = rpc.pop()?;
    rpc.push(Node::pair(&v1, &v2));
    Ok(0)
}

pub fn eval_op(rpc: &mut RunProgramContext) -> Result<u32, EvalErr> {
    /*
    Pop the top value and treat it as a (program, args) pair, and manipulate
    the op & value stack to evaluate all the arguments and apply the operator.
    */
    let pair: Node = rpc.pop()?;
    match pair.sexp() {
        SExp::Atom(_) => pair.u32_err("pair expected"),
        SExp::Pair(program, args) => {
            // put a bunch of ops on op_stack
            match program.sexp() {
                // the program is just a bitfield path through the args tree
                SExp::Atom(as_atom) => {
                    let r: Reduction = traverse_path(&program, &args)?;
                    rpc.push(r.0);
                    Ok(r.1)
                }
                // the program is an operator and a list of operands
                SExp::Pair(operator_node, operand_list) => {
                    match operator_node.sexp() {
                        SExp::Pair(inner_program, _) => {
                            rpc.push(Node::pair(&inner_program, &args));
                            rpc.op_stack.push(Box::new(eval_op));
                            rpc.op_stack.push(Box::new(eval_op));
                            Ok(1)
                        }
                        SExp::Atom(op_as_atom) => {
                            // special case check for quote
                            if op_as_atom.len() == 1 && op_as_atom[0] == rpc.quote_kw {
                                match operand_list.sexp() {
                                    SExp::Atom(_) => {
                                        operand_list.u32_err("got atom, expected list")
                                    }
                                    SExp::Pair(quoted_val, nil) => {
                                        if nil.nullp() {
                                            rpc.push(quoted_val.clone());
                                            Ok(QUOTE_COST)
                                        } else {
                                            operand_list
                                                .u32_err("quote requires exactly 1 parameter")
                                        }
                                    }
                                }
                            } else {
                                rpc.op_stack.push(Box::new(apply_op));
                                rpc.push(operator_node.clone());
                                let mut operands = operand_list.clone();
                                loop {
                                    if operands.nullp() {
                                        break;
                                    }
                                    rpc.op_stack.push(Box::new(cons_op));
                                    rpc.op_stack.push(Box::new(cons_op));
                                    rpc.op_stack.push(Box::new(swap_op));
                                    match operands.sexp() {
                                        SExp::Atom(_) => {
                                            return Err(EvalErr(
                                                operand_list.clone(),
                                                "bad operand list".into(),
                                            ))
                                        }
                                        SExp::Pair(first, rest) => {
                                            rpc.push(first.clone());
                                            operands = rest.clone();
                                        }
                                    }
                                }
                                rpc.push(Node::null());
                                Ok(1)
                            }
                        }
                    }
                }
            }
        }
    }
}

pub fn apply_op(rpc: &mut RunProgramContext) -> Result<u32, EvalErr> {
    let operand_list = rpc.pop()?;
    let operator = rpc.pop()?;
    match operator.sexp() {
        SExp::Pair(p1, p2) => Err(EvalErr(operator, "internal error".into())),
        SExp::Atom(op_as_atom) => {
            let f = (rpc.operator_lookup)(&op_as_atom);
            match f {
                None => Err(EvalErr(operator, "unimplemented operator".into())),
                Some(f1) => {
                    let r: Reduction = f1(&operand_list)?;
                    rpc.push(r.0);
                    Ok(r.1)
                }
            }
        }
    }
}

pub fn run_program(
    program: &Node,
    args: &Node,
    quote_kw: u8,
    max_cost: u32,
    operator_lookup: OperatorLookup,
    //    f_table: &FLookup,
    //    apply_fallback: Box<dyn FApply>,
    //  pre_eval: PreEval,
) -> Result<Reduction, EvalErr> {
    let values: Vec<Node> = vec![Node::pair(program, args)];
    let op_stack: Vec<Box<RPCOperator>> = vec![Box::new(eval_op)];

    let mut rpc = RunProgramContext {
        quote_kw: quote_kw,
        operator_lookup: operator_lookup,
        val_stack: values,
        op_stack: op_stack,
    };

    let mut cost: u32 = 0;

    loop {
        if cost > max_cost {
            return Err(EvalErr(
                rpc.val_stack.pop().unwrap(),
                "cost exceeded".into(),
            ));
        }
        let top = rpc.op_stack.pop();
        match top {
            Some(f) => {
                cost += f(&mut rpc)?;
            }
            None => break,
        }
    }

    Ok(Reduction(rpc.pop()?, cost))
}
