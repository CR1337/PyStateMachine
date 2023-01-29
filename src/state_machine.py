from itertools import chain
from typing import Any, Callable, Dict, Hashable, List, Tuple


class TransitionEvent:

    _in_state: str
    _out_state: str
    _out_state_is_terminal: bool
    _token: Hashable
    _feed_amount: int
    _transition_amount: int
    _payload: Any

    def __init__(
        self, in_state: str, out_state: str, token: Hashable,
        is_terminal: bool, feed_amount: int, transition_amount: int,
        payload: Any
    ):
        self._in_state = in_state
        self._out_state = out_state
        self._out_state_is_terminal = is_terminal
        self._token = token
        self._feed_amount = feed_amount
        self._transition_amount = transition_amount
        self._payload = payload

    @property
    def in_state(self) -> str:
        return self._in_state

    @property
    def out_state(self) -> str:
        return self._out_state

    @property
    def out_state_is_terminal(self) -> bool:
        return self._out_state_is_terminal

    @property
    def token(self) -> Hashable:
        return self._token

    @property
    def feed_amount(self) -> int:
        return self._feed_amount

    @property
    def transition_amount(self) -> int:
        return self._transition_amount

    @property
    def payload(self) -> Any:
        return self._payload


class DeterministicFiniteStateMachine:

    _is_terminal: Dict[str, bool]
    _transitions: Dict[Tuple[str, Hashable], str]

    _out_callbacks: Dict[str, List[Callable[[TransitionEvent], None]]]
    _in_callbacks: Dict[str, List[Callable[[TransitionEvent], None]]]
    _transition_callbacks: Dict[
        Tuple[str, Hashable],
        List[Callable[[TransitionEvent], None]]
    ]
    _termination_callbacks: List[Callable[[TransitionEvent], None]]

    _initial_state: str
    _current_state: str

    _feed_amount: int
    _transition_amount: int

    def __init__(self):
        self._is_terminal = {}
        self._transitions = {}

        self._out_callbacks = {}
        self._in_callbacks = {}
        self._transition_callbacks = {}
        self._termination_callbacks = []

        self._initial_state = None
        self._current_state = None

        self._feed_amount = 0
        self._transition_amount = 0

    def _raise_on_non_existing_state(self, state: str):
        if state not in self._is_terminal:
            raise KeyError(f"State '{state}' does not exist!")

    def add_state(
        self, name: str, is_terminal: bool = False, is_initial: bool = False
    ):
        if name in self._is_terminal:
            raise KeyError(f"State '{name}' already exists!")
        if is_initial and self._initial_state is not None:
            raise ValueError(
                f"There is already an initial state: '{self._initial_state}'!"
            )
        self._is_terminal[name] = is_terminal
        if is_initial:
            self._initial_state = name
            self._current_state = name
        self._in_callbacks[name] = []
        self._out_callbacks[name] = []

    def add_transition(self, out_state: str, in_state: str, token: Hashable):
        self._raise_on_non_existing_state(out_state)
        self._raise_on_non_existing_state(in_state)
        if (out_state, token) in self._transitions:
            raise KeyError(
                f"A transition '{out_state} --({token})--> ...' "
                "already exists!"
            )
        self._transitions[(out_state, token)] = in_state
        self._transition_callbacks[(out_state, token)] = []

    def bind_callback_incoming(
        self, state: str, callback: Callable[[TransitionEvent], None]
    ) -> int:
        self._raise_on_non_existing_state(state)
        self._in_callbacks[state].append(callback)
        return len(self._in_callbacks[state]) - 1

    def unbind_callback_incoming(self, state: str, index: int):
        self._raise_on_non_existing_state(state)
        if index >= len(self._in_callbacks[state]):
            raise IndexError(f"Index '{index}' out of range!")
        if self._in_callbacks[state][index] is None:
            raise IndexError(f"Already unbound at index '{index}'!")
        self._in_callbacks[state][index] = None

    def bind_callback_outgoing(
        self, state: str, callback: Callable[[TransitionEvent], None]
    ) -> int:
        self._raise_on_non_existing_state(state)
        self._out_callbacks[state].append(callback)
        return len(self._out_callbacks[state]) - 1

    def unbind_callback_outgoing(self, state: str, index: int):
        self._raise_on_non_existing_state(state)
        if index >= len(self._out_callbacks[state]):
            raise IndexError(f"Index '{index}' out of range!")
        if self._out_callbacks[state][index] is None:
            raise IndexError(f"Already unbound at index '{index}'!")
        self._out_callbacks[state][index] = None

    def bind_callback_transition(
        self, state: str, token: Hashable,
        callback: Callable[[TransitionEvent], None]
    ) -> int:
        if (state, token) not in self._transitions:
            raise KeyError(
                f"A transition '{state} --({token})--> ...' does not exists!"
            )
        self._transition_callbacks[(state, token)].append(callback)
        return len(self._transition_callbacks[(state, token)]) - 1

    def unbind_callback_transition(
        self, state: str, token: Hashable, index: int
    ):
        if (state, token) not in self._transitions:
            raise KeyError(
                f"A transition '{state} --({token})--> ...' does not exists!"
            )
        if index >= len(self._transition_callbacks[(state, token)]):
            raise IndexError(f"Index '{index}' out of range!")
        if self._transition_callbacks[(state, token)][index] is None:
            raise IndexError(f"Already unbound at index '{index}'!")
        self._transition_callbacks[(state, token)][index] = None

    def bind_callback_termination(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        self._termination_callbacks.append(callback)
        return len(self._termination_callbacks) - 1

    def unbind_callback_termination(self, index: int):
        if index >= len(self._transition_callbacks):
            raise IndexError(f"Index '{index}' out of range!")
        if self._transition_callbacks[index] is None:
            raise IndexError(f"Already unbound at index '{index}'!")
        self._termination_callbacks[index] = None

    def feed(self, token: Hashable, payload: Any = None) -> bool:
        if self._initial_state is None:
            raise RuntimeError("No initial state available!")
        self._feed_amount += 1

        token_ = token
        next_state = self._transitions.get((self._current_state, token_), None)
        if next_state is None:
            token_ = ...
            next_state = self._transitions.get(
                (self._current_state, token_), None
            )
            if next_state is None:
                return False

        self._transition_amount += 1
        next_state = self._transitions[(self._current_state, token_)]
        transition_event = TransitionEvent(
            self._current_state, next_state, token_,
            self._is_terminal[next_state], self._feed_amount,
            self._transition_amount,
            payload
        )
        callbacks = chain(
            (c for c in self._out_callbacks[self._current_state]),
            (
                c for c
                in self._transition_callbacks[(self._current_state, token_)]
            ),
            (c for c in self._in_callbacks[next_state])
        )
        if self._is_terminal[next_state]:
            callbacks = chain(
                callbacks, (c for c in self._termination_callbacks)
            )
        [
            callback(transition_event) for callback in callbacks
            if callback is not None
        ]
        self._current_state = next_state

        return True

    @property
    def current_state(self) -> str:
        return self._current_state

    @property
    def is_terminated(self) -> bool:
        return self._is_terminal[self._current_state]

    @property
    def is_initial(self) -> bool:
        return self._current_state == self._initial_state

    @property
    def feed_amount(self) -> int:
        return self._feed_amount

    @property
    def transition_amount(self) -> int:
        return self._transition_amount

    @property
    def state_amount(self) -> int:
        return len(self._is_terminal.keys())

    @property
    def transition_amount(self) -> int:
        return len(self._transitions.keys())
