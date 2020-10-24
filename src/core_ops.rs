use super::node::Node;
use super::types::{EvalErr, Reduction};

impl Node {
    pub fn first(&self) -> Result<Node, EvalErr> {
        match self.as_pair() {
            Some((a, _b)) => Ok(a),
            _ => self.node_err("first of non-cons"),
        }
    }

    pub fn rest(&self) -> Result<Node, EvalErr> {
        match self.as_pair() {
            Some((_a, b)) => Ok(b),
            _ => self.node_err("rest of non-cons"),
        }
    }
}

pub fn op_if(args: &Node) -> Result<Reduction, EvalErr> {
    let cond = args.first()?;
    let mut chosen_node = args.rest()?;
    if cond.nullp() {
        chosen_node = chosen_node.rest()?;
    }
    Ok(chosen_node.first()?.into())
}

pub fn op_cons(args: &Node) -> Result<Reduction, EvalErr> {
    let a1 = args.first()?;
    let a2 = args.rest()?.first()?;
    Ok(Node::pair(&a1, &a2).into())
}

pub fn op_first(args: &Node) -> Result<Reduction, EvalErr> {
    Ok(args.first()?.first()?.into())
}

pub fn op_rest(args: &Node) -> Result<Reduction, EvalErr> {
    Ok(args.first()?.rest()?.into())
}

pub fn op_listp(args: &Node) -> Result<Reduction, EvalErr> {
    match args.first()?.as_pair() {
        Some((_first, _rest)) => Ok(Node::from(1).into()),
        _ => Ok(Node::null().into()),
    }
}

pub fn op_raise(args: &Node) -> Result<Reduction, EvalErr> {
    args.err("clvm raise")
}

pub fn op_eq(args: &Node) -> Result<Reduction, EvalErr> {
    let a0 = args.first()?;
    let a1 = args.rest()?.first()?;
    if let Some(s0) = a0.as_atom() {
        if let Some(s1) = a1.as_atom() {
            if s0 == s1 {
                return Ok(Node::blob_u8(&[1]).into());
            }
            return Ok(Node::null().into());
        }
    }
    args.err("= on list")
}
