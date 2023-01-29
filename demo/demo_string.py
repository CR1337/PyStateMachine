from src.state_machine import DeterministicFiniteStateMachine


sm = DeterministicFiniteStateMachine()

# Define states by giving them strings as names.
# A state machine needs exactly one initial state
# and can have many terminal states
sm.add_state('x', is_initial=True)
sm.add_state('o')
sm.add_state('m')
sm.add_state('g', is_terminal=True)

# Define transitions between states.
# A Transition needs an outgoing state, an ingoing state
# and a token that triggers the transition.
# Important: The token has to be of a hashable type, meaning it's
# class has to implement __hash__ and __eq__. Most built in types do this.
# See hashable_point.py for an example of a hashable class.
sm.add_transition('x', 'o', "o")
# Using ... as the token indicates that the transition shall be activated
# by any token not matching a previous used one
sm.add_transition('x', 'x', ...)

sm.add_transition('o', 'm', "m")
sm.add_transition('o', 'o', "o")
sm.add_transition('o', 'x', ...)

sm.add_transition('m', 'g', "g")
sm.add_transition('m', 'o', "o")
sm.add_transition('m', 'x', ...)

sm.add_transition('g', 'o', "o")
sm.add_transition('g', 'x', ...)

text = "Hey dude omg! That's awesome. omg!"

omg_indices = []

for char in text:
    # Feed the state machine one char after another causing state transitions.
    # It returns True if a transition is defined for that token, else False.
    sm.feed(char)
    # If the current state is a terminating state, a 'omg' was found.
    if sm.is_terminated:
        # transition_amount counts how many transitions have occured so far.
        # There also exists feed_amount which count all calls to feed, also
        # those that return False
        omg_indices.append(sm.transition_amount - len('omg'))

print(f"{omg_indices=}")
