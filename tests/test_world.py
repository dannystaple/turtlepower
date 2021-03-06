import random
import sys

from mock import call, Mock, patch
from nose.plugins.skip import SkipTest
from nose.tools import assert_greater, eq_

from turtlepower.world import clamp, noisy, PowerTurtle, TurtleWorld, wrap


if sys.version_info[0] < 3:
    _super = '__builtin__.super'
else:
    _super = 'builtins.super'


def _make_mock_turtle(x, y):
    turtle = Mock()
    turtle.pos.return_value = (x, y)
    return turtle


@patch('turtlepower.world.TurtleScreen', Mock())
@patch('turtlepower.world.TK.Canvas', Mock())
@patch('turtlepower.world.Tk', Mock())
def _get_screenless_world():
    return TurtleWorld(10, 10)


def _bound_check(bound_func, before, expected):
    mock_turtle = _make_mock_turtle(*before)
    bound_func(mock_turtle, 10, 10)
    after_x, after_y = before
    if len(mock_turtle.setx.call_args_list):
        setx_args, _ = mock_turtle.setx.call_args
        after_x = setx_args[0]
    if len(mock_turtle.sety.call_args_list):
        sety_args, _ = mock_turtle.sety.call_args
        after_y = sety_args[0]
    eq_(expected, (after_x, after_y))


def _check_noisy(value, variance):
    results = [noisy(value, variance) for _ in range(1000)]
    lower_bound = value * (1 - variance)
    upper_bound = value * (1 + variance)
    for result in results:
        assert_greater(upper_bound, result)
        assert_greater(result, lower_bound)


def test_noisy():
    for value, variance in [(1, 0.01), (2, 0.01), (1, 1), (1000, 0.2)]:
        yield _check_noisy, value, variance


def test_wrap():
    # Assume a width and height of 10
    for before, expected in [
        ((0, 0), (0, 0)),  # Middle of screen
        ((-9, 2), (1, 2)),  # Off left
        ((9, 2), (-1, 2)),  # Off right
        ((2, -9), (2, 1)),  # Off bottom
        ((2, 9), (2, -1)),  # Off top
        ((-9, -9), (1, 1)),  # Off both
    ]:
        yield _bound_check, wrap, before, expected


def test_wrap_doesnt_put_the_pen_down_if_it_isnt_already_down():
    turtle = _make_mock_turtle(-9, -9)
    turtle.isdown.return_value = False
    wrap(turtle, 10, 10)
    eq_(0, turtle.pendown.call_count)


def test_wrap_puts_the_pen_down_if_it_was_already_down():
    turtle = _make_mock_turtle(-9, -9)
    turtle.isdown.return_value = True
    wrap(turtle, 10, 10)
    eq_(1, turtle.pendown.call_count)


def test_clamp():
    # Assume a width and height of 10
    for before, expected in [
        ((0, 0), (0, 0)),  # Middle of screen
        ((-9, 2), (-5, 2)),  # Off left
        ((9, 2), (5, 2)),  # Off right
        ((2, -9), (2, -5)),  # Off bottom
        ((2, 9), (2, 5)),  # Off top
        ((-9, -9), (-5, -5)),  # Off both
    ]:
        yield _bound_check, clamp, before, expected


class TestTurtleWorld(object):

    def test_add_turtle_means_a_turtle_receives_ticks(self):
        world = _get_screenless_world()
        world.ticks = 0
        turtle = _make_mock_turtle(0, 0)
        world.tick()
        eq_(0, turtle.callback.call_count)
        world.add_turtle(turtle)
        world.tick()
        eq_(1, turtle.callback.call_count)

    def test_create_turtle_means_a_turtle_receives_ticks(self):
        raise SkipTest

    @patch('turtlepower.world.PowerTurtle')
    def test_create_turtle_places_turtle(self, power_turtle):
        world = _get_screenless_world()
        world.position_turtle = Mock()
        x, y, angle = 1, 2, 3
        world.create_turtle(Mock(), (x, y), angle)
        eq_([call(power_turtle.return_value, (x, y), angle)],
            world.position_turtle.call_args_list)

    @patch('turtlepower.world.PowerTurtle')
    def test_create_turtle_returns_turtle(self, power_turtle):
        world = _get_screenless_world()
        created_turtle = world.create_turtle(Mock(), (0, 0), 0)
        eq_(power_turtle.return_value, created_turtle)

    @patch('turtlepower.world.PowerTurtle')
    def test_create_turtle_defaults_to_random_position(self, power_turtle):
        world = _get_screenless_world()
        world.position_turtle = Mock()
        world.create_turtle(Mock())
        eq_([call(power_turtle.return_value, None, None)],
            world.position_turtle.call_args_list)

    def test_position_turtle_uses_parameters(self):
        turtle = _make_mock_turtle(0, 0)
        world = _get_screenless_world()
        x, y, angle = 1, 2, 3
        world.position_turtle(turtle, (x, y), angle)
        eq_([call(x, y)], turtle.goto.call_args_list)
        eq_([call(angle)], turtle.setheading.call_args_list)

    @patch('turtlepower.world.randint')
    @patch('turtlepower.world.random')
    def test_position_turtle_defaults_to_random_position(
            self, random, randint):
        randint.side_effect = [1, 1, 3, 2, 5, 5]
        random.side_effect = [0.0, 0.5]
        turtle = _make_mock_turtle(0, 0)
        world = _get_screenless_world()
        world.position_turtle(turtle)
        world.position_turtle(turtle)
        eq_([call(1, 1), call(3, 2)], turtle.goto.call_args_list)
        eq_([call(0.0), call(180.0)],
            turtle.setheading.call_args_list)

    def test_random_position_uses_position_turtle(self):
        turtle = Mock()
        world = _get_screenless_world()
        world.position_turtle = Mock()
        world.random_position(turtle)
        eq_([call(turtle)], world.position_turtle.call_args_list)

    def test_remove_turtle_stops_a_turtle_from_receiving_ticks(self):
        raise SkipTest

    def test_tick_calls_all_turtle_callbacks(self):
        world = _get_screenless_world()
        world.ticks = 0
        world.turtles = [_make_mock_turtle(0, 0) for _ in range(3)]
        world.tick()
        for turtle in world.turtles:
            eq_([call(world)], turtle.callback.call_args_list)

    def test_tick_calls_borders_for_each_turtle(self):
        raise SkipTest


@patch(_super, Mock())
def _turn_towards_check(current_heading, desired_heading, amount,
                        expected_amount):
    turtle = PowerTurtle(Mock())
    turtle.left = Mock()
    turtle.heading = Mock(return_value=current_heading)
    actual_amount = turtle.turn_towards(desired_heading, amount)
    eq_([call(expected_amount)], turtle.left.call_args_list)
    eq_(expected_amount, actual_amount)


def test_turn_towards():
    test_cases = [
        # current_heading, desired_heading, amount, expected_amount
        (0, 0, 2, 0),  # no change
        (0, 1, 2, 1),  # positive change within maximum
        (0, 4, 3, 3),  # positive change hitting bounding
        (0, -1, 2, -1),  # negative change within maximum
        (0, -4, 3, -3),  # negative change hitting bounding
        # non-zero current heading
        (100, 101, 2, 1),  # positive change within maximum
        (100, 104, 3, 3),  # positive change hitting bounding
        (100, 99, 2, -1),  # negative change within maximum
        (100, 96, 3, -3),  # negative change hitting bounding
    ]
    for current, desired, amount, expected in test_cases:
        yield _turn_towards_check, current, desired, amount, expected
