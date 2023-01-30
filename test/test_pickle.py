import os
import unittest
from tempfile import NamedTemporaryFile

from src.state_machine import DeterministicFiniteStateMachine


class TestPickle(unittest.TestCase):

    def setUp(self):
        self.state_machine = DeterministicFiniteStateMachine()

        self.state_machine.add_state('a', is_initial=True)
        self.state_machine.add_state('b', is_terminal=True)

        self.state_machine.add_transition('a', 'b', ...)
        self.state_machine.add_transition('b', 'a', ...)

        self.temp_filename = NamedTemporaryFile().name

    def tearDown(self):
        os.remove(self.temp_filename)

    def test_pickle(self):
        self.assertEqual(self.state_machine.current_state, 'a')
        self.state_machine.pickle_to_file(self.temp_filename)
        state_machine = DeterministicFiniteStateMachine.unpickle_from_file(
            self.temp_filename
        )
        self.assertEqual(state_machine.current_state, 'a')
        state_machine.feed('b')
        self.assertEqual(state_machine.current_state, 'b')
