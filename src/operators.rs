use super::types::{FLookup, OperatorF};

use super::f_table::make_f_lookup;

pub fn default_operator_lookup(op: &[u8]) -> Option<OperatorF> {
    let lookup: FLookup = make_f_lookup();
    if op.len() == 1 {
        lookup[op[0] as usize]
    } else {
        None
    }
}
