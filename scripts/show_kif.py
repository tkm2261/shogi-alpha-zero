import shogi.KIF
import shogi
id = 'f1713ccf39d839c4a82fdc2d6bd301e277271def'
a = shogi.KIF.Parser.parse_file('kif/{}.kif'.format(id))[0]

import pdb
pdb.set_trace()

board = shogi.Board()
for m in a['moves']:
    print(board.sfen())
    board.push_usi(m)
    hand = board.sfen().split()[2]
    if 'k' in hand or 'K' in hand:
        print(board)
