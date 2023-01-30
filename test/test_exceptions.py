import unittest
from src.state_machine import DeterministicFiniteStateMachine


class UnhashableObject(list):
    pass


class TestExceptions(unittest.TestCase):

    def setUp(self):
        self.state_machine = DeterministicFiniteStateMachine(
            raise_on_invalid_token=True
        )

        self.state_machine.add_state('x', is_initial=True)
        self.state_machine.add_state('a')
        self.state_machine.add_state('b', is_terminal=True)

        self.state_machine.add_transition('x', 'a', "a")
        self.state_machine.add_transition('a', 'a', "a")
        self.state_machine.add_transition('a', 'b', "b")
        self.state_machine.add_transition('b', 'a', "a")
        self.state_machine.add_transition('b', 'x', "b")

    def test_invalid_token(self):
        self.assertRaises(ValueError, self.state_machine.feed, "z")

    def test_add_unhashable_state(self):
        self.assertRaises(
            TypeError, self.state_machine.add_state, UnhashableObject()
        )

    def test_add_existing_state(self):
        self.assertRaises(KeyError, self.state_machine.add_state, 'a')

    def test_add_second_initial_state(self):
        self.assertRaises(
            ValueError, self.state_machine.add_state, 'i', is_initial=True
        )

    def test_use_unhashable_state(self):
        self.assertRaises(
            TypeError, self.state_machine.add_transition,
            'a', UnhashableObject(), 'a'
        )

    def test_use_non_existing_state(self):
        self.assertRaises(
            KeyError, self.state_machine.add_transition, 'a', 'z', 'a'
        )

    def test_use_non_existing_transition(self):
        self.assertRaises(
            KeyError, self.state_machine.bind_callback_at_transition,
            'a', 'z', lambda: ...
        )

    def test_unbind_non_existing_handle(self):
        handle = self.state_machine.bind_callback_always(lambda: ...)
        self.assertRaises(
            KeyError, self.state_machine.unbind_callback_always, handle + 1
        )

    def test_unbind_unbound_handle(self):
        handle = self.state_machine.bind_callback_always(lambda: ...)
        self.state_machine.unbind_callback_always(handle)
        self.assertRaises(
            KeyError, self.state_machine.unbind_callback_always, handle
        )

    def test_no_initial_state(self):
        state_machine = DeterministicFiniteStateMachine()
        self.assertRaises(RuntimeError, state_machine.feed, 'a')

    def test_use_unhashable_token(self):
        self.assertRaises(
            TypeError, self.state_machine.feed, UnhashableObject()
        )

    def test_feed_non_matching_payload_amount(self):
        self.assertRaises(
            ValueError, self.state_machine.feed_many, ['a', 'b'], [0, 1, 2]
        )
