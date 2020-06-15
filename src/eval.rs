use super::number::Number;
use super::sexp::Node;

pub struct EvalContext {
    pub eval_f: FEval,
    pub eval_atom: FEval,
    pub apply_f: Box<dyn FApply>,
}

#[derive(Debug, Clone)]
pub struct EvalErr(pub Node, pub String);

pub struct Reduction(pub Node, pub u32);

pub type OperatorF = fn(&Node) -> Result<Reduction, EvalErr>;

pub type FLookup = [Option<OperatorF>; 256];

impl From<std::io::Error> for EvalErr {
    fn from(err: std::io::Error) -> Self {
        EvalErr(Node::blob("std::io::Error"), err.to_string())
    }
}

impl From<Node> for Reduction {
    fn from(node: Node) -> Self {
        Reduction(node, 1)
    }
}

impl Node {
    pub fn err(&self, msg: &str) -> Result<Reduction, EvalErr> {
        Err(EvalErr(self.clone(), msg.into()))
    }

    pub fn node_err(&self, msg: &str) -> Result<Node, EvalErr> {
        Err(EvalErr(self.clone(), msg.into()))
    }
}

pub type FEval =
    Box<dyn Fn(&EvalContext, &Node, &Node, u32, u32, u8, u8) -> Result<Reduction, EvalErr>>;

pub type PreEval = Option<Box<dyn Fn(&Node, &Node, u32, u32) -> Result<PostEval, EvalErr>>>;
pub type PostEval = Option<Box<dyn Fn(&Node) -> ()>>;

pub fn default_eval_atom(
    _eval_context: &EvalContext,
    form: &Node,
    _env: &Node,
    _current_cost: u32,
    _max_cost: u32,
    _op_quote: u8,
    _op_args: u8,
) -> Result<Reduction, EvalErr> {
    form.err("not a list")
}

pub fn eval_atom_as_tree(
    _eval_context: &EvalContext,
    form: &Node,
    env: &Node,
    current_cost: u32,
    _max_cost: u32,
    _op_quote: u8,
    _op_args: u8,
) -> Result<Reduction, EvalErr> {
    let node_index: Option<Number> = form.into();
    let mut node_index: Number = node_index.unwrap();
    let mut cost = current_cost;
    let mut env: Node = env.clone();
    while node_index > (1).into() {
        let new_env = {
            if (node_index & (1).into()) == (1).into() {
                env.rest()?
            } else {
                env.first()?
            }
        };
        env = new_env;
        node_index >>= 1;
        cost += 1;
    }
    Ok(Reduction(env, cost))
}

pub fn default_eval(
    eval_context: &EvalContext,
    form: &Node,
    env: &Node,
    current_cost: u32,
    max_cost: u32,
    op_quote: u8,
    op_args: u8,
) -> Result<Reduction, EvalErr> {
    match form.as_pair() {
        None => (eval_context.eval_atom)(
            eval_context,
            form,
            env,
            current_cost,
            max_cost,
            op_quote,
            op_args,
        ),
        Some((left, right)) => {
            if left.is_pair() {
                let r = (eval_context.eval_f)(
                    &eval_context,
                    &left,
                    &env,
                    current_cost,
                    max_cost,
                    op_quote,
                    op_args,
                )?;
                match r {
                    Reduction(result, new_cost) => (eval_context.eval_f)(
                        eval_context,
                        &result.first()?,
                        &result.rest()?,
                        new_cost,
                        max_cost,
                        op_quote,
                        op_args,
                    ),
                }
            } else {
                let as_operator: Option<u8> = left.clone().into();
                if let Some(opcode) = as_operator {
                    if opcode == op_quote {
                        return {
                            let rest = form.rest()?;
                            if rest.nullp() || !rest.rest()?.nullp() {
                                form.err("quote requires exactly 1 parameter")
                            } else {
                                Ok(Reduction(right.first()?, current_cost + 1))
                            }
                        };
                    } else if opcode == op_args {
                        return Ok(Reduction(env.clone(), current_cost + 1));
                    }
                }
                let Reduction(params, new_cost) = eval_params(
                    &eval_context,
                    &form.rest()?,
                    &env,
                    current_cost,
                    max_cost,
                    op_quote,
                    op_args,
                )?;
                let r = eval_context.apply_f.apply(&eval_context, &left, &params);
                if r.is_none() {
                    return left.err("unknown operator");
                }
                let Reduction(r, apply_cost) = r.unwrap()?;

                Ok(Reduction(r, apply_cost + new_cost))
            }
        }
    }
}

fn eval_params(
    eval_context: &EvalContext,
    params: &Node,
    env: &Node,
    current_cost: u32,
    max_cost: u32,
    op_quote: u8,
    op_args: u8,
) -> Result<Reduction, EvalErr> {
    let mut new_cost = current_cost;
    let mut vec: Vec<Node> = Vec::new();
    for item in params.clone() {
        let r = (eval_context.eval_f)(
            &eval_context,
            &item,
            &env,
            new_cost,
            max_cost,
            op_quote,
            op_args,
        )?;
        vec.push(r.0);
        new_cost += r.1;
        if new_cost >= max_cost {
            return item.err("exceed max cost");
        }
    }
    Ok(Reduction(Node::from_list(vec), new_cost))
}

pub trait FApply {
    fn apply(
        &self,
        eval_context: &EvalContext,
        operator: &Node,
        args: &Node,
    ) -> Option<Result<Reduction, EvalErr>>;
}

pub struct SequentialApplies {
    apply_list: Vec<Box<dyn FApply>>,
}

pub fn make_sequential_applies<'a>(apply_f_list: Vec<Box<dyn FApply>>) -> SequentialApplies {
    return SequentialApplies {
        apply_list: apply_f_list,
    };
}

impl FApply for SequentialApplies {
    fn apply(
        &self,
        eval_context: &EvalContext,
        operator: &Node,
        args: &Node,
    ) -> Option<Result<Reduction, EvalErr>> {
        for apply_f in self.apply_list.iter() {
            let r = apply_f.apply(eval_context, operator, args);
            if r.is_some() {
                return r;
            }
        }
        None
    }
}

pub struct FTableApply {
    f_table: FLookup,
}

impl FApply for FTableApply {
    fn apply(
        &self,
        _eval_context: &EvalContext,
        operator: &Node,
        args: &Node,
    ) -> Option<Result<Reduction, EvalErr>> {
        let op_8: Option<u8> = operator.clone().into();
        let op_8 = op_8?;
        let f = self.f_table[op_8 as usize]?;
        Some(f(&args))
    }
}

pub fn make_default_eval_context(
    f_lookup: FLookup,
    apply_fallback: Box<dyn FApply>,
    pre_eval: PreEval,
) -> EvalContext {
    let eval_f: FEval = {
        match pre_eval {
            Some(pre_eval_f) => {
                let wrapped_eval: FEval = {
                    Box::new(
                        move |eval_context,
                              form,
                              env,
                              current_cost,
                              max_cost,
                              op_quote,
                              op_args|
                              -> Result<Reduction, EvalErr> {
                            let post_eval_f: PostEval =
                                pre_eval_f(form, env, current_cost, max_cost)?;
                            let r: Reduction = default_eval(
                                eval_context,
                                form,
                                env,
                                current_cost,
                                max_cost,
                                op_quote,
                                op_args,
                            )?;
                            match post_eval_f {
                                Some(f) => {
                                    f(&r.0);
                                }
                                None => (),
                            };
                            Ok(r)
                        },
                    )
                };
                Box::new(wrapped_eval)
            }
            None => Box::new(default_eval),
        }
    };

    let f1 = Box::new(FTableApply { f_table: f_lookup });
    let apply_f: Box<dyn FApply> = Box::new(make_sequential_applies(vec![f1, apply_fallback]));

    EvalContext {
        eval_f: eval_f,
        eval_atom: Box::new(eval_atom_as_tree),
        apply_f: apply_f,
    }
}

pub fn run_program(
    form: &Node,
    env: &Node,
    current_cost: u32,
    max_cost: u32,
    f_table: &FLookup,
    apply_fallback: Box<dyn FApply>,
    pre_eval: PreEval,
    op_quote: u8,
    op_args: u8,
) -> Result<Reduction, EvalErr> {
    let eval_context: EvalContext = make_default_eval_context(*f_table, apply_fallback, pre_eval);
    (eval_context.eval_f)(
        &eval_context,
        &form,
        &env,
        current_cost,
        max_cost,
        op_quote,
        op_args,
    )
}
