"""
Various helper functions for working with the data used in this app
"""

import os
import json
from datetime import datetime
from glob import glob
from logging import getLogger

import shogi
#import pyperclip
from shogi_zero.config import ResourceConfig

logger = getLogger(__name__)


def pretty_print(env, colors):
    new_pgn = open("test3.txt", "at")
    game = {}
    game["SFEN"] = env.board.sfen()
    game["Result"] = env.result
    game["White"], game["Black"] = colors
    game["Date"] = datetime.now().strftime("%Y.%m.%d")
    new_pgn.write(json.dumps(game) + "\n\n")
    new_pgn.close()
    # pyperclip.copy(env.board.fen())


def find_kif_files(directory, pattern='*.kif'):
    dir_pattern = os.path.join(directory, pattern)
    files = list(sorted(glob(dir_pattern)))
    return files


def get_game_data_filenames(rc: ResourceConfig):
    pattern = os.path.join(rc.play_data_dir, rc.play_data_filename_tmpl % "*")
    files = list(sorted(glob(pattern)))
    return files


def get_next_generation_model_dirs(rc: ResourceConfig):
    dir_pattern = os.path.join(rc.next_generation_model_dir, rc.next_generation_model_dirname_tmpl % "*")
    dirs = list(sorted(glob(dir_pattern)))
    return dirs


def write_game_data_to_file(path, data):
    try:
        with open(path, "wt") as f:
            json.dump(data, f)
    except Exception as e:
        print(e)


def read_game_data_from_file(path):
    try:
        with open(path, "rt") as f:
            return json.load(f)
    except Exception as e:
        print(e)
