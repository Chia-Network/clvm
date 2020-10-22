use hex;

use super::eval::run_program;
use super::eval::{EvalContext, EvalErr, FApply, Reduction};
use super::f_table::make_f_lookup;
use super::node::Node;
use super::number::Number;
use super::serialize::node_from_stream;
use super::serialize::node_to_stream;
use std::io::Cursor;
use std::io::{Seek, SeekFrom, Write};

pub struct CustomApply {}

impl FApply for CustomApply {
    fn apply(
        &self,
        eval_context: &EvalContext,
        operator: &Node,
        args: &Node,
    ) -> Option<Result<Reduction, EvalErr>> {
        if let Some(blob) = operator.as_blob() {
            if let Ok(s) = String::from_utf8(blob.into()) {
                if s.eq_ignore_ascii_case("com") {
                    return Some(Ok(Node::blob("bwa ha ha").into()));
                }
            }
        }
        None
    }
}

pub fn fallback_apply(
    _eval_context: &EvalContext,
    op: &Node,
    _args: &Node,
) -> Result<Reduction, EvalErr> {
    if let Some(blob) = op.as_blob() {
        if let Ok(s) = String::from_utf8(blob.into()) {
            if s.eq_ignore_ascii_case("com") {
                return Ok(Node::blob("bwa ha ha").into());
            }
        }
    }
    op.err("unimplemented operator")
}

fn dump(n: &Node) {
    let mut buffer = Cursor::new(Vec::new());
    node_to_stream(n, &mut buffer).unwrap();
    let vec = buffer.into_inner();
    println!("n = {}; vec = {:?}", n, vec);
    let mut buff = Cursor::new(vec);
    let n1: Node = node_from_stream(&mut buff).unwrap();
    assert_eq!(*n, n1);
}

fn node_from_hex(the_hex: &str) -> Node {
    let mut buffer = Cursor::new(Vec::new());
    buffer.write_all(&hex::decode(the_hex).unwrap()).unwrap();
    buffer.seek(SeekFrom::Start(0)).unwrap();
    node_from_stream(&mut buffer).unwrap()
}

fn node_to_hex(node: &Node) -> String {
    let mut buffer = Cursor::new(Vec::new());

    node_to_stream(node, &mut buffer).unwrap();
    let vec = buffer.into_inner();
    hex::encode(vec)
}

#[test]
fn test_dump() {
    let n = Node::null();
    dump(&n);

    let n = Node::blob("foo");
    dump(&n);
    let n = Node::pair(&Node::blob("hello"), &Node::blob("foo"));
    dump(&n);

    for idx in 0..=255 {
        let n = Node::blob_u8(&[idx]);

        dump(&n);
    }

    let n: Node = 7.into();
    dump(&n);

    let n: Node = Number::from(1000).into();
    dump(&n);

    let v: Number = Option::from(&n).unwrap();
    println!("v = {:?}", v);
    dump(&n);

    let mut number: Number = Number::from(200_000);
    number *= Number::from(1_845_766_896);
    let n: Node = number.into();
    dump(&n);

    let v: Vec<Node> = vec![7.into(), 20.into(), 100.into()];
    let n: Node = Node::from_list(v);
    dump(&n);

    let v1: Vec<Node> = vec![7.into(), Node::blob_u8(b"foo bar baz")];
    let v: Vec<Node> = vec![Node::from_list(v1), 11.into(), 100.into()];
    let n: Node = Node::from_list(v);
    dump(&n);
}

fn do_run_program(form: &Node, env: &Node) -> Node {
    let f_table = make_f_lookup();
    let da = Box::new(fallback_apply);
    let op_quote = 1;
    let op_args = 3;
    let r = run_program(
        &form,
        &env,
        0,
        100_000,
        &f_table,
        Box::new(CustomApply {}),
        None,
        op_quote,
        op_args,
    );

    match r {
        Ok(Reduction(form, cost)) => {
            println!("cost is {:?}", cost);
            println!("form is {:?}", form);
            form
        }
        Err(e) => {
            println!("error is {:?}", e);
            assert!(false);
            form.clone()
        }
    }
}

fn do_test_run_program(input_as_hex: &str, expected_as_hex: &str) -> () {
    let null = Node::null();
    let n = node_from_hex(input_as_hex);
    println!("n = {:?}", n);
    let r = do_run_program(&n, &null);
    println!("r = {:?}", r);
    assert_eq!(node_to_hex(&r), expected_as_hex);
}

#[test]
fn test_eval() {
    // (q "hello") => "hello"
    do_test_run_program("ff01ff8568656c6c6f80", "8568656c6c6f");

    // (f (q ("hi" . "there"))) => "hi"
    do_test_run_program("ff06ffff01ffff8268698574686572658080", "826869");

    // (r (q ("hi" . "there"))) => "there"
    do_test_run_program("ff07ffff01ffff8268698574686572658080", "857468657265");

    // (c (q "hi") (q "there")) => ("hi" . "there")
    do_test_run_program(
        "ff05ffff01ff82686980ffff01ff8574686572658080",
        "ff826869857468657265",
    );

    // (f (c (q "hi") (q "there"))) => "hi"
    do_test_run_program(
        "ff06ffff05ffff01ff82686980ffff01ff857468657265808080",
        "826869",
    );

    // (i (q 0) (q 200) (q 300)) => 300
    do_test_run_program(
        "ff04ffff01ff8080ffff01ff8200c880ffff01ff82012c8080",
        "82012c",
    );

    // (i (q 1) (q 200) (q 300)) => 200
    do_test_run_program(
        "ff04ffff01ff0180ffff01ff8200c880ffff01ff82012c8080",
        "8200c8",
    );

    // (l (q 1)) => ()
    do_test_run_program("ff08ffff01ff018080", "80");

    // (l (q (50))) => ()
    do_test_run_program("ff08ffff01ffff32808080", "01");

    // (= (q 50) (q 50)) => 1
    do_test_run_program("ff0affff01ff3280ffff01ff328080", "01");

    // (= (q 50) (q 51)) => 1
    do_test_run_program("ff0affff01ff3280ffff01ff338080", "80");

    // (= (q 50) (q (51))) => RAISE
    //do_test_run_program("ff0affff01ff3280ffff01ffff33808080", "80");

    // (sha256 (q 100)) => 0x18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4
    do_test_run_program(
        "ff0bffff01ff648080",
        "a018ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4",
    );

    // (sha256 (q 100) (q 200)) => 0x091255b2ecc91f998e7db8da4fd5dbbe89b413c30c9766f579e20bf8be5b6a3f
    do_test_run_program(
        "ff0bffff01ff6480ffff01ff8200c88080",
        "a0091255b2ecc91f998e7db8da4fd5dbbe89b413c30c9766f579e20bf8be5b6a3f",
    );

    // (+ (q 100) (q 200)) => 300
    do_test_run_program("ff0cffff01ff6480ffff01ff8200c88080", "82012c");

    // (- (q 5000) (q 100) (q 44)) => 4856
    do_test_run_program("ff0dffff01ff82138880ffff01ff6480ffff01ff2c8080", "8212f8");

    // (* (q 111) (q 222)) => 24642
    do_test_run_program("ff0effff01ff6f80ffff01ff8200de8080", "826042");

    // ((q ((q 100))))
    do_test_run_program("ffff01ffffff01ff6480808080", "64");

    // (com (q "foo"))
    do_test_run_program("ff83636f6dffff01ff83666f6f8080", "89627761206861206861");
}
