use super::types::{FLookup, OperatorFT, OperatorLookupT};

//use super::f_table::make_f_lookup;

use super::core_ops::{op_cons, op_eq, op_first, op_if, op_listp, op_raise, op_rest};
use super::more_ops::{op_add, op_gr, op_multiply, op_sha256, op_sha256_tree, op_subtract};
use super::node::Node;
use super::types::{EvalErr, OpFn, Reduction};

static OPCODE_LOOKUP: [(u8, OpFn); 13] = [
    (4, op_if),
    (5, op_cons),
    (6, op_first),
    (7, op_rest),
    (8, op_listp),
    (9, op_raise),
    (10, op_eq),
    (11, op_sha256),
    (12, op_add),
    (13, op_subtract),
    (14, op_multiply),
    (21, op_sha256_tree),
    (22, op_gr),
];

/*
pub fn default_operator_lookup(op: &[u8]) -> Option<&Box<dyn OperatorFT>> {
    let lookup: FLookup = make_f_lookup();
    if op.len() == 1 {
        lookup[op[0] as usize]
    } else {
        None
    }
}
*/

struct OperatorFTCall {
    f: &'static OpFn,
}

impl OperatorFT for OperatorFTCall {
    fn apply_op(&self, node: &Node) -> Result<Reduction, EvalErr> {
        (self.f)(node)
    }
}
pub struct DefaultOperatorLookupT {
    vec: Vec<(u8, Box<dyn OperatorFT>)>,
}

impl DefaultOperatorLookupT {
    fn new() -> Self {
        let mut v: Vec<(u8, Box<dyn OperatorFT>)> = Vec::new();
        for (f_op, f) in &OPCODE_LOOKUP {
            let pair: (u8, Box<dyn OperatorFT>) = (*f_op, Box::new(OperatorFTCall { f }));
            v.push(pair);
        }
        DefaultOperatorLookupT { vec: v }
    }
}

impl OperatorLookupT for DefaultOperatorLookupT {
    fn f_for_operator(&self, op: &[u8]) -> Option<&Box<dyn OperatorFT>> {
        if op.len() == 1 {
            let c: u8 = op[0];
            for (f_op, f) in self.vec.iter() {
                if *f_op == c {
                    return Some(f);
                }
            }
        }
        None
    }
}

pub fn default_operator_lookup() -> Box<dyn OperatorLookupT> {
    Box::new(DefaultOperatorLookupT::new())
}
