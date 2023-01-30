from itertools import chain
from typing import Any, Callable, Dict, Hashable, Tuple


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

    _exit_callbacks: Dict[
        str,
        Dict[int, Callable[[TransitionEvent], None]]
    ]
    _enter_callbacks: Dict[
        str,
        Dict[int, Callable[[TransitionEvent], None]]
    ]
    _transition_callbacks: Dict[
        Tuple[str, Hashable],
        Dict[int, Callable[[TransitionEvent], None]]
    ]
    _enter_termination_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _exit_termination_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _enter_initial_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _exit_initial_callbacks: Dict[int, Callable[[TransitionEvent], None]]
    _always_callbacks: Dict[int, Callable[[TransitionEvent], None]]

    _initial_state: str
    _current_state: str

    _feed_amount: int
    _transition_amount: int
    _next_handle: int

    def __init__(self):
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

        self._feed_amount = 0
        self._transition_amount = 0
        self._next_handle = 0

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
        self._enter_callbacks[name] = {}
        self._exit_callbacks[name] = {}

    def add_transition(self, out_state: str, in_state: str, token: Hashable):
        self._raise_on_non_existing_state(out_state)
        self._raise_on_non_existing_state(in_state)
        if (out_state, token) in self._transitions:
            raise KeyError(
                f"A transition '{out_state} --({token})--> ...' "
                "already exists!"
            )
        self._transitions[(out_state, token)] = in_state
        self._transition_callbacks[(out_state, token)] = {}

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
        self, state: str, callback: Callable[[TransitionEvent], None]
    ) -> int:
        self._raise_on_non_existing_state(state)
        return self._bind_callback(self._enter_callbacks[state], callback)

    def unbind_callback_at_enter(self, state: str, handle: int):
        self._raise_on_non_existing_state(state)
        self._unbind_callback(self._enter_callbacks[state], handle)

    def bind_callback_at_exit(
        self, state: str, callback: Callable[[TransitionEvent], None]
    ) -> int:
        self._raise_on_non_existing_state(state)
        return self._bind_callback(self._exit_callbacks[state], callback)

    def unbind_callback_at_exit(self, state: str, handle: int):
        self._raise_on_non_existing_state(state)
        self._unbind_callback(self._exit_callbacks[state], handle)

    def bind_callback_at_transition(
        self, state: str, token: Hashable,
        callback: Callable[[TransitionEvent], None]
    ) -> int:
        if (state, token) not in self._transitions:
            raise KeyError(
                f"A transition '{state} --({token})--> ...' does not exists!"
            )
        return self._bind_callback(
            self._transition_callbacks[(state, token)], callback
        )

    def unbind_callback_at_transition(
        self, state: str, token: Hashable, handle: int
    ):
        if (state, token) not in self._transitions:
            raise KeyError(
                f"A transition '{state} --({token})--> ...' does not exists!"
            )
        self._unbind_callback(
            self._transition_callbacks[(state, token)], handle
        )

    def bind_callback_at_enter_termination(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        return self._bind_callback(self._enter_termination_callbacks, callback)

    def unbind_callback_at_enter_termination(self, handle: int):
        self._unbind_callback(self._enter_termination_callbacks, handle)

    def bind_callback_at_exit_termination(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        return self._bind_callback(self._exit_termination_callbacks, callback)

    def unbind_callback_at_exit_termination(self, handle: int):
        self._unbind_callback(self._exit_termination_callbacks, handle)

    def bind_callback_at_enter_initial(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        return self._bind_callback(self._enter_initial_callbacks, callback)

    def unbind_callback_at_enter_initial(self, handle: int):
        self._unbind_callback(self._enter_initial_callbacks, handle)

    def bind_callback_at_exit_initial(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        return self._bind_callback(self._exit_initial_callbacks, callback)

    def unbind_callback_at_exit_initial(self, handle: int):
        self._unbind_callback(self._exit_initial_callbacks, handle)

    def bind_callback_always(
        self, callback: Callable[[TransitionEvent], None]
    ) -> int:
        return self._bind_callback(self._always_callbacks, callback)

    def unbind_callback_always(self, handle: int):
        self._unbind_callback(self._always_callbacks, handle)

    def _callback_generator(self, next_state: str, token: Hashable):
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
        [
            callback(transition_event) for callback
            in self._callback_generator(next_state, token_)
            if callback is not None
        ]
        self._current_state = next_state

        return True

    def reset(self):
        self._current_state = self._initial_state
        self._feed_amount = 0
        self._transition_amount = 0

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
    def feed_count(self) -> int:
        return self._feed_amount

    @property
    def transition_count(self) -> int:
        return self._transition_amount

    @property
    def state_amount(self) -> int:
        return len(self._is_terminal.keys())

    @property
    def transition_amount(self) -> int:
        return len(self._transitions.keys())
