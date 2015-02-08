import itertools

__author__ = 'jwilner'


class Game(object):
    def __init__(self, board, player_1, player_2):
        """
        :type board: T <= BaseBoard
        :type player_1: T <= BasePlayer
        :type player_2: T <= BasePlayer
        """
        self.board = board
        self.players = itertools.cycle([player_1, player_2])

