import unittest
from src.state_machine import DeterministicFiniteStateMachine, TransitionEvent


class TestCallbacks(unittest.TestCase):

    def setUp(self):
        self.state_machine = DeterministicFiniteStateMachine()

        self.state_machine.add_state('x', is_initial=True)
        self.state_machine.add_state('a')
        self.state_machine.add_state('b', is_terminal=True)

        self.state_machine.add_transition('x', 'a', "a")
        self.state_machine.add_transition('a', 'a', "a")
        self.state_machine.add_transition('a', 'b', "b")
        self.state_machine.add_transition('b', 'a', "a")
        self.state_machine.add_transition('b', 'x', "b")

        self.callback_ids = []
        self.callback_called = False

        def append_callback_id(callback_id: str):
            self.callback_ids.append(callback_id)

        def append_callback_id_factory(callback_id: str):
            return lambda _: append_callback_id(callback_id)

        self.state_machine.bind_callback_at_exit(
            'a', append_callback_id_factory('exit')
        )
        self.state_machine.bind_callback_at_enter(
            'a', append_callback_id_factory('enter')
        )
        self.state_machine.bind_callback_at_transition(
            'a', "a", append_callback_id_factory('transition')
        )
        self.state_machine.bind_callback_at_enter_termination(
            append_callback_id_factory('enter_termination')
        )
        self.state_machine.bind_callback_at_exit_termination(
            append_callback_id_factory('exit_termination')
        )
        self.state_machine.bind_callback_at_enter_initial(
            append_callback_id_factory('enter_initial')
        )
        self.state_machine.bind_callback_at_exit_initial(
            append_callback_id_factory('exit_initial')
        )
        self.state_machine.bind_callback_always(
            append_callback_id_factory('always')
        )

    def test_exit(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed_many(['a', 'b'])
        self.assertIn('exit', self.callback_ids)

    def test_enter(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed_many(['a', 'b', 'a'])
        self.assertIn('enter', self.callback_ids)

    def test_transition(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed_many(['a', 'a'])
        self.assertIn('transition', self.callback_ids)

    def test_enter_termination(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed_many(['a', 'b'])
        self.assertIn('enter_termination', self.callback_ids)

    def test_exit_termination(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed_many(['a', 'b', 'b'])
        self.assertIn('exit_termination', self.callback_ids)

    def test_enter_initial(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed_many(['a', 'b', 'b'])
        self.assertIn('enter_initial', self.callback_ids)

    def test_exit_initial(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed('a')
        self.assertIn('exit_initial', self.callback_ids)

    def test_always(self):
        self.assertFalse(self.callback_ids)
        self.state_machine.feed_many(['a', 'b', 'a', 'b', 'a'])
        self.assertEqual(self.callback_ids.count('always'), 5)

    def test_bind_unbind(self):
        handle = self.state_machine.bind_callback_always(lambda _: ...)
        self.state_machine.unbind_callback_always(handle)

    def test_event(self):
        def event_handler(event: TransitionEvent):
            self.callback_called = True
            self.assertEqual(event.entered_state, 'b')
            self.assertEqual(event.exited_state, 'a')
            self.assertTrue(event.entered_state_is_terminal)
            self.assertEqual(event.token, "b")
            self.assertEqual(event.feed_count, 2)
            self.assertEqual(event.transition_count, 2)
            self.assertEqual(event.payload, "test_payload")

        self.state_machine.bind_callback_at_enter_termination(event_handler)

        self.state_machine.feed('a')
        self.state_machine.feed('b', payload="test_payload")

        self.assertTrue(self.callback_called)
