"""
Discussions interface

author: Roman Kutlak <roman@kutlak.net>
based on dialog game by Mikolaj Podlaszewski <mikolaj.podlaszewski@gmail.com>

date: 11 July 2013

This module implements interface for persuasion discussions.

"""

import sys, os, logging
from optparse import OptionParser
from cmd import Cmd
from glob import glob

from argumentation.common import Move, ArgumentationException
from argumentation.aal import ArgumentationFramework, Labelling
from argumentation.kb import KnowledgeBase, Literal, ParseError
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
            answer = raw_input().lower()
        return answer

    # others
    def preloop(self):
        pass

    def emptyline(self):
        pass
