"""
    author: Roman Kutlak <roman@kutlak.net>

    Based on the Abstract Argumentation Library by
    Mikolaj Podlaszewski <mikolaj.podlaszewski@gmail.com>

"""

import copy
from .common import *
from .kb import Literal


class Labelling:
    """Labelling (possibly partial)"""
    _framework, IN, OUT, UNDEC = None, None, None, None

    def __init__(self, frame, IN = set(), OUT = None, UNDEC = None):
        self.steps = dict()
        self._framework = frame
        self.IN = IN
        self.OUT = OUT
        self.UNDEC = UNDEC
        if self.UNDEC == None:
            self._update_UNDEC()

    @classmethod
    def grounded(cls, af):
        """ Return grounded labeling created from a framework. """
        return cls.all_UNDEC(af).up_complete_update()

    def _update_UNDEC(self):
        """Updates UNDEC so that it contains arguments not present in IN and OUT"""
        self.UNDEC = set(self._framework._arguments.values())
        self.UNDEC.difference_update(self.IN, self.OUT)


    def __eq__(self, other):
        return (self.IN == other.IN and
                self.OUT == other.OUT and
                self.UNDEC == other.UNDEC)

    def __repr__(self):
        IN = [a.name for a in self.IN]
        OUT = [a.name for a in self.OUT]
        UNDEC = [a.name for a in self.UNDEC]
        IN.sort()
        OUT.sort()
        UNDEC.sort()
        return "Labelling: ({%s},{%s},{%s})" % (', '.join(IN),
                                                ', '.join(OUT),
                                                ', '.join(UNDEC))
    
    def __str__(self):
        """Dialogue string representation: in(a,b)"""
        res = []
        IN = [a.name for a in self.IN]
        if IN:
            IN.sort()
            res.append('in(%s)' % ','.join(IN))
        
        OUT = [a.name for a in self.OUT]
        if OUT:
            OUT.sort()
            res.append('out(%s)' % ','.join(OUT))
    
        UNDEC = [a.name for a in self.UNDEC]
        if UNDEC:
            UNDEC.sort()
            res.append('undec(%s)' % ','.join(UNDEC))
        return ' '.join(res) if res else '-'

    def getLab(self, arg):
        """Returns status of argument"""
        if arg in self.IN:
            return "IN"
        elif arg in self.OUT:
            return "OUT"
        else:
            return "UNDEC"

    def setLab(self, arg, status):
        self.IN.discard(arg)
        self.OUT.discard(arg)
        self.UNDEC.discard(arg)
        if status == "IN":
            self.IN.add(arg)
        elif status == "OUT":
            self.OUT.add(arg)
        elif status == "UNDEC":
            self.UNDEC.add(arg)
        else:
            raise Exception("Wrong status: %s" % status)

    # Predefined labellings
    @classmethod
    def all_IN(cls, af):
        """ Return labelling where all arguments are labelled as IN. """
        return cls(af, set(af.arguments), set(), set())

    @classmethod
    def all_OUT(cls, af):
        """ Return labelling where all arguments are labelled as OUT. """
        return cls(af, set(), set(af.arguments), set())

    @classmethod
    def all_UNDEC(cls, af):
        """ Return labelling where all arguments are labelled as UNDEC. """
        return cls(af, set(), set(), set(af.arguments))

    #Operations on labellings
    def intersection(self, other):
        lab = copy.deepcopy(self)
        lab.intersection_update(other)
        return lab

    def intersection_update(self, other):
        self.IN &= other.IN
        self.OUT &= other.OUT
        self._update_UNDEC()
        return self
    
    def union(self, other):
        lab = copy.deepcopy(self)
        lab.union_update(other)
        return lab
    
    def union_update(self, other):
        self.IN |= other.IN - self.OUT
        self.OUT |= other.OUT - self.IN
        self._update_UNDEC()
        return self
    
    def is_sublabelling(self, other):
        return (self.IN <= other.IN and
                self.OUT <= other.OUT and
                self.UNDEC <= other.UNDEC)
    
    def isLegallyOUT(self, arg):
        return arg.minus & self.IN
    
    def isLegallyIN(self, arg):
        return arg.minus <= self.OUT
    
    def is_legally_conlictfree_IN(self, arg):
        return arg.minus <= self.OUT and not arg.plus & self.IN
    
    def isLegallyUNDEC(self, arg):
        return not arg.minus & self.IN and arg.minus & self.UNDEC


################################################################################
# Roman

    @property
    def arguments(self):
        """ Return all arguments in this labeling. """
        args = set(self.IN | self.OUT | self.UNDEC)
        return args

    def is_in(self, arg):
        return arg in self.IN

    def is_out(self, arg):
        return arg in self.OUT

    def is_undec(self, arg):
        return arg in self.UNDEC

    def add_arg(self, arg, lab):
        lab = lab.upper()
        if lab == 'IN':
            self.IN.add(arg)
        elif lab == 'OUT':
            self.OUT.add(arg)
        elif lab == 'UNDEC':
            self.UNDEC.add(arg)
        else:
            raise IllegalArgument('The label "%s" does not exist' % lab)

    def label_for(self, arg):
        """ Returns status of argument """
        if arg in self.IN:
            return 'IN'
        elif arg in self.OUT:
            return 'OUT'
        elif arg in self.UNDEC:
            return 'UNDEC'
        else:
            raise IllegalArgument()

    def labelling_for(self, arg):
        lab = self.label_for(arg)
        res = Labelling(None, set(), set(), set())
        res.add_arg(arg, lab)
        return res

    def has_single_label(self):
        """ When the labelling contains arguments with the same label,
            return True. Otherwise, return False.

        """
        if (len(self.IN) == len(self)):
            return True
        elif (len(self.OUT) == len(self)):
            return True
        elif (len(self.UNDEC == len(self))):
            return True
        else:
            return False

    @property
    def label(self):
        """ When the labelling contains arguments with the same label, 
            return the label. Otherwise, rais MethodNotApplicable.
            
        """
        if (len(self.IN) == len(self)):
            return 'IN'
        elif (len(self.OUT) == len(self)):
            return 'OUT'
        elif (len(self.UNDEC) == len(self)):
            return 'UNDEC'
        else:
            raise MethodNotApplicable('Method "label" invoked on a labeling '
                                      'that contains more than one label: %s' %
                                      str(self))

    @property
    def argument(self):
        """ Return an argument in this labeling
            or raise MethodNotApplicable exception.

        """
        args = self.arguments
        if (len(args) != 1):
            raise MethodNotApplicable('Method "argument" invoked on labeling '
                                      'that does not have any arguments: %s' %
                                      str(self))
        return list(args)[0]

    def find_lowest_step(self, labelled_arguments):
        if len(labelled_arguments) == 0:
            raise IllegalArgument

        args = list()
        for la in labelled_arguments:
            args.append( (self.steps[la.argument], la))

        args = sorted(args, key=lambda x: x[0])
        return args[0][1]

    def find_argument(self, string):
        return self._framework.find_argument(string)

    def find_arguments_with_conclusion(self, concl_str):
        concl = Literal.from_str(concl_str)
        for arg in self.arguments:
            if arg.conclusion == concl: yield arg

    def is_valid_conclusion(self, conclusion):
        possible = list(self.find_arguments_with_conclusion(conclusion))
        if len(possible) == 0:
            print('E: No arguments with conclusion "%s"' % conclusion)
        for c in possible:
            if self.label_for(c) == 'IN':
                return True


################################################################################


    def down_admissible_update(self):
        while True:
            illigalIn = set([a for a in self.IN if not self.isLegallyIN(a)])
            illigalOut = set([a for a in self.OUT if not self.isLegallyOUT(a)])
            if not illigalIn and not illigalOut: return self
            self.IN -= illigalIn
            self.OUT -= illigalOut
            self.UNDEC |= illigalIn
            self.UNDEC |= illigalOut
    
    def up_complete_update(self):
        counter = 0
        while True:
            counter += 1
            legally_IN = set([a for a in self.UNDEC if self.isLegallyIN(a)])
            legally_OUT = set([a for a in self.UNDEC if self.isLegallyOUT(a)])
            if not legally_IN and not legally_OUT: return self
            self.IN |= legally_IN
            self.OUT |= legally_OUT
            self.UNDEC -= legally_IN
            self.UNDEC -= legally_OUT
            # assign the number of the step to the updated arguments
            this_step = legally_IN | legally_OUT
            for a in this_step:
                if a not in self.steps:
                    self.steps[a] = counter

    def up_complete_step(self):
        L = Labelling(self._framework, self.IN, self.OUT, self.UNDEC)
        legally_IN = set([a for a in L.UNDEC if L.isLegallyIN(a)])
        if legally_IN:
            L.IN |= legally_IN
            L.UNDEC.difference_update(legally_IN)
            legally_OUT = set([a for a in L.UNDEC if L.isLegallyOUT(a)])
            if legally_OUT:
                L.OUT |= legally_OUT
                L.UNDEC -= legally_OUT
            return L
        return False
    
    def diffargs(self, other):
        """return set of args on which labellings differ"""
        return (self.IN & other.OUT) | (self.IN & other.UNDEC) | \
            (self.OUT & other.IN) | (self.OUT & other.UNDEC) | \
            (self.UNDEC & other.IN) | (self.UNDEC & other.OUT)
    
    def split(self):
        """splits current labelling into single agrument labellings and returns as a list"""
        LL = []
        for a in self.IN: LL.append(self._framework.in_labelling([a]))
        for a in self.OUT: LL.append(self._framework.out_labelling([a]))
        for a in self.UNDEC: LL.append(self._framework.UNDEC_labelling([a]))
        return LL
    
    def __len__(self):
        return len(self.IN) + len(self.OUT) + len(self.UNDEC)
    
    def __sub__(self, other):
        return Labelling(self._framework,self.IN - other.IN, self.OUT - other.OUT, self.UNDEC - other.UNDEC)
    
    def __and__(self, other):
        return Labelling(self._framework,self.IN & other.IN, self.OUT & other.OUT, self.UNDEC & other.UNDEC)


################################################################################
# helpers

# TODO: reverse order of parameters
def is_in(labelling, arg):
    """ Check whether an argument is IN wrt to this labelling. """
    # an argument IN in if all of its attackers are OUT
    return ((arg.minus & labelling.OUT) == arg.minus)


def is_out(labelling, arg):
    """ Check whether an argument is OUT wrt to this labelling. """
    # argument is OUT if any of its attackers are IN
    return any(arg.minus & labelling.IN)


def is_undec(labelling, arg):
    """ Check whether an argument is UNDEC wrt to this labelling. """
    # an argument is UNDEC if non of its attackers are IN but not all are OUT
    return (not is_in(labelling, arg) and not is_out)

def assign_label_from(labelling, arg):
    if is_in(labelling, arg): return 'IN'
    elif is_out(labelling, arg): return 'OUT'
    elif is_undec(labelling, arg): return 'UNDEC'
    else: return None

def is_justified(lab_arg, labelling):
    """ Return true if the label is justified by the given labelling """
    if (len(lab_arg) == 0): return True # empty labelling
    if (lab_arg.argument.minus == set()): return True # not attackers
    return (lab_arg.label == assign_label_from(labelling, lab_arg.argument))


################################################################################


class ArgumentationFramework:
    def __init__(self, kb):
        self.debug = False
        self._arguments = dict()
        self.kb = kb
        if kb is not None:
            self._construct_graph(kb.arguments)

    @classmethod
    def from_arguments(cls, arguments):
        af = cls(None)
        af._construct_graph(arguments.values())
        return af

    @property
    def arguments(self):
        for a in self._arguments.values():
            yield a

    def find_argument(self, string):
        return self._arguments[string]
        
    def _construct_graph(self, arguments):
        # now go through the arguments and figure out the attacks
        arguments = list(arguments)
        for a1 in arguments:
            for a2 in arguments:
                if ((not a1.is_strict) and (not a2.is_strict)) :
                    self._check_undercut(a1, a2)
                    self._check_rebut(a1, a2)
                if (a1.is_strict and (not a2.is_strict)) :
                    self._check_undercut(a1, a2)
                    self._check_strict_rebut(a1, a2)
            a1._framework = self
            self._arguments[a1.name] = a1
    
    def _check_undercut(self, a1, a2):
        # a1 undercuts a2 if a2 has a rule with vulnerability that is neg a1
        if self.debug: print('undercuts for %s' % str(a1))
        for subargument in a2.subarguments:
            if (-a1.conclusion in subargument.vulnerabilities):
                a1.plus.add(a2)
                a2.minus.add(a1)
                break
    
    def _check_rebut(self, a1, a2):
        #weakest link approach
        defeasibles_1 = list(a1.get_defeasible_rules())
        defeasibles_2 = list(a2.get_defeasible_rules())
        weights_1 = list(map(lambda x: x.weight, defeasibles_1))
        weights_2 = list(map(lambda x: x.weight, defeasibles_2))
        w1 = min(weights_1)
        w2 = min(weights_2)
        
        # a1 rebuts a2 if one of the subarguments of a2 has an opposite concl.
        if self.debug: print('rebuts for %s' % str(a1))
        for subargument in a2.subarguments:
            if (-a1.conclusion == subargument.conclusion):
                # depending on the ordering rules...
                if not (w1 < w2):
                    a1.plus.add(a2)
                    a2.minus.add(a1)
    
    def _check_strict_rebut(self, a1, a2):
        if self.debug: print('rebuts for %s' % str(a1))
        for subargument in a2.subarguments:
            if (-a1.conclusion == subargument.conclusion):
                a1.plus.add(a2)
                a2.minus.add(a1)
    
    
    def __str__(self):
        tmp = lambda a: ('%s:\n\tattacking: %s\n\tattackers: %s'
                         % (str(a),
                            str(sorted([x.name for x in a.plus])),
                            str(sorted([x.name for x in a.minus]))))
        args = sorted(self.arguments, key=lambda x: x.name)
        return '\n'.join([ tmp(a) for a in args])
    
    def __repr__(self):
        return 'Argumentation Framework:\n%s' % str(self)
    
    def save_graph(self):
        self._save_graph(list(self.arguments))

    def save_interesting_graph(self):
        """ Only plot arguments that attack or are attacked by something. """
        is_interesting = lambda x: len(x.plus) > 0 or len(x.minus) > 0

        arguments = [x for x in self.arguments if is_interesting(x)]
        self._save_graph(arguments)

    def _save_graph(self, arguments):
        try:
            import pygraphviz as gv
            G = gv.AGraph(strict=False, directed=True)#, rankdir="LR"
            name = ''
            if self.kb is not None: name = self.kb.name
            G.graph_attr['label']="Argumentation Framework from KB\n'%s'" % name
            G.node_attr['shape']='circle'
            G.edge_attr['color']='blue'
            l = Labelling.grounded(self)

            for a in arguments:
                if is_in(l, a):
                    G.add_node(arg_to_str(a), color='green')
                elif is_out(l, a):
                    G.add_node(arg_to_str(a), color='red')
                elif is_undec(l, a):
                    G.add_node(arg_to_str(a), color='black')

            for a in arguments:
                for attacked in a.plus:
                    G.add_edge(arg_to_str(a), arg_to_str(attacked))

            G.layout(prog="dot")
            G.write("./af.dot")
            G.draw("./af.pdf", prog='dot')
        except Exception as e:
            print('Exception: %s' % str(e))


# helpers
################################################################################

def s2s(s):
    """convert set to string"""
    return "{%s}" % ", ".join([str(x) for x in s])


def arg_to_str(a):
    return '%s(%s)' % (a.name, str(a.rule))


# some instances for interactive testing
################################################################################

AF = ArgumentationFramework

#kb = KnowledgeBase.from_file('/Users/roman/Work/Aspic-/data/eg_tandem.txt')
#
#af = ArgumentationFramework(kb)
#
#af.save_graph()
