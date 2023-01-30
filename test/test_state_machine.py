import unittest
from src.state_machine import DeterministicFiniteStateMachine


class TestStateMachine(unittest.TestCase):

    def setUp(self):
        self.state_machine = DeterministicFiniteStateMachine()

        self.state_machine.add_state(
            '0', is_terminal=True, is_initial=True
        )
        self.state_machine.add_state('1')
        self.state_machine.add_state('2')
        self.state_machine.add_state('3')

        self.state_machine.add_transition('0', '0', 0)
        self.state_machine.add_transition('0', '1', 1)
        self.state_machine.add_transition('0', '2', 2)
        self.state_machine.add_transition('1', '1', 0)
        self.state_machine.add_transition('1', '2', 1)
        self.state_machine.add_transition('1', '3', 2)
        self.state_machine.add_transition('2', '2', 0)
        self.state_machine.add_transition('2', '3', 1)
        self.state_machine.add_transition('2', '0', 2)
        self.state_machine.add_transition('3', '3', 0)
        self.state_machine.add_transition('3', '0', 1)
        self.state_machine.add_transition('3', '1', 2)

    def test_state_amount(self):
        self.assertEqual(self.state_machine.state_amount, 4)

    def test_transition_amount(self):
        self.assertEqual(self.state_machine.transition_amount, 12)

    def test_current_state(self):
        self.assertEqual(self.state_machine.current_state, '0')
        self.state_machine.feed(1)
        self.assertEqual(self.state_machine.current_state, '1')

    def test_is_terminated(self):
        self.state_machine.feed_many([2, 1, 1])
        self.assertTrue(self.state_machine.is_terminated)

    def test_is_initial(self):
        self.assertTrue(self.state_machine.is_initial)
        self.state_machine.feed_many([1, 1, 1, 1])
        self.assertTrue(self.state_machine.is_initial)

    def test_feed_count(self):
        self.assertEqual(self.state_machine.feed_count, 0)
        self.state_machine.feed_many([1, 1, 1, 42])
        self.assertEqual(self.state_machine.feed_count, 4)

    def test_transition_count(self):
        self.assertEqual(self.state_machine.transition_count, 0)
        self.state_machine.feed_many([1, 1, 1, 42])
        self.assertEqual(self.state_machine.transition_count, 3)

    def test_reset(self):
        self.state_machine.feed_many([1, 2, 42, 1, 1])
        self.state_machine.reset()
        self.assertTrue(self.state_machine.is_initial)
        self.assertEqual(self.state_machine.feed_count, 0)
        self.assertEqual(self.state_machine.transition_count, 0)

    def test_feed(self):
        self.assertTrue(self.state_machine.feed(1))

    def test_invalid_token(self):
        self.assertFalse(self.state_machine.feed(42))
