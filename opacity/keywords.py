KEYWORD_FROM_INT = (
    ". choose1 aggsig point_add assert_output pubkey_for_exp and type equal"
    " sha256 reduce + * - / wrap unwrap list quote quasiquote unquote get env").split()

KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}
