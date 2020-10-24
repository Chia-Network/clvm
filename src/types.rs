use super::node::Node;

pub struct EvalContext {
    pub eval_f: FEval,
    pub eval_atom: FEval,
    pub apply_f: Box<dyn FApply>,
}

pub type FLookup = [Option<OperatorF>; 256];

#[derive(Debug, Clone)]
pub struct EvalErr(pub Node, pub String);

pub struct Reduction(pub Node, pub u32);

pub type OperatorF = fn(&Node) -> Result<Reduction, EvalErr>;

pub type OperatorLookup = fn(&[u8]) -> Option<OperatorF>;

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
