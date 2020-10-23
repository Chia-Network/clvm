use std::fmt::{self, Display, Formatter};
use std::sync::Arc;

pub type Atom = Box<[u8]>;

#[derive(Debug, PartialEq)]
pub enum SExp {
    Atom(Atom),
    Pair(Node, Node),
}

#[derive(Debug, Clone, PartialEq)]
pub struct Node(pub Arc<SExp>);

impl Node {
    pub fn null() -> Self {
        Node::blob("")
    }

    pub fn blob(v: &str) -> Self {
        Node(Arc::new(SExp::Atom(Vec::from(v).into())))
    }

    pub fn blob_u8(v: &[u8]) -> Self {
        Node(Arc::new(SExp::Atom(Vec::from(v).into())))
    }

    pub fn pair(first: &Node, rest: &Node) -> Self {
        Node(Arc::new(SExp::Pair(first.clone(), rest.clone())))
    }

    pub fn from_list(nodes: Vec<Node>) -> Self {
        let iter = nodes.iter().rev();
        let mut last = Node::null();
        for v in iter {
            last = Node::pair(v, &last)
        }
        last
    }

    pub fn as_atom(&self) -> Option<&Atom> {
        let sexp: &SExp = &self.0;
        match sexp {
            SExp::Atom(a) => Some(a),
            _ => None,
        }
    }

    pub fn as_blob(&self) -> Option<&[u8]> {
        let sexp: &SExp = &self.0;
        match sexp {
            SExp::Atom(b) => Some(&b),
            _ => None,
        }
    }

    pub fn as_pair(&self) -> Option<(Node, Node)> {
        let sexp: &SExp = &self.0;
        match sexp {
            SExp::Pair(a, b) => Some((a.clone(), b.clone())),
            _ => None,
        }
    }

    pub fn is_pair(&self) -> bool {
        let sexp: &SExp = &self.0;
        matches!(sexp, SExp::Pair(_a, _b))
    }

    pub fn nullp(&self) -> bool {
        match self.as_blob() {
            Some(blob) => blob.is_empty(),
            None => false,
        }
    }

    pub fn sexp(&self) -> &SExp {
        &self.0
    }

    fn fmt_list(&self, f: &mut Formatter, is_first: bool) -> fmt::Result {
        if let Some((first, rest)) = self.as_pair() {
            if !is_first {
                write!(f, " ")?;
            }
            first.fmt(f)?;
            rest.fmt_list(f, false)
        } else {
            if !self.nullp() {
                write!(f, " . ")?;
                self.fmt(f)?;
            }
            Ok(())
        }
    }
}

impl Display for Node {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        if let Some(blob) = self.as_blob() {
            let t: &[u8] = &*blob;
            if t.is_empty() {
                write!(f, "()")?;
            } else {
                write!(f, "0x")?;
                for u in t {
                    write!(f, "{:02x}", u)?;
                }
            }
        }
        if let Some((_first, _rest)) = self.as_pair() {
            write!(f, "(")?;
            self.fmt_list(f, true)?;
            write!(f, ")")?;
        }

        Ok(())
    }
}

impl Iterator for Node {
    type Item = Node;

    fn next(&mut self) -> Option<Self::Item> {
        match &*self.0 {
            SExp::Pair(first, rest) => {
                let v = first.clone();
                self.0 = rest.0.clone();
                Some(v)
            }
            _ => None,
        }
    }
}

impl From<u8> for Node {
    fn from(item: u8) -> Self {
        let v: Vec<u8> = vec![item];
        Node(Arc::new(SExp::Atom(v.into())))
    }
}

impl From<Node> for Option<u8> {
    fn from(item: Node) -> Option<u8> {
        let blob = item.as_blob()?;
        let len = blob.len();
        if len == 0 {
            Some(0)
        } else if len == 1 {
            Some(blob[0])
        } else {
            None
        }
    }
}
