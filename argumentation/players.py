import random

from .common import Move, PlayerType, NoMoreMoves, IllegalArgument, IllegalMove
from .aal import Labelling, is_justified, oi_to_args


class Player:
    def __init__(self, player_type):
        self.role = player_type
        self.commitment = Labelling(None, set(), set(), set())

    def __str__(self):
        return ('%s: %s' % (role_str(self.role),
                            str(self.commitment)))

    __repr__ = __str__

    def update_commitment(self, lab_arg):
        self.commitment.IN |= lab_arg.IN - self.commitment.OUT
        self.commitment.OUT |= lab_arg.OUT - self.commitment.IN
        self.commitment.UNDEC |= lab_arg.UNDEC

    def make_move(self, discussion):
        """ Make a move given the current state of the discussion. """
        if len(discussion.moves) == 0:
            # if the user wants the computer to initiate the discussion
            # pick a random argument
            lab = discussion.question()
            return (self, Move.CLAIM, lab)

        _, move_type, lab_arg = discussion.moves[-1]

        # the other player played the following move
        if move_type == Move.QUESTION:
            return self._question(discussion, lab_arg)
        elif move_type == Move.CLAIM:
            return self._answer_because(discussion, lab_arg)
        elif move_type == Move.WHY:
            return self._answer_why(discussion, lab_arg)
        elif move_type == Move.BECAUSE:
            return self._answer_because(discussion, lab_arg)
        elif move_type == Move.CONCEDE:
            return self._answer_concede(discussion, lab_arg)

    def _answer_because(self, discussion, lab_arg):
        """ React on 'because.' """
        return self._ask_why_or_concede(discussion)

    def _answer_why(self, discussion, lab_arg):
        """ Answer 'why' question. """
        loi = discussion.open_issues[-1]
        attacker = self._give_reason_for(loi, discussion)
        self.update_commitment(loi)
        return (self, Move.BECAUSE, attacker)

    def _answer_concede(self, discussion, lab_arg):
        """ React to 'concede.' """
        # proponent does not have to anything
        last_move = discussion.moves[-1]
        if last_move[0] != self:
            return None
        # if there are any more open issues, discuss them
        if len(discussion.open_issues) > 0:
            return self._ask_why_or_concede(discussion)
        else:
            raise NoMoreMoves()

    def _ask_why_or_concede(self, discussion):
        """ Ask about a reason for labeling the LOI the way it was labeled. """
        loi = discussion.open_issues[-1]
        # if  we agree with the label, accept it
        if (loi.label == discussion.labelling.label_for(loi.argument)):
            self.update_commitment(loi)
            return (self, Move.CONCEDE, loi)
        return (self, Move.WHY, loi)

    def _give_reason_for(self, lab_arg, discussion):
        attackers = self._possible_attackers(discussion, lab_arg)
        # remove commited arguments
        attackers = list(filter(lambda x:
            not x.argument in self.commitment.arguments, attackers))
        attacker = discussion.labelling.find_lowest_step(attackers)
        return attacker

    def _possible_attackers(self, discussion, lab_arg):
        """ Return attackers of an argument that are not open issues. """
        attackers = lab_arg.argument.minus - oi_to_args(discussion.open_issues)
        attackers = map(discussion.labelling.labelling_for, attackers)
        # filter out irrelevant attackers ie attackers with same label or UNDEC
        attackers = list(filter(lambda x:
            x.label != 'UNDEC' or x.label != lab_arg.label, attackers))
        return attackers
    
    def _agree_on_label_or_rise(self, labelling, lab_arg):
        # first check that we agree on the label
        label = labelling.label_for(lab_arg.argument)
        if (label != lab_arg.label):
            raise discussions.Disagree('%s is %s, not %s' %
                (str(lab_arg.argument), label, lab_arg.label))

    def is_commited_to(self, lab_arg):
        return lab_arg.is_sublabelling(self.commitment)

    def _is_reason_for(self, reason, issue):
        """ Check if arg_reason is a justification for arg_conclusion. """
        # reason is not valid if it does not fit in with my commitments
        if not is_justified(reason, self.commitment): return False
        # if we agree with the status of the reason, chech that it is an attack
        return (reason.argument in issue.argument.minus)


class HumanPlayer(Player):
    """ A player that represents a human. """

    def make_move(self, discussion):
        """ Make a move given the current state of the discussion. """
        pass

    def parse_command(self, command, discussion):
        """ Parse a command from a string and return a valid discussion move."""
        tmp = command.strip().split(' ')
        print('User command: %s' % str(tmp))

        if len(tmp) == 0: raise IllegalMove
        move_type = None
        if   tmp[0] == 'why': move_type = Move.WHY
        elif tmp[0] == 'concede': move_type = Move.CONCEDE
        elif tmp[0] == 'assert': move_type = Move.ASSERT
        else: raise IllegalMove('"%s" is not a valid move' % tmp[0])

        if move_type == Move.CONCEDE:
            return (self, move_type, discussion.open_issues[-1])

        if move_type == Move.WHY:
            if len(tmp) < 3: raise IllegalMove('"Why" requires two parameters')
            lab = tmp[1]
            id  = tmp[2]
            args = list(discussion.labelling.find_arguments_with_conclusion(id))
            args = list(map(lambda x: discussion.labelling_for(x), args))
            if len(args) == 0:
                raise IllegalArgument('Ther is no argument with conclusion "%s"'
                            % tmp[2])
            return (self, move_type, args[0])


class ScepticalPlayer(Player):
    """ A player that keeps asking WHY unless an argument has no attackers. """
    
    def _ask_why_or_concede(self, discussion):
        """ Ask about a reason for labeling the LOI the way it was labeled. """
        loi = discussion.open_issues[-1]
        if is_justified(loi, self.commitment):
            self.update_commitment(loi)
            return (self, Move.CONCEDE, loi)
        return (self, Move.WHY, loi)


class SmartPlayer(Player):
    """ A player that questions the validity of reasons. """

    def _answer_because(self, discussion, lab_arg):
        """ React on 'because' by questioning the status of the attackers. """
        loi = discussion.open_issues[-1]
        # ignore undecided args
        if (loi.label == 'UNDEC'):
            return (self, Move.CONCEDE, loi)

        # do we agree that lab_arg is a valid reason for the LOI?
        if self._is_reason_for(lab_arg, loi):
            # if a reason is valid, commit to the reason
            self.update_commitment(lab_arg)

        # if we need more reasons, ask about the LOI, otherwise CONCEDE
        return self._ask_why_or_concede(discussion);

    def _answer_why(self, discussion, lab_arg):
        """ React to 'why' question by giving a reason or failing. """
        loi = discussion.open_issues[-1] # == lab_arg
        attackers = self._possible_attackers(discussion, loi)
        # now select the attacker with the lowest step?
        if len(attackers) == 0:
            return (self, Move.BECAUSE, Labelling(None, set(), set(), set()))
        attacker = discussion.labelling.find_lowest_step(attackers)
        self.update_commitment(attacker)
        return (self, Move.BECAUSE, attacker)

    def _ask_why_or_concede(self, discussion):
        """ Ask about a reason for labeling the LOI the way it was labeled. """
        loi = discussion.open_issues[-1]
        if is_justified(loi, self.commitment):
            self.update_commitment(loi)
            return (self, Move.CONCEDE, loi)
        attackers = self._possible_attackers(discussion, loi)
        # remove the ones the player believes in
        attackers = list(filter(lambda x:
            not x.argument in self.commitment.arguments, attackers))
        # now select the attacker with the lowest step?
        attacker = discussion.labelling.find_lowest_step(attackers)

        if attacker.argument.minus == set():
            self.update_commitment(loi)
            return (self, Move.CONCEDE, loi)
        else:
            return (self, Move.WHY, attacker)




