"""
Encapsulates the functionality for representing
and operating on the shogi environment.
"""
import copy
import enum
from collections import defaultdict
import shogi
import numpy as np


from .consts import (
    # PIECES,
    NUM_PIECES,
    PICCES_IDX,
    # HANDABLE_PIECES,
    NUM_HANDABLE_PIECES,
    HANDABLE_PIECES_IDX,
)

from logging import getLogger
logger = getLogger(__name__)

Winner = enum.Enum("Winner", "black white draw")


class ShogiEnv:
    """
    Represents a shogi environment where a shogi game is played/

    Attributes:
        :ivar shogi.Board board: current board state
        :ivar int num_halfmoves: number of half moves performed in total by each player
        :ivar Winner winner: winner of the game
        :ivar boolean resigned: whether non-winner resigned
        :ivar str result: str encoding of the result, 1-0, 0-1, or 1/2-1/2
    """

    def __init__(self):
        self.board = None
        self.num_halfmoves = 0
        self.map_count_state = None
        self.winner = None  # type: Winner
        self.resigned = False
        self.result = None

    def reset(self):
        """
        Resets to begin a new game
        :return ShogiEnv: self
        """
        self.board = shogi.Board()
        self.num_halfmoves = 0
        self.map_count_state = defaultdict(int)
        self.map_count_state[self.board.sfen().split(" ")[0]] += 1
        self.winner = None
        self.resigned = False
        return self

    def update(self, board):
        """
        Like reset, but resets the position to whatever was supplied for board
        :param shogi.Board board: position to reset to
        :return ShogiEnv: self
        """
        self.board = shogi.Board(board)
        self.map_count_state = defaultdict(int)
        self.map_count_state[self.board.sfen().split(" ")[0]] += 1
        self.winner = None
        self.resigned = False
        return self

    @property
    def done(self):
        return self.winner is not None

    @property
    def white_won(self):
        return self.winner == Winner.white

    @property
    def white_to_move(self):
        return self.board.turn == 0

    def step(self, action: str, check_over=True):
        """

        Takes an action and updates the game state

        :param str action: action to take in usi notation
        :param boolean check_over: whether to check if game is over
        """
        if action is None:
            self._resign()
            return
        try:
            self.board.push_usi(action)
        except ValueError:
            self._resign()
            return
        board = self.board.sfen().split(" ")[0]
        self.map_count_state[board] += 1
        if self.map_count_state[board] >= 4:
            self.ending_average_game()
            return

        self.num_halfmoves += 1

    def _resign(self):
        self.resigned = True
        if self.white_to_move:  # WHITE RESIGNED!
            self.winner = Winner.black
            self.result = "0-1"
        else:
            self.winner = Winner.white
            self.result = "1-0"

    def adjudicate(self):
        self.winner = Winner.draw
        self.result = "1/2-1/2"

    def ending_average_game(self):
        self.winner = Winner.draw
        self.result = "1/2-1/2"

    def copy(self):
        env = copy.deepcopy(self)
        return env

    def render(self):
        print("\n")
        print(self.board)
        print("\n")

    @property
    def observation(self):
        return self.board.sfen()

    def deltamove(self, fen_next):
        moves = list(self.board.legal_moves)
        for mov in moves:
            self.board.push(mov)
            fee = self.board.sfen()
            self.board.pop()
            if fee == fen_next:
                return mov.usi()
        return None

    def canonical_input_planes(self):
        """

        :return: a representation of the board using an (?, 9, 9) shape, good as input to a policy / value network
        """
        sfen = self.board.sfen()
        sfen_info = SfenInfo(sfen)
        if not self.white_to_move:
            sfen_info = sfen_info.get_flipped_sfen_info()
        canonical_input = CanonicalInput(sfen_info, self.map_count_state[sfen_info.board])
        return canonical_input.create()


class SfenInfo:

    def __init__(self, sfen):

        self.sfen = sfen

        tmp = sfen.split(" ")
        self.board = tmp[0]
        self.turn = tmp[1]  # w or b
        self.hand = tmp[2]
        self.harf_turn_count = int(tmp[3])

        self._flipped_sfen_info = None

    def get_flipped_sfen_info(self):
        def swapcase(a):
            if a.isalpha():
                return a.lower() if a.isupper() else a.upper()
            return a

        def swapall(aa):
            return "".join([swapcase(a) for a in aa])

        tmp = self.sfen.split(" ")
        board = tmp[0]
        turn = tmp[1]
        hand = tmp[2]

        board = "/".join(swapall(row) for row in reversed(board.split("/")))
        turn = 'w' if turn == 'b' else 'b'
        hand = swapall(hand)

        flipped_sfen = " ".join([board, turn, hand] + tmp[3:])
        return SfenInfo(flipped_sfen)

    def get_indexed_board(self):
        indexed_board = np.zeros(81, dtype=np.uint8)
        ptr = 0
        cnt = 0
        while cnt < 81:
            if self.board[ptr].isdigit():
                cnt += int(self.board[ptr])
            elif self.board[ptr] == '/':
                pass
            else:
                piece = self.board[ptr]
                # promotion
                if piece == '+':
                    ptr += 1
                    piece += self.board[ptr]
                indexed_board[cnt] = PICCES_IDX[piece]
                cnt += 1
            ptr += 1

        return indexed_board.reshape((9, 9))

    def get_indexed_hand(self):
        indexed_hand = {}
        num = 1
        for s in self.hand:
            # no hand
            if s == '-':
                break

            if s.isdigit():
                num = int(s)
            else:
                indexed_hand[HANDABLE_PIECES_IDX[s]] = num
                num = 1

        return indexed_hand


class CanonicalInput:
    """
    Create canonical input (i.e. input to neural net model) from current SFEN

    Attributes:
        :ivar SfenInfo sfen: SFEN that keeps always player as a white player
    """

    def __init__(self, sfen_info, count_same_state):
        self.sfen_info = sfen_info
        self.count_same_state = count_same_state

    def create(self):
        """
        Create canonical input

        Attributes:
            :return : (?, 9, 9) representation of the game state
        """
        logger.debug("enter")
        board_features = self._create_board_features()
        hand_features = self._create_hand_features()
        game_features = self._create_game_features()

        all_features = np.vstack([board_features, hand_features, game_features])
        return all_features

    def _create_board_features(self):
        board_features = np.zeros((NUM_PIECES, 9, 9), dtype=np.float32)
        indexed_board = self.sfen_info.get_indexed_board()

        for i in range(9):
            for j in range(9):
                board_features[indexed_board[i, j], i, j] = 1

        return board_features

    def _create_hand_features(self):
        hand_features = np.zeros((NUM_HANDABLE_PIECES, 9, 9), dtype=np.float32)
        indexed_hand = self.sfen_info.get_indexed_hand()
        for piece, num in indexed_hand.items():
            hand_features[piece] = num
        return hand_features

    def _create_game_features(self):
        count_same_state_feature = np.full((9, 9), self.count_same_state, dtype=np.float32)
        #turn_feature = np.full((9, 9), self.sfen_info.turn == 'w', dtype=np.float32)
        turn_count_feature = np.full((9, 9), self.sfen_info.harf_turn_count, dtype=np.float32)
        return np.stack([count_same_state_feature, turn_count_feature])


'''
def check_current_planes(realfen, planes):
    cur = planes[0:12]
    assert cur.shape == (12, 9, 9)
    fakefen = ["1"] * 81
    for i in range(12):
        for rank in range(9):
            for file in range(9):
                if cur[i][rank][file] == 1:
                    assert fakefen[rank * 9 + file] == '1'
                    fakefen[rank * 9 + file] = pieces_order[i]

    castling = planes[12:16]
    fiftymove = planes[16][0][0]
    ep = planes[17]

    castlingstring = ""
    for i in range(4):
        if castling[i][0][0] == 1:
            castlingstring += castling_order[i]

    if len(castlingstring) == 0:
        castlingstring = '-'

    epstr = "-"
    for rank in range(8):
        for file in range(8):
            if ep[rank][file] == 1:
                epstr = coord_to_alg((rank, file))

    realfen = maybe_flip_fen(realfen, flip=is_black_turn(realfen))
    realparts = realfen.split(' ')
    assert realparts[1] == 'w'
    assert realparts[2] == castlingstring
    assert realparts[3] == epstr
    assert int(realparts[4]) == fiftymove
    # realparts[5] is the fifty-move clock, discard that
    return "".join(fakefen) == replace_tags_board(realfen)


'''
