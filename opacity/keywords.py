MORE_KEYWORDS = (
    ". choose1 aggsig point_add assert_output pubkey_for_exp and type equal "
    "sha256 reduce + * - / wrap unwrap list quote quasiquote unquote get env "
    "case is_atom list1 "
    "cons first rest list type is_null var apply eval "
    "macro_expand reduce_var reduce_bytes reduce_list if not bool or map "
    "get_raw env_raw has_unquote get_default "
    "first_true raise reduce_raw rewrite rewrite_op concat ").split()


KEYWORD_FROM_INT = [] + MORE_KEYWORDS

KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}
