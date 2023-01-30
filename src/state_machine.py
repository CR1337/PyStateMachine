from itertools import chain
from dataclasses import dataclass
import pickle
from typing import Any, Callable, Dict, Hashable, Iterable, List, Tuple


class TransitionEvent:

    _entered_state: Hashable
    _exited_state: Hashable
    _entered_state_is_terminal: bool
    _token: Hashable
    _feed_count: int
    _transition_count: int
    _payload: Any

    def __init__(
        self, entered_state: Hashable, exited_state: Hashable, token: Hashable,
        is_terminal: bool, feed_count: int, transition_count: int,
        payload: Any
    ):
        self._entered_state = entered_state
        self._exited_state = exited_state
        self._entered_state_is_terminal = is_terminal
        self._token = token
        self._feed_count = feed_count
        self._transition_count = transition_count
        self._payload = payload

    @property
    def entered_state(self) -> Hashable:
        """The state entered after the transition.

        Returns:
            Hashable: state after the transition
        """
        return self._entered_state

    @property
    def exited_state(self) -> Hashable:
        """The state exited due to the transition.

        Returns:
            Hashable: state exited
        """
        return self._exited_state

    @property
    def entered_state_is_terminal(self) -> bool:
        """Wether the entered state is a terminal state.

        Returns:
            bool: True if entered state is terminal, else False
        """
        return self._entered_state_is_terminal

    @property
    def token(self) -> Hashable:
        """The token that caused the transition.

        Returns:
            Hashable: token that caused the transition
        """
        return self._token

    @property
    def feed_count(self) -> int:
        """How many feeds already occurred.

        Returns:
            int: count of feed calls so far
        """
        return self._feed_count

    @property
    def transition_count(self) -> int:
        """"How many transitions already occurred.

        Returns:
            int: count of transitions so far
        """
        return self._transition_count

    @property
    def payload(self) -> Any:
        """The optional payload feed to the state machine.

        Returns:
            Any: optional payload
        """
        return self._payload


@dataclass
class _PicklableDeterministicFiniteStateMachine:

    _is_terminal: Dict[Hashable, bool]
    _transitions: Dict[Tuple[Hashable, Hashable], Hashable]

    _initial_state: Hashable
    _current_state: Hashable

    _feed_count: int
    _transition_count: int

    _raise_on_invalid_token: bool

    @classmethod
    def from_state_machine(
        cls, state_machine: 'DeterministicFiniteStateMachine'
    ) -> '_PicklableDeterministicFiniteStateMachine':
        return cls(
            state_machine._is_terminal,
            state_machine._transitions,
            state_machine._initial_state,
            state_machine._current_state,
            state_machine._feed_count,
            state_machine._transition_count,
            state_machine._raise_on_invalid_token
        )

    def pickle_to_file(self, filename: str, protocol: int = None):
        with open(filename, 'wb') as file:
            pickle.dump(self, file, protocol)

    @classmethod
    def unpickle_from_file(
        cls, filename: str
    ) -> '_PicklableDeterministicFiniteStateMachine':
        with open(filename, 'rb') as file:
            return pickle.load(file)

    def to_state_machine(self) -> 'DeterministicFiniteStateMachine':
        state_machine = DeterministicFiniteStateMachine()
        state_machine._is_terminal = self._is_terminal
        state_machine._transitions = self._transitions
        state_machine._initial_state = self._initial_state
        state_machine._current_state = self._current_state
        state_machine._feed_count = self._feed_count
        state_machine._transition_count = self._transition_count
        state_machine._raise_on_invalid_token = self._raise_on_invalid_token

        for state in self._is_terminal:
            state_machine._enter_callbacks[state] = {}
            state_machine._exit_callbacks[state] = {}

        for transition in self._transitions:
            state_machine._transition_callbacks[transition] = {}

        return state_machine


class DeterministicFiniteStateMachine:

    _is_terminal: Dict[Hashable, bool]
    _transitions: Dict[Tuple[Hashable, Hashable], Hashable]

    _exit_callbacks: Dict[
        Hashable,
        Dict[int, Callable[[TransitionEvent], None]]
    ]
    _enter_callbacks: Dict[
        Hashable,
        Dict[int, Callable[[TransitionEvent], None]]
    ]
    _transition_callbacks: Dict[
        Tuple[Hashable, Hashable],
        Dict[int, Callable[[TransitionEvent], None]]
    ]
    _enter_termination_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _exit_termination_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _enter_initial_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _exit_initial_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _always_callbacks: Dict[int, Callable[[TransitionEvent], None]]

    _initial_state: Hashable
    _current_state: Hashable

    _feed_count: int
    _transition_count: int
    _next_handle: int

    _raise_on_invalid_token: bool

    @staticmethod
    def unpickle_from_file(filename: str) -> 'DeterministicFiniteStateMachine':
        """Create a DeterministicFiniteStateMachine from a pickle file.

        Args:
            filename (str): filename of the pickle file

        Returns:
            DeterministicFiniteStateMachine: pickled state machine
        """
        picklable_state_machine = (
            _PicklableDeterministicFiniteStateMachine.unpickle_from_file(
                filename
            )
        )
        return picklable_state_machine.to_state_machine()

    def pickle_to_file(self, filename: str, protocol: int = None):
        """Pickle the state machine to a file. Note that callbacks are not
        pickled and all states and transitions passed to the state machine
        have to be picklable.

        Args:
            filename (str): filename to pickle to
            protocol (int, optional): pickle protocol. Defaults to None.
        """
        picklable_state_machine = (
            _PicklableDeterministicFiniteStateMachine.from_state_machine(self)
        )
        picklable_state_machine.pickle_to_file(filename, protocol)

    def __init__(self, raise_on_invalid_token: bool = False):
        """Initialize a state machine.

        Args:
            raise_on_invalid_token (bool, optional):
            wether to raise an exception when an invalid token is fedd.
            Defaults to False.
        """
        self._is_terminal = {}
        self._transitions = {}

        self._exit_callbacks = {}
        self._enter_callbacks = {}
        self._transition_callbacks = {}
        self._enter_termination_callbacks = {}
        self._exit_termination_callbacks = {}
        self._enter_initial_callbacks = {}
        self._exit_initial_callbacks = {}
        self._always_callbacks = {}

        self._initial_state = None
        self._current_state = None

        self._feed_count = 0
        self._transition_count = 0
        self._next_handle = 0

        self._raise_on_invalid_token = raise_on_invalid_token

    def _raise_on_state(self, state: Hashable):
        if not isinstance(state, Hashable):
            raise TypeError(f"State '{state}' has to be hashable!")
        if state not in self._is_terminal:
            raise KeyError(f"State '{state}' does not exist!")

    def _raise_on_transition(self, state: Hashable, token: Hashable):
        self._raise_on_state(state)
        self._raise_on_token(token)
        if (state, token) not in self._transitions:
            raise KeyError(
                f"A transition '{state} --({token})--> ...' does not exists!"
            )

    def _raise_on_token(self, token: Hashable):
        if not isinstance(token, Hashable):
            raise TypeError(f"Token '{token}' has to be hashable!")

    def add_state(
        self, state: Hashable, is_terminal: bool = False, is_initial: bool = False
    ):
        """Adds a state to ste state machine.

        Args:
            state (Hashable): the state
            is_terminal (bool, optional): wether it is terminal.
            Defaults to False.
            is_initial (bool, optional): wether it is initial.
            Defaults to False.

        Raises:
            TypeError: when state is not hashable
            KeyError: when state already exists
            ValueError: when is_initial is True but there already is
            an initial state
        """
        if not isinstance(state, Hashable):
            raise TypeError(f"State '{state}' has to be hashable!")
        if state in self._is_terminal:
            raise KeyError(f"State '{state}' already exists!")
        if is_initial and self._initial_state is not None:
            raise ValueError(
                f"There is already an initial state: '{self._initial_state}'!"
            )
        self._is_terminal[state] = is_terminal
        if is_initial:
            self._initial_state = state
            self._current_state = state
        self._enter_callbacks[state] = {}
        self._exit_callbacks[state] = {}

    def add_transition(
        self, exited_state: Hashable, entered_state: Hashable, token: Hashable
    ):
        """Adds a transition to the state machine.

        Args:
            exited_state (Hashable): state exited due to the transition
            entered_state (Hashable): state entered after the transition
            token (Hashable): token triggering the transition

        Raises:
            KeyError: when transition already exists
        """
        self._raise_on_state(exited_state)
        self._raise_on_state(entered_state)
        if (exited_state, token) in self._transitions:
            raise KeyError(
                f"A transition '{exited_state} --({token})--> ...' "
                "already exists!"
            )
        self._transitions[(exited_state, token)] = entered_state
        self._transition_callbacks[(exited_state, token)] = {}

    def _bind_callback(
        self,
        callbacks: Dict[int, Callable[[TransitionEvent], None]],
        callback: Callable[[TransitionEvent], None]
    ) -> int:
        callbacks[self._next_handle] = callback
        self._next_handle += 1
        return self._next_handle - 1

    def _unbind_callback(
        self, callbacks: Dict[int, Callable[[TransitionEvent], None]],
        handle: int
    ):
        if handle not in callbacks:
            raise KeyError(f"Handle '{handle}' does not exist!")
        del callbacks[handle]

    def bind_callback_at_enter(
        self, state: Hashable, callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to entering a state.

        Args:
            state (Hashable): the state
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        self._raise_on_state(state)
        return self._bind_callback(self._enter_callbacks[state], callback)

    def unbind_callback_at_enter(self, state: Hashable, handle: int):
        """Unbinds a callback for entering a state

        Args:
            state (Hashable): the state
            handle (int): the callback handle
        """
        self._raise_on_state(state)
        self._unbind_callback(self._enter_callbacks[state], handle)

    def bind_callback_at_exit(
        self, state: Hashable, callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to exiting a state.

        Args:
            state (Hashable): the state
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        self._raise_on_state(state)
        return self._bind_callback(self._exit_callbacks[state], callback)

    def unbind_callback_at_exit(self, state: Hashable, handle: int):
        """Unbinds a callback for exiting a state.

        Args:
            state (Hashable): the state
            handle (int): the callback handle
        """
        self._raise_on_state(state)
        self._unbind_callback(self._exit_callbacks[state], handle)

    def bind_callback_at_transition(
        self, state: Hashable, token: Hashable,
        callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to a transition.

        Args:
            state (Hashable): the exited state
            token (Hashable): the triggering token
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        self._raise_on_transition(state, token)
        return self._bind_callback(
            self._transition_callbacks[(state, token)], callback
        )

    def unbind_callback_at_transition(
        self, state: Hashable, token: Hashable, handle: int
    ):
        """Unbinds a callback for a transition.

        Args:
            state (Hashable): the exited state
            token (Hashable): the triggering token
            handle (int): the callback handle
        """
        self._raise_on_transition()
        self._unbind_callback(
            self._transition_callbacks[(state, token)], handle
        )

    def bind_callback_at_enter_termination(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to entering a terminal state.

        Args:
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        return self._bind_callback(self._enter_termination_callbacks, callback)

    def unbind_callback_at_enter_termination(self, handle: int):
        """Unbinds a callback for entering a terminal state.

        Args:
            handle (int): the callback handle
        """
        self._unbind_callback(self._enter_termination_callbacks, handle)

    def bind_callback_at_exit_termination(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to exiting a terminal state.

        Args:
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        return self._bind_callback(self._exit_termination_callbacks, callback)

    def unbind_callback_at_exit_termination(self, handle: int):
        """Unbinds a callback for exiting a terminal state.

        Args:
            handle (int): the callback handle
        """
        self._unbind_callback(self._exit_termination_callbacks, handle)

    def bind_callback_at_enter_initial(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to entering the initial state.

        Args:
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        return self._bind_callback(self._enter_initial_callbacks, callback)

    def unbind_callback_at_enter_initial(self, handle: int):
        """Unbinds a callback for entering the initial state.

        Args:
            handle (int): the callback handle
        """
        self._unbind_callback(self._enter_initial_callbacks, handle)

    def bind_callback_at_exit_initial(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to exiting the initial state.

        Args:
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        return self._bind_callback(self._exit_initial_callbacks, callback)

    def unbind_callback_at_exit_initial(self, handle: int):
        """Unbinds a callback for exiting the initial state.

        Args:
            handle (int): the callback handle
        """
        self._unbind_callback(self._exit_initial_callbacks, handle)

    def bind_callback_always(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        """Binds a callback to all transitions.

        Args:
            callback (Callable[[TransitionEvent], None]): the callback

        Returns:
            int: the callback handle
        """
        return self._bind_callback(self._always_callbacks, callback)

    def unbind_callback_always(self, handle: int):
        """Unbinds a callback for all transitions.

        Args:
            handle (int): the callback handle
        """
        self._unbind_callback(self._always_callbacks, handle)

    def _callback_generator(self, next_state: Hashable, token: Hashable):
        result = chain(
            (c for c in self._always_callbacks.values()),
            (c for c in self._exit_callbacks[self._current_state].values()),
            (
                c for c
                in self._transition_callbacks[
                    (self._current_state, token)
                ].values()
            ),
            (c for c in self._enter_callbacks[next_state].values())
        )
        for condition, callbacks in zip(
            (
                self._is_terminal[self._current_state],
                self._current_state == self._initial_state,
                self._is_terminal[next_state],
                next_state == self._initial_state
            ),
            (
                self._exit_termination_callbacks,
                self._exit_initial_callbacks,
                self._enter_termination_callbacks,
                self._enter_initial_callbacks
            )
        ):
            if condition:
                result = chain(
                    result, (
                        c for c in callbacks.values()
                    )
                )
        return result

    def feed_many(
        self, tokens: Iterable[Hashable], payloads: Iterable[Any] = None
    ) -> List[bool]:
        """Feed tokens and optionals payloads to the state machine.

        Args:
            tokens (Iterable[Hashable]): the tokens
            payloads (Iterable[Any], optional): the payloads. Defaults to None.

        Returns:
            List[bool]: a list of truth values representing the validity of
            the feed tokens.
        """
        if payloads is None:
            payloads = [None] * len(tokens)
        return [
            self.feed(token, payload)
            for token, payload in zip(tokens, payloads, strict=True)
        ]

    def feed(self, token: Hashable, payload: Any = None) -> bool:
        """Feed a token and a optional payload to the state machine.

        Args:
            token (Hashable): the token
            payload (Any, optional): the payload. Defaults to None.

        Raises:
            RuntimeError: when there is no initial state
            ValueError: when the token is invalid und raise_on_invalid_token
            was set to True

        Returns:
            bool: True if the token is valid, else False
        """
        if self._initial_state is None:
            raise RuntimeError("No initial state available!")
        self._raise_on_token(token)

        self._feed_count += 1

        token_ = token
        next_state = self._transitions.get((self._current_state, token_), None)
        if next_state is None:
            token_ = ...
            next_state = self._transitions.get(
                (self._current_state, token_), None
            )
            if next_state is None:
                if self._raise_on_invalid_token:
                    raise ValueError(f"Invalid token: '{token}'!")
                return False

        self._transition_count += 1
        next_state = self._transitions[(self._current_state, token_)]
        transition_event = TransitionEvent(
            next_state, self._current_state, token_,
            self._is_terminal[next_state], self._feed_count,
            self._transition_count,
            payload
        )
        [
            callback(transition_event) for callback
            in self._callback_generator(next_state, token_)
            if callback is not None
        ]
        self._current_state = next_state

        return True

    def reset(self):
        """Resets the state machine to the initial state. Also resets
        the feed count and the transition count.
        """
        self._current_state = self._initial_state
        self._feed_count = 0
        self._transition_count = 0

    @property
    def current_state(self) -> Hashable:
        """The current state the state machine is in.

        Returns:
            Hashable: the state machines current state
        """
        return self._current_state

    @property
    def is_terminated(self) -> bool:
        """Wether the current state is a terminal state

        Returns:
            bool: True if the state machine has terminated, else False
        """
        return self._is_terminal[self._current_state]

    @property
    def is_initial(self) -> bool:
        """Wether the current state is the initial state

        Returns:
            bool: True if the current state is the initial state, else False
        """
        return self._current_state == self._initial_state

    @property
    def feed_count(self) -> int:
        """How many times the feed method was called without raising a
        RuntimeError or TypeError.

        Returns:
            int: the feed count
        """
        return self._feed_count

    @property
    def transition_count(self) -> int:
        """How many times a transition was performed.

        Returns:
            int: the transition count
        """
        return self._transition_count

    @property
    def state_amount(self) -> int:
        """The amount of states the state machine has.

        Returns:
            int: the state amount
        """
        return len(self._is_terminal.keys())

    @property
    def transition_amount(self) -> int:
        """The amount of transitions the state machine has.

        Returns:
            int: the transition amount
        """
        return len(self._transitions.keys())
