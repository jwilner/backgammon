from unittest import TestCase
import backgammon.board

__author__ = 'jwilner'


class TestGetAllMoveSets(TestCase):
    def test_basic_case(self):
        spots = [0] * 26
        spots[20] = 1
        jail = ()
        side = backgammon.board.Side.WHITE
        remaining_dice = 5, 6

        all_move_sets = backgammon.board._get_all_move_sets(tuple(spots),
                                                            jail, side,
                                                            remaining_dice)

        print(all_move_sets)
