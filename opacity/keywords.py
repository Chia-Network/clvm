KEYWORD_FROM_INT = (". choose1 aggsig point_add . pubkey_for_exp hash . equal sha256 reduce +").split()

KEYWORD_TO_INT = {v: k for k, v in enumerate(KEYWORD_FROM_INT)}
