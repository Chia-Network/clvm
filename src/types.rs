use super::node::Node;

pub struct EvalContext {
    pub eval_f: FEval,
    pub eval_atom: FEval,
    pub apply_f: Box<dyn FApply>,
}

pub type FLookup = [Option<OperatorF>; 256];

#[derive(Debug, Clone)]
pub struct EvalErr(pub Node, pub String);

#[derive(Debug)]
pub struct Reduction(pub Node, pub u32);

pub type OpFn = fn(&Node) -> Result<Reduction, EvalErr>;

pub trait OperatorFT {
    fn apply_op(&self, node: &Node) -> Result<Reduction, EvalErr>;
}

pub type OperatorF = Box<dyn OperatorFT>;

pub trait OperatorLookupT {
    fn f_for_operator(&self, op: &[u8]) -> Option<&Box<dyn OperatorFT>>;
}

pub type OperatorLookup = Box<dyn OperatorLookupT>;

pub trait FApply {
    fn apply(
        &self,
        eval_context: &EvalContext,
        operator: &Node,
        args: &Node,
    ) -> Option<Result<Reduction, EvalErr>>;
}

pub type FEval =
    Box<dyn Fn(&EvalContext, &Node, &Node, u32, u32, u8, u8) -> Result<Reduction, EvalErr>>;

impl From<std::io::Error> for EvalErr {
    fn from(err: std::io::Error) -> Self {
        EvalErr(Node::blob("std::io::Error"), err.to_string())
    }
}

impl Node {
    pub fn err(&self, msg: &str) -> Result<Reduction, EvalErr> {
        Err(EvalErr(self.clone(), msg.into()))
    }

    pub fn node_err(&self, msg: &str) -> Result<Node, EvalErr> {
        Err(EvalErr(self.clone(), msg.into()))
    }

    pub fn u32_err(&self, msg: &str) -> Result<u32, EvalErr> {
        Err(EvalErr(self.clone(), msg.into()))
    }
}

impl From<Node> for Reduction {
    fn from(node: Node) -> Self {
        Reduction(node, 1)
    }
}
