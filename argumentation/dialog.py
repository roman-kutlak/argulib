"""
Discussions interface

author: Roman Kutlak <roman@kutlak.net>
based on dialog game by Mikolaj Podlaszewski <mikolaj.podlaszewski@gmail.com>

date: 11 July 2013

This module implements interface for persuasion discussions.

"""

import logging
from cmd import Cmd

from argumentation.common import Move, IllegalMove, ArgumentationException
from argumentation.aal import ArgumentationFramework, Labelling
from argumentation.kb import KnowledgeBase, Literal, ParseError
from argumentation.kb import StrictRule, DefeasibleRule
from argumentation.players import SmartPlayer, ScepticalPlayer
from argumentation.players import HumanPlayer, PlayerType
from argumentation.discussions import GroundedDiscussion2


def get_log():
    return logging.getLogger('arg')

Debug = False

class NoSuchArgumentError(Exception):
    pass

class LabellingParseError(Exception):
    pass


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

    def labelling(self):
        return Labelling.grounded(self.aaf)

    def is_accepted_conclusion(self, conclusion):
        """Return true if there is an argument with the conclusion and it is IN.
        """
        if self.discussion is None: self._init_discussion()
        args = self.find_arguments(conclusion)
        get_log().info(str(args))
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
    def add(self, rule_str):
        """ Add a rule to the knowledge base. """
        get_log().debug('Adding rule "%s"' % str(rule_str))
        if isinstance(rule_str, str):
            if '->' in rule_str:
                result, rule = self.kb.construct_strict_rule(rule_str)
                if result:
                    self.kb.close()
                    self.kb.recalculate()
                return result
            elif '=>' in rule_str:
                result, _ = self.kb.construct_defeasible_rule(rule_str, True)
                return result
            elif '<' in rule_str:
                result, _ = self.kb.construct_ordering_rule(rule_str, True)
                return result
            else:
                raise ParseError('"%s" is not a valid rule' % rule_str)

    def delete(self, rule):
        """ Remove a rule from the knowledge base. """
        get_log().debug('Deleting rule "%s"' % str(rule))
        if isinstance(rule, str):
            if '->' in rule:
                rule = StrictRule.from_str(rule)
                rules = self.kb.transpositions(rule)
                rules.append(rule)
            elif '=>' in rule:
                rule = DefeasibleRule.from_str(rule)
                rules = {rule}
            else:
                raise ParseError('"%s" is not a valid rule' % rule)
        result = False
        for r in rules:
            result |= self.kb.del_rule(r)
        return result


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
        # if user asserts only a conclusion, add the defeasible rule synt. part
        if (isinstance(rule, str) and
            ('->' not in rule and '=>' not in rule and '<' not in rule)):
            rule = '==> ' + rule
        try:
            res = self.add(rule)
            if res:
                self.recalculate()
                return 'asserted %s' % str(rule)
            else:
                return ('Rule "%s" not added (it probably already exists?)' %
                        str(rule))
        except ParseError as pe:
            return str(pe)

    def do_retract(self, rule):
        if isinstance(rule, str) and '->' not in rule and '=>' not in rule:
            rule = '==> ' + rule
        try:
            res = self.delete(rule)
            if res:
                self.recalculate()
                return 'deleted %s' % str(rule)
            else:
                return 'no rule "%s" found' % str(rule)
            return res
        except Exception as e:
            return str(e)

    def recalculate(self):
        """ Recalculate the arguments from the knowledge base. """
        get_log().info('Recalculating aaf')
        self.aaf = ArgumentationFramework(self.kb)
        self.discussion = None

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
        get_log().info('parsing command: "%s"' % command)
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



################################ unused ################################

class Commands(Cmd):
    intro = "Persuasion dialogue."

    def __init__(self, desc=None):
        self.prompt = 'U: '
        self.kb = None
        self.af = None
        self.labelling = None
        self.discussion = None
        self.human_player = None
        self.computer_player = None
        Cmd.__init__(self)
        self.identchars += '()'

    def do_quit(self, l):
        """Quits the program."""
        return True

    def do_exit(self, l):
        """Quits the program."""
        return True

    # framework
    def do_load(self, path):
        """Loads a framework from a file."""
        try:
            self.kb = KnowledgeBase.from_file(path)
            self.af = ArgumentationFramework(self.kb)
            self.labelling = Labelling.grounded(self.af)
        except Exception as e:
            print("*** faild to load framework: %s" % path)
            print(e)

    def do_save(self, l):
        """Saves the graph of the current framework to a file."""
        try:
            self.af.save_graph()
        except Exception as e:
            print('Exception: %s' % e)

    def do_save_interesting(self, l):
        """Saves the graph of the current framework to a file."""
        try:
            self.af.save_interesting_graph()
        except Exception as e:
            print('Exception: %s' % e)

    def do_print_af(self, l):
        """Displays the current argumentation framework."""
        print('Current framework: ')
        print(self.af)

    def do_print_kb(self, l):
        """ Print the current knowledge base. """
        print('Current knowledge base: ')
        print(self.kb)


    def do_print_labelling(self, l):
        """ Print the current labelling. """
        print('Current labelling: ')
        print(self.labelling)

    def do_print_discussion(self, l):
        """ Prints the current history of the discussion. """
        if self.discussion is not None: print(self.discussion)
        else: print('Nothing has been discussed so far.')

    # dialog commands

    def do_question(self, l):
        """Asks for the status of a given argument.
        Example: question a

        """
        # start a discussion
        self.__start_game(human_role='opponent')
        arg = self._get_arg(l)
        if arg is not None:
            lab = self.labelling.labelling_for(arg)
            move = (self.computer_player, Move.CLAIM, lab)
            self._perform_move(move)

    def do_claim(self, l):
        """Claims an argument has a particular status.
        Examples:
            claim in(a)
            claim out(b)

        """
        self.__start_game(human_role='proponent')
        lab = self._get_label(l)
        if lab is None: return
        move = (self.human_player, Move.CLAIM, lab)
        if self._perform_move(move):
            self._respond()

    def do_retract(self, l):
        """Retracts the main claim and hence finishes the discussion.
         Example: retract

         """
        if not self._check_discussion_running(): return
        lab = self._get_label(l)
        if lab is None: return
        move = (self.human_player, Move.RETRACT, lab)
        if self._perform_move(move):
            self._respond()

    def do_why(self, l):
        """Asks for reasons why a particular argument is said to have
        a particular status.

        Examples:
            why in(a)
            why out(c)

         """
        if not self._check_discussion_running(): return
        lab = self._get_label(l)
        if lab is None: return
        move = (self.human_player, Move.WHY, lab)
        if self._perform_move(move):
            self._respond()

    def do_because(self, l):
        """Gives a reason for the status of the argument
        played in the previous 'claim' or 'because' move.

        Examples:
            because in(b)
            because out(c,d)

        """
        if not self._check_discussion_running(): return
        lab = self._get_label(l)
        if lab is None: return
        move = (self.human_player, Move.BECAUSE, lab)
        if self._perform_move(move):
            self._respond()

    def do_concede(self, l):
        """Concedes the status of an open issue.
        Examples:
            concede in(a)
            concede out(b)

        """
        if not self._check_discussion_running(): return
        # if human player is the proponent and concedes, finish the game
        if self.discussion.proponent == self.human_player:
            self.__finish_game(msg='C: I am happy to have convinced you.')
            return
        if len(l.strip()) == 0:
            # user gave up - terminate discussion
            return self.__finish_game()

        lab = self._get_label(l)
        if lab is None: return
        move = (self.human_player, Move.CONCEDE, lab)
        if self._perform_move(move):
            self._respond()

    # helpers

    def _perform_move(self, move):
        """ Try to make the given move and print any errors. """
        try:
            # print human moves only in debug
            if Debug: self._print_move(move)
            elif (move is not None and move[0] == self.computer_player):
                print('C:', end=' ')
                self._print_move(move)

            if move is not None:
                self.discussion.move(*move)
            return True
        except ArgumentationException as e:
            print(e)
            return False

    def _respond(self):
        """ Respond to the last dialog move. """
        if not self._check_discussion_running(): return
        if self.discussion.open_issues == []: return self.__finish_game()
        m = self.computer_player.make_move(self.discussion)
        if self._perform_move(m):
            if (m is not None and
                m[0] == self.computer_player and m[1] == Move.CONCEDE):
                self._respond()

    def _print_move(self, move):
        if move is None: return
        if move[2] == Labelling.empty():
            print('no attackers')
            return
        type = Move.reverse_mapping[move[1]]
        label = move[2].label
        arg = move[2].argument
        print('%s %s(%s)' % (type, label.lower(), str(arg.name)))

    def _get_label(self, l):
        try:
            labelling = self.__parse_labeling(l)
            return labelling

        except LabellingParseError as e:
            print(str(e))

        except NoSuchArgumentError as e:
            print(str(e))

    def _get_arg(self, l):
        try:
            arg = self.__parse_argument(l)
            return arg

        except NoSuchArgumentError as e:
            print(str(e))

    def __parse_labeling(self, l):
        """ Parse text to create labelling of an argument. """
        # replace braces
        l = l.replace('(', ' ').replace(')', ' ')
        args = l.strip().split(' ')
        # there should be two params: label and arg. conclusion
        if len(args) > 2:
            raise LabellingParseError('too many words for labelling: "%s"' % l)
        if len(args) < 2:
            raise LabellingParseError('too few words for labelling: "%s"' % l)

        label = args[0].strip().upper()
        if label not in ['IN', 'OUT', 'UNDEC']:
            raise LabellingParseError('no such label: "%s"' % label)

        labelling = Labelling.empty()
        arg = self.__parse_argument(args[1].strip())
        if 'UNDEC' == label: labelling.UNDEC.add(arg)
        elif 'IN' == label: labelling.IN.add(arg)
        elif 'OUT' == label: labelling.OUT.add(arg)

        return labelling


    def __parse_argument(self, name):
        """ Find an argument with given name.
        Raise NoSuchArgumentError if no such argument exists.

        """
#        if isinstance(name, str):
#            args = name.strip().split(' ')
#            # there should be two params: label and arg. name
#            if len(args) != 1:
#                raise NoSuchArgumentError('argument can\'t have space: "%s"'
#                                            % name)
#            try:
#                name = Literal.from_str(name)
#            except ParseError as e:
#                raise NoSuchArgumentError('incorrect argument name: "%s" - %s'
#                                            % (name, str(e)))
        if not name in self.af._arguments:
            raise NoSuchArgumentError('no argument with name "%s"'
                                        % name)
        else:
            arg = self.af._arguments[name]
            return arg


    # discussion

    def __finish_game(self, msg=None):
        if self.discussion.proponent == self.computer_player:
            print("C: Feel free to 'question' other argument")
        else:
            if msg is None:
                print('C: You convinced me, I believe you.')
            else:
                print(msg)
        self.discussion = None
        self.computer_player = None
        self.human_player = None

    def __start_game(self, human_role):
        """ Start a new discussion. """
        if self.labelling is None:
            print('No framework loaded.')
            return False

        if human_role == 'opponent':
            self.computer_player = SmartPlayer(PlayerType.PROPONENT)
            self.human_player    = HumanPlayer(PlayerType.OPPONENT)
            self.discussion = GroundedDiscussion2(self.labelling,
                                             self.computer_player,
                                             self.human_player)
        else:
            self.computer_player = SmartPlayer(PlayerType.OPPONENT)
            self.human_player    = HumanPlayer(PlayerType.PROPONENT)
            self.discussion = GroundedDiscussion2(self.labelling,
                                             self.human_player,
                                             self.computer_player)

    def _check_discussion_running(self):
        """ Return true if discussion is in progress.
        Else print prompt and return false.

        """
        if self.discussion is None:
            print('Start the discussion by asking the computer '\
                 + '(question p) or by claiming a status of a conclusion '\
                 + '(claim in(p))')
            return False
        else:
            return True

    def __prompt(self, question, options):
        answer = ''
        while answer not in options:
            print(question, '[%s]' % '/'.join(options), end='')
            answer = input().lower()
        return answer

    # others
    def preloop(self):
        pass

    def emptyline(self):
        pass
