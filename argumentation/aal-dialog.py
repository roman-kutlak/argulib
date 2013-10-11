"""
Discussions interface

author: Mikolaj Podlaszewski <mikolaj.podlaszewski@gmail.com>
date: 12 Apr 2012

This module implements interface for persuasion discussions.

Modified by Roman Kutlak <roman@kutlak.net>
"""

import sys, os
from optparse import OptionParser
from cmd import Cmd
from glob import glob

import aal as af
from kb import *


class Commands(Cmd):
    AF = None
    GL = None
    LL = []
    D = []
    CSu = None
    CSc = None
    intro = "Persuasion dialogue."
    
    def __init__(self, desc=None):
        self.prompt = 'U: '
        Cmd.__init__(self)
        self.identchars += '()'
        
    def __print_CS(self):
        print("\tCommitment Stores")
        print("\tUser: %s\tComputer: %s" % (self.CSu.dl_str(), self.CSc.dl_str()))
    
    def __reset_discussion(self):
        self.D = []
        self.CSu = self.AF.empty_labelling()
        self.CSc = self.AF.empty_labelling()
    
    def __draw_reason(self,reason):
        pass
    
    def __clear_ubigraph(self):
        pass
    
    def __draw_ubigraph(self):
        pass
    
    def __set_af(self, AF):
        self.AF = AF
        self.GL = AF.find_grounded()
        L = self.AF.undec_labelling()
        self.LL = []
        while type(L) != bool:
            self.LL.append(L)
            L = L.up_complete_step()
        self.__reset_discussion()
        assert(self.LL[-1] == self.GL)
        
    def __prompt(self, question, options):
        answer = ''
        while answer not in options:
            print(question, '[%s]' % '/'.join(options), end='')
            answer = raw_input().lower()
        return answer    

    #framework
    def do_load(self, l):
        """Loads a framework from a file."""
        try:
            kb = KnowledgeBase.from_file(l)
            self.__set_af(af.ArgumentationFramework(kb))
            print("new framework loaded.")
        except IOError:
            print("*** faild to load framework: %s" % l)
        
    def do_save(self, path):
        """Saves the graph of the current framework to a file."""
        try:
            self.AF.save_graph()
        except Exception as e:
            print('Exception: %s' % e)
    
    def _do_frame(self, l):
        if l:
            self.__set_af(af.ArgumentationFramework(l.split(' ')))
            print('framework changed\n')
        else:
            print('current framework\n')
        print(self.AF)
    
    def do_af_cat(self, l):
        """Displays the current argumentation framework."""
        print('current framework\n')
        print(self.AF)
    
    def do_af_define(self, l):
        """Defines a new argumentation framework."""
        self.__set_af(af.ArgumentationFramework(l.split(' ')))
        print('framework changed\n')
        print(self.AF)
    
    #discussion
    def __parse_args(self, l, a):
        try:
            a += self.AF.labs2args(l)
            return True
        except KeyError as key:
            print('*** unknown argument: %s' % key)
            return False
    
    def __parse_lab(self, l, L):
        """Parses line l and write into labelling L. Returns True if successful
             Format: in(a), out(a,b,c)"""
        l = l.strip()
        if not l:
            print("*** missing labelling")
            print("*** expected format: in(a[,...]), out(a[,...])"        )
        args, argslab = [], ''
        if l[:2] == 'in':
            lab = 'IN'
            argslab = l[3:-1]
        elif l[:3] == 'out':
            lab = 'OUT'
            argslab = l[4:-1]
        if argslab and self.__parse_args(argslab.split(','), args):
            for a in args: L.setLab(a, lab)
        else:
            return
        if L.dl_str() == l:
            return True
        else:
            print("*** cannot parse labelling: %s" % l)
            print("*** expected format: in(a[,...]), out(a[,...])")
            return False
    
    def __finish_game(self):
        """Call to finish game. Returns True if game in progres"""
        if self.D:
            print('*** we are discussing %s' % self.D[0][2].dl_str())
            if self.D[0][0] == 'C':
                print('*** use concede if you want to stop')
            else:
                print('*** use retract if you want to stop')
            return True
        else: 
            return False 
    
    def __start_game(self):
        """Call to start game. Returns True if game not in progress"""
        if not self.D:
            print("*** Start discussion first")
            print("*** Use 'question' or 'claim' to start discussion")
            return True
        else: 
            return False 
    
    def do_question(self, l):
        """Asks for the status of a given argument.
     Example: question a"""
        # is move ok
        if self.__finish_game(): return
        #parse lab
        a = []
        if not self.__parse_args([l], a):
            return
        a = a[0]
        lab = self.GL.getLab(a)
        #answer
        if lab in ['IN', 'OUT']:
            print('C: claim %s(%s)' % (lab.lower(), a.name))
            L = self.AF.empty_labelling()
            L.setLab(a,lab)
            M = ('C', 'claim', L)
            self.D.append(M)
            self.CSc.union_update2(L)
            self.__print_CS()
            self.__clear_ubigraph()
            self.__draw_reason(L)
        else:
            print('no commitment')

#    def complete_question(self, text, line, bidx, eidx):
#        if text: return [text]
#        return self.AF.ar.keys()
    
    def do_claim(self, l):
        """Claims an argument has a particular status.
     Examples:
         claim in(a)
         claim out(b)"""
        #is move OK?
        if self.__finish_game(): return
        L = self.AF.empty_labelling()
        if not self.__parse_lab(l, L): return 
        #single arg?
        if not self.__single_arg(L): return
        #make move 
        if L.is_sublabelling(self.GL):
            print('C: concede %s' % L.dl_str())
        else:
            M = ('U', 'claim', L)
            self.D.append(M)
            self.CSu.union_update2(L)
            self.__print_CS()
            self.__clear_ubigraph()
            self.__draw_reason(L)
            #answer
            M = ('C', 'why', L)
            self.D.append(M)
            print('C: why %s' % L.dl_str())
    
#    def complete_claim(self, text, line, bidx, eidx):
#        a = ['in(%s)' % a for a in self.AF.ar.keys()] + ['out(%s)' % a for a in self.AF.ar.keys()]
#        return filter(lambda s: s.startswith(text), a)
    
    def do_retract(self, l):
        """Retracts the main claim and hence finishes the discussion.
     Example: retract"""
        if self.__start_game(): return
        if self.D[0][0] != 'U':
            print("*** I have made main claim")
            print("*** Use 'concede' to stop discussion")
            return
        #stops discussion
        self.__terminate_discussion()
    
    def __get_OI(self):
        if self.D[0][0] == 'C':
            return self.CSc - self.CSu
        else:
            return self.CSu - self.CSc
    
    def __get_LOI(self):
        OI = self.__get_OI()
        for i in range(len(self.D)-1, -1, -1):
            M = self.D[i]
            L = OI & M[2]
            if L: return L
        return self.AF.empty_labelling()
    
    def __get_reasons(self,L):
        reasons = []
        for a in L.IN:
            reasons.append(self.AF.out_labelling(a.minus))
        for a in L.OUT:
            for b in a.minus:
                reasons.append(self.AF.in_labelling([b]))
        return reasons
    
    def __good_reason(self,L):
        reasons = self.__get_reasons(L)
        for L in self.LL:
            for R in reasons:
                if R.is_sublabelling(L): return R
    
    def __contains_reasons(self, LAB, L):
        for R in self.__get_reasons(L):
            if R.is_sublabelling(LAB): return R
        return False
    
    def __in_LOI(self, L):
        LOI = self.__get_LOI()
        if not L.is_sublabelling(LOI):
            print("*** current open issue is %s" % LOI.dl_str())
            print("*** use 'why' or 'concede' concerning an open issue")
            return False
        return True
    
    def __single_arg(self, L):
        if len(L) != 1:
            print("*** you need to give a statement about single argument")
            return False
        return True
    
    def do_why(self, l):
        """Asks for reasons why a particular argument is said to have a particular status.
     Examples:
         why in(a)
         why out(c)"""
        #parse
        L = self.AF.empty_labelling()
        if not self.__parse_lab(l, L): return 
        #is move OK?
        if self.__start_game(): return
        #is in scope
        if not self.__in_LOI(L): return
        #single arg?
        if not self.__single_arg(L): return
        #is not committed?
        reason = self.__contains_reasons(self.CSu, L)
        if reason:
            print("*** you already know why")
            print("*** we agreed that %s" % reason.dl_str())
            print("*** use 'concede'")
            return
        if type(reason) != bool:
            print("*** %s has no attackers. 'concede'?" % list(L.IN)[0])
            return
        #answer
        reason = self.__good_reason(L)
        M = ('C', 'because', reason)
        self.D.append(M)
        self.CSc.union_update2(reason)
        self.__draw_reason(reason)
        self.__print_CS()
        print('C: because %s' % reason.dl_str())
    
#    def do_test(self, l):
#        print(self.AF.ar.keys(), ['arg: %s' % a for a in self.AF.ar.keys()])
        
    def do_because(self, l):
        """Gives a reason for the status of the argument played in the previous 'claim' or 'because' move.
     Examples:
         because in(b)
         because out(c,d)"""
        #parse
        L = self.AF.empty_labelling()
        if not self.__parse_lab(l, L): return 
        #is in scope
        if self.__start_game(): return
        LM = self.D[-1]
        if LM[0] != 'C' or LM[1] != 'why':
             print("*** I haven't asked anything")
             return
        #is proper answer?
        reasons = self.__get_reasons(LM[2])
        if L not in reasons:
             print("*** %s is not a good reason for %s" % (L.dl_str(), LM[2].dl_str()))
             if reasons:
                 print("*** good reasons: %s" % ' or '.join([r.dl_str() for r in reasons]))
             else:
                 print("*** there are no good reasons. 'retract'?")
             return
        OI = self.__get_OI()
        if L & OI:
             print("*** %s is still under discussion" % (L & OI).dl_str())
             print("*** therefore %s cannot be used as a reason" % L.dl_str())
             return
        diffargs = L.diffargs(self.CSu)
        if diffargs:
             print("*** you cannot explain %s when committed to %s" % (L.dl_str(), self.CSu.dl_str()))
             print("*** choose other reason or 'retract'")
             return
        self.CSu.union_update2(L)
        self.__print_CS()
        self.__draw_reason(L)
        M = ('U', 'because', L)
        self.D.append(M)        
        #answer
        Ls = self.__get_LOI().split()
        #take anything in L
        M = ('C', 'why', Ls[0])
        self.D.append(M)
        print('C: why %s' % Ls[0].dl_str())
    
    def __terminate_discussion(self):
        self.__reset_discussion()        
        print("C: I am happy to convince you")
        print("C: Feel free to 'question' other argument")
        
    def do_concede(self, l):
        """Concedes the status of an open issue.
     Examples:
         concede in(a)
         concede out(b)"""
        if self.__start_game(): return
        l = l.strip()
        if not l:
            if self.D[0][0] != 'C':
                print("*** you made the main claim")
                print("*** use 'retract' to stop discussion")
                return
                #stops discussion
            self.__terminate_discussion()
        else:        
            #parse
            L = self.AF.empty_labelling()
            if not self.__parse_lab(l, L): return 
            #single arg?
            if not self.__single_arg(L): return
            #is in scope
            if not self.__in_LOI(L): 
                print("*** or concede without labelling to terminate discussion" )
                return
            self.CSu.union_update2(L)
            self.__print_CS()
            self.__draw_reason(L)
            M = ('U', 'concede', L)
            self.D.append(M)
            if not self.__get_LOI():
                self.__terminate_discussion()
                    
    #others
    def do_quit(self, l):
        """Quits the program."""
        return True
    
    def do_exit(self, l):
        """Quits the program."""
        return True
    
    def preloop(self):
        pass

    def emptyline(self):
        pass

#prompt parsing
parser = OptionParser(usage="usage: \n\t%prog <framework description>    \n\t%prog -f <framework file>", version="%prog 0.4")
parser.add_option("-f", "--file", type="string", action="store", dest="aff", default=None,
                                    help="file with argumentation framework")
(options, args) = parser.parse_args()

desc = None
if options.aff:
        try:
                desc = file(options.aff).read()
        except IOError:
                print("Error reading file %s" % options.aff)
                quit()
elif (args):
        desc = args
else:
        print('Warning: Empty Argumentation Framework'        )

app = Commands(desc)
app.cmdloop()

