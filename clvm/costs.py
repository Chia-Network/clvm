IF_COST = 1
CONS_COST = 3
FIRST_COST = 1
REST_COST = 1
LISTP_COST = 1

ARITH_BASE_COST = 1
ARITH_COST_PER_LIMB_DIVIDER = 16
ARITH_COST_PER_ARG = 3

LOG_BASE_COST = 1
LOG_COST_PER_LIMB_DIVIDER = 16
LOG_COST_PER_ARG = 3

CMP_BASE_COST = 2
CMP_COST_PER_LIMB_DIVIDER = 64

GR_BASE_COST = 5
GR_COST_PER_LIMB_DIVIDER = 32

DIVMOD_BASE_COST = 11
DIVMOD_COST_PER_LIMB_DIVIDER = 16

DIV_BASE_COST = 9
DIV_COST_PER_LIMB_DIVIDER = 8

SHA256_BASE_COST = 2
SHA256_COST_PER_ARG = 2
SHA256_COST_PER_BYTE_DIVIDER = 16

POINT_ADD_BASE_COST = 316
POINT_ADD_COST_PER_ARG = 13600

PUBKEY_BASE_COST = 13600
PUBKEY_COST_PER_BYTE_DIVIDER = 8

MUL_BASE_COST = 1
MUL_COST_PER_OP = 8
MUL_LINEAR_COST_PER_BYTE_DIVIDER = 16
MUL_SQUARE_COST_PER_BYTE_DIVIDER = 16384

STRLEN_BASE_COST = 2
STRLEN_COST_PER_BYTE_DIVIDER = 128

PATH_LOOKUP_COST_PER_LEG = 1
PATH_LOOKUP_COST_PER_ZERO_BYTE = 1

CONCAT_BASE_COST = 1
CONCAT_COST_PER_ARG = 1
CONCAT_COST_PER_BYTE_DIVIDER = 16

BOOL_BASE_COST = 1
BOOL_COST_PER_ARG = 3

SHIFT_BASE_COST = 4
SHIFT_COST_PER_BYTE_DIVIDER = 16

LOGNOT_BASE_COST = 3
LOGNOT_COST_PER_BYTE_DIVIDER = 16

APPLY_COST = 1
QUOTE_COST = 1
