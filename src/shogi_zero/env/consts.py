"""
constant parameter of shogi and SFEN

"""
PIECES = ["K", "R", "B", "G", "S", "N", "L", "P"] + \
    ["+R", "+B", "+S", "+N", "+L", "+P"] + \
    ["k", "r", "b", "g", "s", "n", "l", "p"] + \
    ["+r", "+b", "+s", "+n", "+l", "+p"]
NUM_PIECES = len(PIECES)
PICCES_IDX = {PIECES[i]: i for i in range(NUM_PIECES)}

HANDABLE_PIECES = ["R", "B", "G", "S", "N", "L", "P"] + \
    ["r", "b", "g", "s", "n", "l", "p"]

NUM_HANDABLE_PIECES = len(HANDABLE_PIECES)

HANDABLE_PIECES_IDX = {HANDABLE_PIECES[i]: i for i in range(NUM_HANDABLE_PIECES)}
