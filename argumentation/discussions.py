#from enum import Enum

import logging
import random

from .common import Move, role_str, move_str, PlayerType
from .common import IllegalArgument, IllegalMove, NotYourMove


def log():
    return logging.getLogger('arg')

class GroundedDiscussion:
    Debug = False

    def __init__(self, labelling, proponent, opponent):
        """ Initialise the dialog by setting the labelling and two players. """
        self.proponent = proponent
        self.opponent = opponent
        self.labelling = labelling
        self.moves = list()
        self.open_issues = list()

    def __str__(self):
        op_str = str('Oponent: %s' % self.opponent.commitment)
        pr_str = str('Proponent: %s' % self.proponent.commitment)
        oi_str = str('Open Issues: %s' % [str(i) for i in self.open_issues])
        m_str  = ('Moves:\n\t' + '\n\t'.join(['%s: %s %s' %
                      (role_str(player.role), move_str(move), str(arg)) for
                           player, move, arg in self.moves]))
        return ('\n'.join([pr_str, op_str, oi_str, m_str]))

    __repr__ = __str__

    def labelling_for(self, arg):
        """ Find the label of the given argument. """
        return self.labelling.labelling_for(arg)

    def is_valid_conclusion(self, conclusion):
        return self.labelling.is_valid_conclusion(conclusion)

    def find_argument(self, string):
        """ Find the argument corresponding to the given string. """
        return self.labelling.find_argument(string)

    def is_oi(self, lab_arg):
        """ Return true if the labelled argument is an open issue. """
        return (lab_arg in self.open_issues)

    def is_last_oi(self, lab_arg):
        """ Return true if the labelled argument is the last open issue. """
        if len(self.open_issues) < 1: return False
        return (self.open_issues[-1] == lab_arg)

    def is_contradicting(self, lab_arg):
        """ Return true if an argument was labelled differently before. """
        if len(lab_arg) == 0: return False

        for la in self.open_issues:
            if len(la) == 0: continue
            if (la.argument == lab_arg.argument and la != lab_arg):
                return True
        return False

    def _last_why(self):
        """ Return the last WHY move. """
        for m in reversed(self.moves):
            if (m[1] == Move.WHY):
                return m
        raise IllegalArgument('WHY has not yet been played')

    def _last_because(self):
        """ Return the last BECAUSE or CLAIM move. """
        for m in reversed(self.moves):
            if (m[1] == Move.BECAUSE or m[1] == Move.CLAIM):
                return m
        raise IllegalArgument('BECAUSE has not yet been played')

    def move(self, player, move_type, arg):
        """ Update the data stores by performing a move in the discussion. """
        if move_type is None: return

        if move_type == Move.QUESTION:
            self._question(player, arg)
        elif move_type == Move.CLAIM:
            self._claim(player, arg)
        elif move_type == Move.WHY:
            self._why(player, arg)
        elif move_type == Move.BECAUSE:
            self._because(player, arg)
        elif move_type == Move.CONCEDE:
            self._concede(player, arg)
        elif move_type == Move.RETRACT:
            self._retract(player, arg)
        elif move_type == Move.DISAGREE:
            return None
        else:
            raise IllegalMove('Unknown move: %d' % move_type)

    def question(self, arg=None):
        """ Ask about the status of the argument. """
        if arg is None:
            arg = random.choice(list(self.labelling.arguments))
        lab = self.labelling_for(arg)
        return lab

    def _claim(self, player, lab_arg):
        """ Claim that the argument has a particular status. """
        if player.role != PlayerType.PROPONENT:
            print(player)
            raise NotYourMove('Only the proponent can "claim" arguments')

        if len(self.moves) != 0:
            raise IllegalMove('claim can only be used at the beginning '
                              'of the discussion')

        if self.Debug: print('appending "claim %s"' % lab_arg)
        player.update_commitment(lab_arg)
        self.open_issues.append(lab_arg)
        self.moves.append( (player, Move.CLAIM, lab_arg) )

    def _retract(self, player, lab_arg):
        if lab_arg in self.open_issues:
            self.open_issues.remove(lab_arg)
            self.moves.append( (player, Move.RETRACT, lab_arg) )
            return None
        else:
            raise IllegalMove('%s(%s) is not in open issues'
                    % (lab_arg.label, lab_arg.argument.name))

    def _because(self, player, lab_arg):
        if player.role != PlayerType.PROPONENT:
            raise NotYourMove('Only the proponent can use "because"')

        if len(self.moves) == 0 :
            raise IllegalMove('There are no open issues, play "claim" first')

        if self.moves[-1][1] == Move.BECAUSE :
            raise IllegalMove('Cannot play "because" twice in a rwo')

        if self.is_oi(lab_arg) :
            raise IllegalMove('This argument is already an open issue')

        if self.is_contradicting(lab_arg):
            raise IllegalMove('This argument was already used but with '
                              'a different label. '
                              'Use retract if you wish to chage it.')

        if self.Debug: print('appending "because %s"' % lab_arg)
        self.open_issues.append(lab_arg)
        player.update_commitment(lab_arg)
        self.moves.append( (player, Move.BECAUSE, lab_arg) )

    def _why(self, player, lab_arg):
        """ Challenge the status of the argument. """
        if player.role != PlayerType.OPPONENT:
            raise NotYourMove('Only the opponent can ask "why"')

        if not self.proponent.is_commited_to(lab_arg):
            raise IllegalMove('%s is not an issue' % lab_arg)

        if self.is_contradicting(lab_arg):
            raise IllegalMove('This argument was already used but with '
                              'a different label. '
                              'Use retract if you wish to chage it.')

        if not self.is_oi(lab_arg):
            self.open_issues.append(lab_arg)

        if self.Debug: print('appending "why %s"' % lab_arg)
        self.moves.append( (player, Move.WHY, lab_arg) )

    def _concede(self, player, lab_arg):
        """ Agree with the proponent on a particular labelling. """
        if player.role != PlayerType.OPPONENT:
            raise NotYourMove('Only the opponent can "concede"')

        if len(self.open_issues) == 0 :
            raise IllegalMove('There are no open issues')

        # chech that player is conceding to the last open issue
        if self.Debug: print('appending "concede %s"' % lab_arg)
        player.update_commitment(lab_arg)
        self.moves.append( (player, Move.CONCEDE, lab_arg) )
        self._concede_upto(lab_arg)

    def _concede_upto(self, lab_arg):
        idx = self.open_issues.index(lab_arg)
        self.open_issues = self.open_issues[:idx]

    def justify(self, arg):
        """ Return the rules of the reasoning chain
        leading to the conclusion contained in the argument.

        """
        return [a.rule for a in arg.subarguments]


################################################################################

class GroundedDiscussion2(GroundedDiscussion):
    Debug = False

    def _because(self, player, lab_arg):
        if player.role != PlayerType.PROPONENT:
            raise NotYourMove('Only the proponent can use "because"')

        if len(self.open_issues) == 0 :
            raise IllegalMove('There are no open issues, play "claim" first')

        if self.moves[-1][1] == Move.BECAUSE :
            print(self.moves)
            raise IllegalMove('Cannot play "because" twice in a row')

        if self.is_oi(lab_arg) :
            raise IllegalMove('This argument is already an open issue')

        if self.is_contradicting(lab_arg):
            raise IllegalMove('This argument was already used but with '
                              'a different label. '
                              'Use retract if you wish to chage it.')

        if self.Debug: print('appending "because %s"' % lab_arg)
        self.open_issues.append(lab_arg)
        self.moves.append( (player, Move.BECAUSE, lab_arg) )

    def _why(self, player, lab_arg):
        """ Challenge the status of the argument. """
        if player.role != PlayerType.OPPONENT:
            raise NotYourMove('Only the opponent can ask "why"')

        if self.is_contradicting(lab_arg):
            raise IllegalMove('This argument was already used but with '
                              'a different label. '
                              'Use retract if you wish to chage it.')

        if not self.is_oi(lab_arg):
            self.open_issues.append(lab_arg)

        if self.Debug: print('appending "why %s"' % lab_arg)
        self.moves.append( (player, Move.WHY, lab_arg) )

    def _concede(self, player, lab_arg):
        """ Agree with the proponent on a particular labelling. """
        if player.role != PlayerType.OPPONENT:
            raise NotYourMove('Only the opponent can "concede"')

        if len(self.open_issues) == 0 :
            raise IllegalMove('There are no open issues')

        # chech that player is conceding to the last open issue
        if self.Debug: print('appending "concede %s"' % lab_arg)
        self.moves.append( (player, Move.CONCEDE, lab_arg) )
        self._concede_upto(lab_arg)


class SimpleDiscussion(GroundedDiscussion):
    Debug = False

    def _because(self, player, lab_arg):
        if self.Debug: print('appending "because %s"' % lab_arg)
        self.open_issues.append(lab_arg)
        self.moves.append( (player, Move.BECAUSE, lab_arg) )

    def _why(self, player, lab_arg):
        """ Challenge the status of the argument. """
        if not self.is_oi(lab_arg):
            self.open_issues.append(lab_arg)

        if self.Debug: print('appending "why %s"' % lab_arg)
        self.moves.append( (player, Move.WHY, lab_arg) )

    def _concede(self, player, lab_arg):
        """ Agree with the proponent on a particular labelling. """
        # chech that player is conceding to the last open issue
        if self.Debug: print('appending "concede %s"' % lab_arg)
        self.moves.append( (player, Move.CONCEDE, lab_arg) )
        self._concede_upto(lab_arg)
