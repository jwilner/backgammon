"""
Board is a tuple of 28 ints, the sign of each int representing the side and
its absolute value representing the number present. If empty, the spot has 0.
"""
import functools
import random
import collections
import enum

__author__ = 'jwilner'

START_FROM_JAIL_FLAG = -1

DICE_CHOICES = tuple(range(1, 7))

NO_MOVE_EMPTY_SET = tuple()


class IllegalMoveException(Exception):
    pass


class Side(enum.Enum):
    # int value, home, jail start, cap method
    WHITE = 1, 25, 0, min
    BLACK = -1, 0, 25, max

    def __init__(self, token, home, jail_start, cap):
        """
        :type token: int
        :type home: int
        :type jail_start: int
        :type cap: (int) -> int
        """

        self.token = token
        self.direction = token
        self.home = home
        self.jail_start = jail_start
        self.cap_to_home = functools.partial(cap, home)

        first_spot = jail_start + self.direction
        inclusive_end = home + self.direction

        self.progression = tuple(range(first_spot, inclusive_end,
                                       self.direction))

    @property
    def other_side(self):
        """
        :rtype: Side
        """
        if self == Side.WHITE:
            return Side.BLACK
        else:
            return Side.WHITE

    def owns_spot(self, spot_value):
        """
        :type spot_value: int
        :rtype: bool
        """
        return spot_value != 0 and spot_value / abs(spot_value) == self.token


class MoveTuple(collections.namedtuple("MoveTuple", "side start die_roll")):
    @property
    def effective_end(self):
        """
        :rtype: int
        """
        return self.side.cap_to_home(self.effective_start + self.signed_roll)

    @property
    def signed_roll(self):
        """
        :rtype: int
        """
        return self.die_roll * self.side.direction

    @property
    def starts_in_jail(self):
        """
        :rtype: bool
        """
        return self.start == START_FROM_JAIL_FLAG

    @property
    def effective_start(self):
        """
        :rtype: int
        """
        return self.side.jail_start if self.starts_in_jail else self.start

    @property
    def direction(self):
        """
        :rtype: int
        """
        dist = self.effective_end - self.effective_start
        return dist / abs(dist)

    @property
    def uses_whole_roll(self):
        """
        :rtype: bool
        """
        return self.effective_distance == self.die_roll

    @property
    def effective_distance(self):
        """
        :rtype: int
        """
        return abs(self.effective_end - self.effective_start)


def play(spots, jail, side, move_set, rolled_dice):
    """
    :type spots: tuple[int]
    :type jail: ((int, int),)
    :type side: Side
    :type rolled_dice: tuple[int]
    :type move_set: tuple[MoveTuple]
    :rtype: tuple[int]
    """
    if not all(move.uses_whole_roll for move in move_set):
        # check uses the maximum available combination of dice
        optimal_moves = _get_all_optimal_moves(spots, jail, side, rolled_dice)
        if move_set not in optimal_moves:
            raise IllegalMoveException("More optimal moves existed.",
                                       optimal_moves)

    for move in move_set:
        spots, jail = _make_move(spots, jail, move)

    return spots, jail


def _make_move(spots, jail, move):
    """
    :type spots: tuple[int]
    :type jail: ((Side, int))
    :type move: MoveTuple
    :rtype: (tuple[int], ((Side, int)))
    """
    spots = list(spots)
    jail = dict(jail)

    if move.direction != move.side.direction:
        raise IllegalMoveException("Wrong direction", move)

    if move.effective_end == move.side.home and \
            not _all_in_last_quarter(spots, move.side):
        raise IllegalMoveException("Cannot move into home when all not in "
                                   "last quarter", move)

    # decrement starting point
    if not move.starts_in_jail:
        spots[move.effective_start] = \
            _decrement_for_side(spots[move.effective_start], move.side)
    else:
        jail[move.side] = _decrement_for_side(jail.get(move.side, 0), move.side)

    # handle any stomping
    other_side = move.side.other_side
    if other_side.owns_spot(spots[move.effective_end]):
        if not _is_stompable(spots[move.effective_end]):
            raise IllegalMoveException("Unstompable formation.", move.side,
                                       move.effective_start, move.effective_end)
        spots[move.effective_end] = \
            _decrement_for_side(spots[move.effective_end], other_side)
        jail[other_side] = _increment_for_side(jail.get(other_side, 0),
                                               other_side)

    spots[move.effective_end] = \
        _increment_for_side(spots[move.effective_end], move.side)

    return tuple(spots), tuple(jail.items())


def _get_all_move_sets(spots, jail, side, remaining_dice):
    """
    :type spots: tuple[int]
    :type jail: ((int, int),)
    :type side: Side
    :type remaining_dice: tuple[int]
    :rtype: tuple[tuple[MoveTuple]]
    """
    if not remaining_dice:
        return NO_MOVE_EMPTY_SET,

    start_spots = tuple(i for i, spot in zip(side.progression[-1:], spots)
                        if side.owns_spot(spot))

    if not start_spots:
        return NO_MOVE_EMPTY_SET,

    all_move_sets = ()
    for start_spot in start_spots:
        for die, other_dice in _get_die_and_other_dice(remaining_dice):
            try:
                move = MoveTuple(side=side, start=start_spot, die_roll=die)
                next_spots, next_jail = _make_move(spots, jail, move)
            except IllegalMoveException:
                continue
            else:
                move_sets = tuple((move,) + move_set for move_set in
                                  _get_all_move_sets(next_spots, next_jail,
                                                     side, other_dice))
                all_move_sets += move_sets

    return all_move_sets


def _get_all_optimal_moves(spots, jail, side, rolled_dice):
    """
    :type spots: tuple[int]
    :type jail: tuple[(Side, int)]
    :type side: Side
    :type rolled_dice: tuple[int]
    :rtype: set[tuple[MoveTuple]]
    """
    all_legal_move_sets = _get_all_move_sets(spots, jail, side, rolled_dice)
    ratings = tuple(sum(move.effective_distance for move in move_set)
                    for move_set in all_legal_move_sets)
    best_rating = max(ratings)
    return {move_set for move_set, rating
            in zip(all_legal_move_sets, ratings)
            if rating == best_rating}


def _is_stompable(spot_value):
    """
    :type spot_value: int
    :rtype: bool
    """
    return spot_value < 2


def roll_dice():
    """
    :rtype: tuple[int]
    """
    a, b = rolls = random.choice(DICE_CHOICES), random.choice(DICE_CHOICES)
    if a == b:
        rolls = rolls + rolls
    return tuple(sorted(rolls))


def _get_die_and_other_dice(dice):
    """
    :type dice: tuple[int]
    :rtype: __generator[int, tuple[int]]
    """
    for i, die in enumerate(dice):
        other_dice = dice[:i] + dice[i + 1:]
        yield die, other_dice


def _get_number_present(spot_value):
    """
    :type spot_value: int
    :rtype: int
    """
    return abs(spot_value)


def _increment_for_side(spot_value, side):
    """
    :type spot_value: int
    :type side: Side
    :rtype: int
    """
    if side.other_side.owns_spot(spot_value):
        raise ValueError("Cannot increment a spot for a side to which the spot"
                         "does not belong.")
    return spot_value + (1 * side.token)


def _decrement_for_side(spot_value, side):
    """
    :type spot_value: int
    :type side: Side
    :rtype: int
    """
    if not side.owns_spot(spot_value):
        raise ValueError("Cannot decrement a spot for a side to which the spot "
                         "doesn't belong.")
    return spot_value - (1 * side.token)


def _all_in_last_quarter(spots, side):
    """

    :type spots:
    :type side: Side
    :rtype: bool
    """
    first_three_quarters = (spots[i] for i in side.progression[:-7])
    return all(_get_number_present(spot_value) == 0
               for spot_value in first_three_quarters
               if side.owns_spot(spot_value))
