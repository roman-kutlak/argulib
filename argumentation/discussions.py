#from enum import Enum

from .common import *
from .kb import KnowledgeBase, StrictRule, DefeasibleRule, Literal, ParseError
from .aal import ArgumentationFramework, Labelling
from .players import SmartPlayer, HumanPlayer


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









class Dialog:
    """ A class for supporting a dialog between the user and the computer.
    The class is responsible for parsing commands, updating a knowledge base,
    presenting arguments and reasoning.
    
    The methods for handling commands start with do_
    (same as in Python's cmd.Cmd). As the class represents a dialog, the answers
    from do_ are strings. Any reasonable exceptions are handled inside the class
    and errors are returned as strings.
    
    """

    def __init__(self, kb_path=None):
        self.load_kb(kb_path)
        self.discussion = None

    def load_kb(self, path):
        self.kb = KnowledgeBase.from_file(path)
        self.aaf = ArgumentationFramework(self.kb)

    def _init_discussion(self):
        self.discussion = GroundedDiscussion2(Labelling.grounded(self.aaf),
                            SmartPlayer(PlayerType.PROPONENT),
                            HumanPlayer(PlayerType.OPPONENT))

    def is_accepted_conclusion(self, conclusion):
        """Return true if there is an argument with the conclusion and it is IN.
        """
        if self.discussion is None: self._init_discussion()
        args = self.find_arguments(conclusion)
        if args is None: return False
        lab = self.discussion.labelling.label_for
        for arg in args:
            if arg is not None and lab(arg) == 'IN':
                return True
        return False

    def find_rule(self, conclusion):
        """ Find a rule with the given conclusion.
        Return None if no such rule exists.
        
        """
        if isinstance(conclusion, str):
            try:
                conclusion = Literal.from_str(conclusion)
            except ParseError as pe:
                print(pe)
                return None
        if not conclusion in self.kb.rules:
            return None
        else:
            rules = self.kb.rules[conclusion]
            # return the 'first' rule
            for x in rules: return x
            
    def find_rules(self, conclusion):
        """ Find rules with the given conclusion.
        Return None if no such rule exists.
        
        """
        if isinstance(conclusion, str):
            try:
                conclusion = Literal.from_str(conclusion)
            except ParseError as pe:
                print(pe)
                return None
        if not conclusion in self.kb.rules:
            return None
        else:
            rules = self.kb.rules[conclusion]
            return list(rules)

    def find_argument(self, conclusion):
        """ Find an argument with given conclusion.
        Return None if no such argument exists.
        
        """
        if isinstance(conclusion, str):
            try:
                conclusion = Literal.from_str(conclusion)
            except ParseError as pe:
                print(pe)
                return None
        if not conclusion in self.kb._arguments:
            return None
        else:
            args = self.kb._arguments[conclusion]
            # return the 'first' rule
            for x in args: return x
            
    def find_arguments(self, conclusion):
        """ Find argument with given conclusion.
        Return None if no such argument exists.
        
        """
        if isinstance(conclusion, str):
            try:
                conclusion = Literal.from_str(conclusion)
            except ParseError as pe:
                print(pe)
                return None
        if not conclusion in self.kb._arguments:
            return None
        else:
            args = self.kb._arguments[conclusion]
            return list(args)

    # FIXME: throw an exception if a new rule would make KB inconsistent?
    def add(self, rule):
        """ Add a rule to the knowledge base. """
        if isinstance(rule, str):
            if '->' in rule:
                rule = StrictRule.from_str(rule)
            elif '=>' in rule:
                rule = DefeasibleRule.from_str(rule)
            else:
                raise ParseError('"%s" is not a valid rule' % rule)
        # rule is either a StrictRule or DefeasibleRule
        self.kb.add_rule(rule)
        self.aaf = ArgumentationFramework(self.kb)
        self.discussion = None

    def delete(self, rule):
        """ Remove a rule from the knowledge base. """
        if isinstance(rule, str):
            if '->' in rule:
                rule = StrictRule.from_str(rule)
            elif '=>' in rule:
                rule = DefeasibleRule.from_str(rule)
            else:
                raise ParseError('"%s" is not a valid rule' % rule)
        res = self.kb.del_rule(rule)
        if res:
            self.aaf = ArgumentationFramework(self.kb)
            self.discussion = None
        return res


    #############  Commands #############

    def do_question(self, label, conclusion):
        """ Question the staus of an argument. """
        if self.discussion is None: self._init_discussion()
        arg = self.find_argument(conclusion)
        if arg is None:
            return self.do_explain(conclusion)
        system_lab = self.discussion.labelling.label_for(arg)
        if system_lab != label.upper():
            return (['The argument', str(conclusion),
                     'is labeled', str(system_lab.lower()),
                     'and not', str(label)])
        d = self.discussion
        lab_arg = Labelling.from_argument(arg, label)
        d.move(d.opponent, Move.WHY, lab_arg)
        move = d.proponent.make_move(d)
        try:
            if move is not None: self.discussion.move(*move)
        except IllegalMove:
            pass
        if move is not None:
            if move[2] == Labelling.empty():
                return ('There are no arguments against "%s".'
                            % str(conclusion))
            rule = move[2].argument.rule
            return ('argument_against_label_' + label, rule)
        else:
            return 'ok'

    def do_justify(self, conclusion):
        """ Ask for the rules that make the conclusion valid. """
        arg = self.find_argument(conclusion)
        if arg is None:
            return ('There is no argument with conclusion "%s"' % conclusion)
        return ('justification', arg.rule)

    def do_explain(self, conclusion):
        """ Show which antecedants are missing to achieve the conclusion. """
        print('Trying to explain ' + str(conclusion))
        rules = self.find_rules(conclusion)
        if rules is None or len(rules) == 0:
            rule = self.find_rule('-' + conclusion)
            if rule is None:
                return ('There is no rule with conclusion "%s"' % conclusion)
            else:
                return self.do_justify('-' + conclusion)

        # check that it is actually not true
        args = self.find_arguments(conclusion)
        if args is not None and len(args) > 0:
            return ('The proposition "%s" is true' % conclusion)

        # find out what the problem is
        for rule in rules:
            # find missing antecedants
            missing = list()
            for a in rule.antecedent:
                ar = self.find_argument(a)
                if ar is None:
                    missing.append(a)
            if missing != []:
                return ('The following conditions are not fulfilled: %s' %
                         str(missing))

        # if all fails...
        return ('No idea. The examined rules are: "%s"' % rules)

    def do_assert(self, rule):
        if isinstance(rule, str) and '->' not in rule and '=>' not in rule:
            rule = '==> ' + rule
        try:
            self.add(rule)
#            return 'Rule "%s" asserted.' % str(rule)
            return 'asserted %s' % str(rule)
        except ParseError as pe:
            return str(pe)

    def do_retract(self, rule):
        if isinstance(rule, str) and '->' not in rule and '=>' not in rule:
            rule = '==> ' + rule
        try:
            res = self.delete(rule)
            if res:
#                return 'rule "%s" deleted' % str(rule)
                return 'deleted %s' % str(rule)
            else:
                return 'no rule "%s" found' % str(rule)
        except Exception as e:
            return str(e)

    def do_print_aaf(self):
        """ Return the string representing the current argumentation framework.
        """
        return str(self.aaf)

    def do_print_kb(self):
        """ Return the string representing the current knowledge base.
        """
        return str(self.kb)

    def parse(self, command):
        """ Parse a command from a string.
        The commands have form: 
            why in x  - discuss why is an argument with conclusion x labeled IN
            why out x - discuss why is an argument with conclusion x labeled OUT
            why p     - what reasoning lead to conclusion p
            why not p - what reasoning lead to conclusion -p
            assert r  - add a rule to the knowledge base
            retract r - remove a rule from the knowledge base
            print af  - print argumentation framework
            pring kb  - print knowledge base
            concede   - concede to the last open issue

        """
        tmp = command.strip().split(' ')
#        print('User command: %s' % str(tmp))
        if len(tmp) < 2:
            return('the command "%s" has too few arguments' % command)

        if 'why' == tmp[0]:
            if ('IN' == tmp[1].upper() or
               'OUT' == tmp[1].upper() or
               'UNDEC' == tmp[1].upper() or
               'NOT' == tmp[1].upper()):
                if len(tmp) < 3:
                    return('the command "%s" has too few arguments' % command)
                return self.do_question(tmp[1], tmp[2])
            return self.do_justify(tmp[1])

        elif 'assert' == tmp[0]:
            rule = ' '.join(tmp[1:]) # the rule was split, put it back together
            return self.do_assert(rule)

        elif 'retract' == tmp[0]:
            rule = ' '.join(tmp[1:])
            return self.do_retract(rule)

        elif 'print' == tmp[0]:
            if 'kb'   == tmp[1].strip().lower(): return self.do_print_kb()
            elif 'af' == tmp[1].strip().lower(): return self.do_print_aaf()
            else: return 'Unknown parameter "%s"' % tmp[1]
        elif 'save' == tmp[0]:
            self.aaf.save_interesting_graph()
        else: return 'Unknown command'







