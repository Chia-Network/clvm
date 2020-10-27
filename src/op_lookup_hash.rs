use super::types::{OperatorFT, OperatorLookupT};
use std::collections::HashMap;

pub struct Pair(Vec<u8>, Box<dyn OperatorFT>);

struct OpLookupHash {
    map: HashMap<Vec<u8>, Box<dyn OperatorFT>>,
}

impl OpLookupHash {
    fn new(pairs: Vec<Pair>) -> OpLookupHash {
        let mut map: HashMap<Vec<u8>, Box<dyn OperatorFT>> = HashMap::new();
        for pair in pairs.into_iter() {
            let name = pair.0;
            let func = pair.1;
            map.insert(name, func);
        }
        OpLookupHash { map }
    }
}

impl OperatorLookupT for OpLookupHash {
    fn f_for_operator(&self, op: &[u8]) -> Option<&Box<dyn OperatorFT>> {
        self.map.get(op)
    }
}
