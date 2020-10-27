use super::node::Node;
use super::operators::default_operator_lookup;
use super::pysexp::PySExp;
use super::run_program::run_program;
use super::serialize::{node_from_stream, node_to_stream};
use super::types::{
    EvalContext, EvalErr, FApply, OperatorFT, OperatorLookup, OperatorLookupT, Reduction,
};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use pyo3::wrap_pyfunction;
use pyo3::PyObject;
use std::io::Cursor;
use std::io::{Seek, SeekFrom, Write};

impl From<PyErr> for EvalErr {
    fn from(_err: PyErr) -> Self {
        EvalErr(Node::blob("PyErr"), "bad type from python call".to_string())
    }
}

fn node_from_bytes(b: &[u8]) -> std::io::Result<Node> {
    let mut buffer = Cursor::new(Vec::new());
    buffer.write_all(&b)?;
    buffer.seek(SeekFrom::Start(0))?;
    node_from_stream(&mut buffer)
}

fn node_to_bytes(node: &Node) -> std::io::Result<Vec<u8>> {
    let mut buffer = Cursor::new(Vec::new());

    node_to_stream(node, &mut buffer)?;
    let vec = buffer.into_inner();
    Ok(vec)
}

struct PyWrapApply {
    apply_f: PyObject,
}

impl PyWrapApply {
    fn inner_apply(
        &self,
        _eval_context: &EvalContext,
        operator: &Node,
        args: &Node,
    ) -> Result<Reduction, EvalErr> {
        let gil = Python::acquire_gil();
        let py = gil.python();
        let byte_vec: Vec<u8> = self
            .apply_f
            .call1(py, (node_to_bytes(&operator)?, node_to_bytes(&args)?))?
            .extract(py)?;
        let bytes: &[u8] = &byte_vec;
        Ok(Reduction(node_from_bytes(bytes)?, 1000))
    }
}

impl FApply for PyWrapApply {
    fn apply(
        &self,
        eval_context: &EvalContext,
        operator: &Node,
        args: &Node,
    ) -> Option<Result<Reduction, EvalErr>> {
        Some(self.inner_apply(eval_context, operator, args))
    }
}

//let env = node_from_bytes(env_u8.as_bytes())?;
//let f_table = make_f_lookup();

//let py_apply: Box<dyn FApply> = Box::new(PyWrapApply {apply_f});

/*
let pre_eval: PreEval = {
    if py_pre_eval.is_none(py) {
        None
    } else {
        Some(Box::new(
            move |sexp, args, current_cost, max_cost| -> Result<PostEval, EvalErr> {
                let py_post_eval: PyObject = py_pre_eval
                    .call1(
                        py,
                        (
                            node_to_bytes(&sexp)?,
                            node_to_bytes(&args)?,
                            current_cost,
                            max_cost,
                        ),
                    )?
                    .extract(py)?;
                Ok(wrap_py_post_eval(py, py_post_eval))
            },
        ))
    }
};
let pre_eval = None;
let r = run_program(
    &sexp, &env, 0, 100_000, &f_table, py_apply, pre_eval, op_quote, op_args,
);
match r {
    Ok(Reduction(node, cycles)) => Ok(("".into(), node_to_bytes(&node)?, cycles)),
    Err(EvalErr(node, err)) => Ok((err, node_to_bytes(&node)?, 0)),
}
*/

#[pyfunction]
fn test_run_program(program: &PySExp, args: &PySExp) -> PyResult<(String, PySExp, u32)> {
    let quote_kw: u8 = 1;
    let max_cost = 1 << 31;

    let r: Result<Reduction, EvalErr> = run_program(
        &program.node,
        &args.node,
        quote_kw,
        max_cost,
        default_operator_lookup(),
    );
    match r {
        Ok(reduction) => Ok(("worked".into(), reduction.0.into(), reduction.1)),
        Err(eval_err) => Ok((eval_err.1, eval_err.0.into(), 1)),
    }
}

#[pyclass(subclass, unsendable)]
pub struct PyOperatorLookup {
    pub val: OperatorLookup,
}

impl OperatorLookupT for PyOperatorLookup {
    fn f_for_operator(&self, op: &[u8]) -> Option<&Box<dyn OperatorFT>> {
        self.val.f_for_operator(op)
    }
}

//#[pyfunction]
fn py_run_program(
    program: &PySExp,
    args: &PySExp,
    quote_kw: u8,
    max_cost: u32,
    op_lookup: OperatorLookup,
) -> PyResult<(String, PySExp, u32)> {
    let r: Result<Reduction, EvalErr> =
        run_program(&program.node, &args.node, quote_kw, max_cost, op_lookup);
    match r {
        Ok(reduction) => Ok(("worked".into(), reduction.0.into(), reduction.1)),
        Err(eval_err) => Ok((eval_err.1, eval_err.0.into(), 1)),
    }
}

/// This module is a python module implemented in Rust.
#[pymodule]
fn clvm_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(test_run_program, m)?)
        .unwrap();
    //m.add_function(wrap_pyfunction!(py_run_program, m)?)
    //  .unwrap();
    m.add_class::<PySExp>()?;
    Ok(())
}
