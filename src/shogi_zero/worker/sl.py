"""
Contains the worker for training the model using recorded game data rather than self-play
"""
import os
from collections import deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from logging import getLogger
from threading import Thread
from time import time

import shogi.KIF
from shogi_zero.agent.player_shogi import ShogiPlayer
from shogi_zero.config import Config
from shogi_zero.env.shogi_env import ShogiEnv, Winner
from shogi_zero.lib.data_helper import write_game_data_to_file, find_kif_files

logger = getLogger(__name__)


def start(config: Config):
    return SupervisedLearningWorker(config).start()


class SupervisedLearningWorker:
    """
    Worker which performs supervised learning on recorded games.

    Attributes:
        :ivar Config config: config for this worker
        :ivar list((str,list(float)) buffer: buffer containing the data to use for training -
            each entry contains a FEN encoded game state and a list where every index corresponds
            to a shogi move. The move that was taken in the actual game is given a value (based on
            the player elo), all other moves are given a 0.
    """

    def __init__(self, config: Config):
        """
        :param config:
        """
        self.config = config
        self.buffer = []

    def start(self):
        """
        Start the actual training.
        """
        start_time = time()

        def callback(res):
            env, data, game_id = res.result()
            if env is None:
                logger.info('invalid data: {}'.format(game_id))
                return

            self.save_data(data, game_id)
            logger.debug(f"game {game_id}"
                         f"halfmoves={env.num_halfmoves:3} {env.winner:12}"
                         f"{' by resign ' if env.resigned else '           '}"
                         f"{env.observation.split(' ')[0]}")

        with ProcessPoolExecutor(max_workers=3) as executor:
            games = self.get_games_from_all_files()

            # poisoned reference (memleak)
            for i, game in enumerate(games):
                job = executor.submit(get_buffer, self.config, game, len(games), i)
                job.add_done_callback(callback)
            # for res in as_completed([executor.submit(get_buffer, self.config, game, len(games), i) for i, game in enumerate(games)]):

    def get_games_from_all_files(self):
        """
        Loads game data from pgn files
        :return list(shogi.pgn.Game): the games
        """
        files = find_kif_files(self.config.resource.play_data_dir)
        logger.debug(files)
        games = []
        for filename in files:
            games.extend(self.get_games_from_file(filename))
        logger.debug("done reading")
        return games

    def save_data(self, data, game_id):
        rc = self.config.resource
        path = os.path.join(rc.play_data_dir, rc.play_data_filename_tmpl % game_id)
        logger.info(f"save play data to {path}")
        thread = Thread(target=write_game_data_to_file, args=(path, data))
        thread.start()

    def get_games_from_file(self, filename):
        """

        :param str filename: file containing the kif game data
        :return list(pgn.Game): shogi games in that file
        """
        kifs = shogi.KIF.Parser.parse_file(filename)
        game_id = filename.split('/')[-1].split('.')[0]
        rc = self.config.resource
        path = os.path.join(rc.play_data_dir, rc.play_data_filename_tmpl % game_id)
        if os.path.exists(path):
            return []

        for kif in kifs:
            kif["game_id"] = game_id
            kif["win"] = "w" if len(kif["moves"]) % 2 == 0 else "b"
        n = len(kifs)
        logger.debug(f"found {n} games in {filename}")
        return kifs


def get_buffer(config, game, tot_num, idx):
    try:
        return _get_buffer(config, game, tot_num, idx)
    except Exception:
        return None, None, game['game_id']


def _get_buffer(config, game, tot_num, idx):
    """
    Gets data to load into the buffer by playing a game using PGN data.
    :param Config config: config to use to play the game
    :param pgn.Game game: game to play
    :return list(str,list(float)): data from this game for the SupervisedLearningWorker.buffer
    """
    env = ShogiEnv().reset()
    white = ShogiPlayer(config, dummy=True)
    black = ShogiPlayer(config, dummy=True)
    for move in game["moves"]:
        if env.white_to_move:
            action = white.sl_action(env.observation, move)  # ignore=True
        else:
            action = black.sl_action(env.observation, move)  # ignore=True
        env.step(action, False)

    # this program define white as "Sente".
    if game['win'] == "b":
        env.winner = Winner.white
        black_win = -1
    elif game["win"] == "w":
        env.winner = Winner.black
        black_win = 1
    else:
        env.winner = Winner.draw
        black_win = 0

    black.finish_game(black_win)
    white.finish_game(-black_win)

    data = []
    for i in range(len(white.moves)):
        data.append(white.moves[i])
        if i < len(black.moves):
            data.append(black.moves[i])

    return env, data, game['game_id']
