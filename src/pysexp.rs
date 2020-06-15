use super::sexp::Node;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyType};
use pyo3::wrap_pyfunction;

#[pyclass(name=Node)]
pub struct PySExp {
    node: Node,
}

#[pymethods]
impl PySExp {
    #[classmethod]
    fn from_bytes(_cls: &PyType, blob: &PyBytes) -> Self {
        Node::blob_u8(blob.as_bytes()).into()
    }

    #[classmethod]
    fn from_pair(_cls: &PyType, left: &PySExp, right: &PySExp) -> Self {
        Node::pair(&left.node, &right.node).into()
    }

    pub fn as_pair(&self) -> Option<(PySExp, PySExp)> {
        match self.node.as_pair() {
            None => None,
            Some(pair) => {
                let left = pair.0;
                let right = pair.1;
                let new_pair = (PySExp { node: left }, PySExp { node: right });
                Some(new_pair)
            }
        }
    }

    pub fn as_atom(&self) -> Option<&[u8]> {
        self.node.as_blob()
    }
}

impl From<Node> for PySExp {
    fn from(item: Node) -> PySExp {
        PySExp { node: item }
    }
}
