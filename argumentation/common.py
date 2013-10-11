class IllegalArgument(Exception):
    pass

class IllegalMove(Exception):
    pass

class NotYourMove(Exception):
    pass

class DiscussionFinished(Exception):
    pass

class MethodNotApplicable(Exception):
    pass

class NoMoreMoves(Exception):
    pass

class Confused(Exception):
    pass

class Disagree(Exception):
    pass

def enum(*sequential, **named):
    """ This functions declares a new type 'enum' that acts as an enum. """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


Move = enum('QUESTION', 'CLAIM', 'WHY', 'BECAUSE', 'CONCEDE', 'ASSERT')

PlayerType = enum('OPONENT', 'PROPONENT')


def role_str(p):
    return PlayerType.reverse_mapping[p]


def move_str(m):
    return Move.reverse_mapping[m]

# helpers
def oi_to_args(issues):
    """ Return a set containing all arguments in the list of open issues."""
    res = set()
    for i in issues:
        res &= set(i.arguments)
    return res

