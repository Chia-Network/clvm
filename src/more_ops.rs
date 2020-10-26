use super::node::Node;
use super::number::Number;
use super::types::{EvalErr, Reduction};
use sha2::{Digest, Sha256};

pub fn op_sha256(args: &Node) -> Result<Reduction, EvalErr> {
    let mut hasher = Sha256::new();
    for arg in args.clone() {
        match arg.as_blob() {
            Some(blob) => hasher.input(blob),
            None => return args.err("atom expected"),
        }
    }
    Ok(Node::blob_u8(&hasher.result()).into())
}

pub fn sha256_tree(args: &Node) -> Box<[u8]> {
    let mut hasher = Sha256::new();
    if args.is_pair() {
        hasher.input([2]);
        hasher.input(sha256_tree(&args.first().unwrap()));
        hasher.input(sha256_tree(&args.rest().unwrap()));
    } else {
        hasher.input([1]);
        hasher.input(args.as_blob().unwrap());
    }

    let result = hasher.result();
    let v: Vec<u8> = result.into_iter().collect();
    v.into_boxed_slice()
}

pub fn op_sha256_tree(args: &Node) -> Result<Reduction, EvalErr> {
    let n: Node = args.first()?;
    Ok(Node::blob_u8(&sha256_tree(&n)).into())
}

pub fn op_add(args: &Node) -> Result<Reduction, EvalErr> {
    let mut total: Number = 0.into();
    for arg in args.clone() {
        let v: Option<Number> = Option::from(&arg);
        match v {
            Some(value) => total += value,
            None => return args.err("+ takes integer arguments"),
        }
    }
    let total: Node = total.into();
    Ok(total.into())
}

pub fn op_subtract(args: &Node) -> Result<Reduction, EvalErr> {
    let mut total: Number = 0.into();
    let mut is_first = true;
    for arg in args.clone() {
        let v: Option<Number> = Option::from(&arg);
        match v {
            Some(value) => {
                if is_first {
                    total += value;
                } else {
                    total -= value;
                };
                is_first = false;
            }
            None => return args.err("- takes integer arguments"),
        }
    }
    let total: Node = total.into();
    Ok(total.into())
}

pub fn op_multiply(args: &Node) -> Result<Reduction, EvalErr> {
    let mut total: Number = 1.into();
    for arg in args.clone() {
        let v: Option<Number> = Option::from(&arg);
        match v {
            Some(value) => total *= value,
            None => return args.err("* takes integer arguments"),
        }
    }
    let total: Node = total.into();
    Ok(total.into())
}

pub fn op_gr(args: &Node) -> Result<Reduction, EvalErr> {
    let a0 = args.first()?;
    let v0: Option<Number> = Option::from(&a0);
    let a1 = args.rest()?.first()?;
    let v1: Option<Number> = Option::from(&a1);
    if let Some(n0) = v0 {
        if let Some(n1) = v1 {
            return Ok(if n0 > n1 {
                Node::blob_u8(&[1]).into()
            } else {
                Node::null().into()
            });
        }
    }
    args.err("> on list")
}
