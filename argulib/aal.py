"""
    author: Roman Kutlak <roman@kutlak.net>

    Based on the Abstract Argumentation Library by
    Mikolaj Podlaszewski <mikolaj.podlaszewski@gmail.com>

"""

import copy
import json
import logging
from collections import defaultdict

from .common import IllegalArgument, MethodNotApplicable
from .kb import Literal, KnowledgeBase
from .signals import Signal

logger = logging.getLogger('arg.aaf')


# TODO: consider adding method `attach` that attaches kb/aaf to signal.


class Argument:
    """ Argument - based on Mikolaj Podlaszewski's code. """

    def __init__(self, proof, framework=None):
        self._framework = framework
        self.proof = proof  # the proof on which the argument is based
        self.plus = set()  # set of arguments being attacked by this argument
        self.minus = set()  # set of arguments attacking this argument

    @property
    def name(self):
        """ Return the name of the argument based on the name of the proof. """
        return self.proof.name

    @property
    def rule(self):
        """ Return the top rule used in the proof of this argument. """
        return self.proof.rule

    @property
    def rules(self):
        """ Return all rules used in the proofs. """
        return self.proof.rules

    @property
    def defeasible_rules(self):
        return self.proof.defeasible_rules

    @property
    def strict_rules(self):
        """ Return a generator containing all strict rules used in this arg. """
        return self.proof.strict_rules

    @property
    def consequent(self):
        """ Return the consequent (conclusion). """
        return self.proof.consequent

    @property
    def conclusion(self):
        """ Return the consequent (conclusion). """
        return self.proof.consequent

    @property
    def vulnerabilities(self):
        """ Return all possible vulnerabilities. """
        return self.proof.vulnerabilities

    @property
    def antecedents(self):
        return self.proof.antecedents

    @property
    def proofs(self):
        """ Return all proofs used by this argument including the top proof. """
        return self.proof.proofs

    @property
    def is_defeasible(self):
        """ Return True if the argument is based on a defeasible rule. """
        return self.proof.is_defeasible

    @property
    def is_strict(self):
        """ Return True if the argument is based ONLY on strict rules. """
        return self.proof.is_strict

    def __hash__(self):
        return hash(self.proof)

    def __eq__(self, other):
        return self.proof == other.proof

    def __lt__(self, other):
        """ Re-use the order of the proofs. """
        return self.proof < other.proof

    def __str__(self):
        return '%s: (%s)' % (self.name, str(self.rule))

    def __repr__(self):
        return '<Argument %s>' % str(self)

    def clear(self):
        """ Remove the attack relations. """
        self.plus.clear()
        self.minus.clear()


class ArgumentationFramework:
    _hash = None

    def __init__(self, kb):
        self.debug = False
        self.kb = kb or KnowledgeBase()
        self._arguments = defaultdict(set)  # {conclusion : {arguments}}
        if kb:
            # signals
            self.updated = Signal()
            # connect kb
            self.kb.updated.connect(self._kb_updated)
            # calculate graph and attacks
            self.reconstruct()

    def __str__(self):
        def helper(a):
            return ('%s:\n\tattacking: %s\n\tattackers: %s' % (
                str(a),
                str(sorted([x.name for x in a.plus])),
                str(sorted([x.name for x in a.minus]))))

        args = sorted(self.arguments, key=lambda x: x.name)
        return '\n'.join([helper(a) for a in args])

    def __repr__(self):
        return 'Argumentation Framework:\n%s' % str(self)

    def __hash__(self):
        """Return a hash. 
        
        Because the class uses signals, it has to be hashable.
        
        """
        if not self._hash:
            self._hash = hash(str(self))
        return self._hash

    @property
    def arguments(self):
        """ Return the generator listing all arguments in the framework. """
        for arguments in self._arguments.values():
            for a in arguments:
                yield a

    def find_argument_by_name(self, name):
        """ Return the argument with `name` or None. """
        for a in self.arguments:
            if a.name == name: return a
        return None

    def find_arguments_with_conclusion(self, conclusion):
        """ Return the set of arguments with the given conclusion or empty set.
        Method accepts a string or a Literal as a conclusion.
        
        """
        if isinstance(conclusion, str):
            conclusion = Literal.from_str(conclusion)
        if conclusion in self._arguments:
            return self._arguments[conclusion]
        else:
            return set()

    def _kb_updated(self, proofs, added):
        """ KB was updated, reconstruct the graph and attack relations. """
        logger.debug('KB updated -- recalculating AAF')
        if proofs:
            if added:
                self._construct_arguments(proofs)
            else:
                self.reconstruct()

    def reconstruct(self):
        """Reconstruct the argument graph from the knowledge base. """
        self._arguments.clear()
        self._construct_arguments(self.kb.proofs)

    def _construct_arguments(self, proofs):
        """ Construct the graph of the arguments for given proofs. """
        if not proofs: return
        logger.debug('Constructing arguments...')
        for p in proofs:
            a = Argument(p, self)
            self._arguments[a.consequent].add(a)
        self.calculate_attacks()

    def calculate_attacks(self):
        """ Take the existing arguments and create the attacks. """
        logger.debug('Reconstructing the attacks...')
        # clear the attack relations first
        arguments = list(sorted(self.arguments))
        for a in arguments: a.clear()
        for a1 in arguments:
            for a2 in arguments:
                if a2.is_strict or a1 == a2: continue
                self._check_undercut(a1, a2)
                self._check_rebut(a1, a2)
        logger.debug('Argumentation framework reconstructed.')
        self.updated()

    # TODO: add the proof which is being attacked to `plus` and `minus`

    def _check_undercut(self, a1, a2):
        # a1 undercuts a2 if a2 has a rule with vulnerability that is neg a1
        logger.debug('checking undercuts for (%s) and (%s)', a1, a2)
        for proof in a2.proofs:
            if -a1.conclusion in proof.vulnerabilities:
                a1.plus.add(a2)
                a2.minus.add(a1)
                break

    def _check_rebut(self, a1, a2):
        # weakest link approach
        logger.debug('checking rebut for (%s) and (%s)', a1, a2)
        # a1 rebuts a2 if one of the subproofs of a2 has an opposite concl.
        for proof in a2.proofs:
            if -a1.conclusion == proof.conclusion:
                if not (self.more_preferred(proof.weakest_link, a1.proof.weakest_link)):
                    logger.debug('...rebut accepted')
                    a1.plus.add(a2)
                    a2.minus.add(a1)

    def more_preferred(self, a, b):
        """ Return True if according to the KB a is preferred over b. """
        result = self.kb.more_preferred(a, b)
        logger.debug('{0} is {1}more preferred than {2}'
                     .format(a, ('' if result else 'not '), b))
        return result

    def save_graph(self):
        self._save_graph(list(self.arguments))

    def save_interesting_graph(self, path='af.pdf'):
        """ Only plot arguments that attack or are attacked by something. """

        def is_interesting(x):
            return len(x.plus) > 0 or len(x.minus) > 0

        arguments = [x for x in self.arguments if is_interesting(x)]
        self._save_graph(arguments)

    def _save_graph(self, arguments):
        try:
            import pygraphviz as gv
            G = gv.AGraph(strict=False, directed=True)  # , rankdir="LR"
            name = ''
            if self.kb is not None: name = self.kb.name
            G.graph_attr['label'] = "Argumentation Framework from KB\n'%s'" % name
            G.node_attr['shape'] = 'oval'
            G.edge_attr['color'] = 'blue'
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
                    # FIXME: change arg_to_str to attack_to_str
                    G.add_edge(arg_to_str(a), arg_to_str(attacked))

            G.layout(prog="dot")
            G.write("./af.dot")
            G.draw("./af.pdf", prog='dot')
        except Exception as e:
            print('Exception: %s' % str(e))


class Labelling:
    """Labelling (possibly partial)"""
    framework, IN, OUT, UNDEC = None, None, None, None

    def __init__(self, frame, IN=None, OUT=None, UNDEC=None):
        self.steps = dict()
        self.framework = frame or ArgumentationFramework(None)
        self.IN = IN or set()
        self.OUT = OUT or set()
        self.UNDEC = UNDEC
        if self.UNDEC is None:
            self._update_undecided()
        # link to the aaf
        if frame:
            # signals
            self.updated = Signal()
            self.framework.updated.connect(self._framework_updated)

    def __hash__(self):
        """Return a hash (needed for signals)."""
        if not hasattr(self, 'hash'):
            self.hash = hash(self.framework)
        return self.hash

    def to_dict(self):
        return {
            'IN': [x.name for x in self.IN],
            'OUT': [x.name for x in self.OUT],
            'UNDEC': [x.name for x in self.UNDEC],
        }

    @classmethod
    def from_dictcls(cls, aaf, data):
        return cls(aaf,
                   data['IN'],
                   data['OUT'],
                   data['UNDEC'])

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

    @classmethod
    def inverse(cls, labelling):
        """ Create labelling for single argument where the labe is inverse. """
        lab = labelling.label
        arg = labelling.argument
        if 'OUT' == lab:
            inv_lab = 'IN'
        elif 'IN' == lab:
            inv_lab = 'OUT'
        else:
            inv_lab = 'UNDEC'

        l = Labelling.empty()
        l.add_arg(arg, inv_lab)
        return l

    @classmethod
    def empty(cls):
        """ Return new empty labelling. """
        return cls(None, set(), set(), set())

    @classmethod
    def grounded(cls, af):
        """ Return grounded labeling created from a framework. """
        return cls.all_UNDEC(af).up_complete_update()

    @classmethod
    def from_argument(cls, arg, label):
        """ Return labelling with one argument. """
        l = Labelling.empty()
        l.add_arg(arg, label)
        return l

    def _framework_updated(self):
        logger.debug('Framework updated -- reload labelling.')
        self.UNDEC = set(self.framework.arguments)
        self.IN.clear()
        self.OUT.clear()
        self.up_complete_update()
        self.updated()

    def _update_undecided(self):
        """Updates UNDEC so that it contains arguments not present in IN and OUT """
        self.UNDEC = set(self.framework.arguments)
        self.UNDEC.difference_update(self.IN, self.OUT)

    def __eq__(self, other):
        if not isinstance(other, Labelling): return False
        return (self.IN == other.IN and
                self.OUT == other.OUT and
                self.UNDEC == other.UNDEC)

    def __repr__(self):
        _in = sorted(a.name for a in self.IN)
        _out = sorted(a.name for a in self.OUT)
        _undecided = sorted(a.name for a in self.UNDEC)
        return "Labelling: ({%s},{%s},{%s})" % (', '.join(_in),
                                                ', '.join(_out),
                                                ', '.join(_undecided))

    def __str__(self):
        """Dialogue string representation: in(a,b)"""
        res = [
            'in(%s)' % ','.join(sorted(a.name for a in self.IN)),
            'out(%s)' % ','.join(sorted(a.name for a in self.OUT)),
            'undec(%s)' % ','.join(sorted(a.name for a in self.UNDEC))
        ]
        return ' '.join(res) if res else '-'

    def get_label(self, arg):
        """Returns status of argument"""
        if arg in self.IN:
            return "IN"
        elif arg in self.OUT:
            return "OUT"
        else:
            return "UNDEC"

    def set_label(self, arg, status):
        if status not in ('IN', 'OUT', 'UNDEC'):
            raise Exception("Wrong status: %s" % status)
        self.IN.discard(arg)
        self.OUT.discard(arg)
        self.UNDEC.discard(arg)
        if status == "IN":
            self.IN.add(arg)
        elif status == "OUT":
            self.OUT.add(arg)
        elif status == "UNDEC":
            self.UNDEC.add(arg)

    # Operations on labellings
    def intersection(self, other):
        lab = copy.deepcopy(self)
        lab.intersection_update(other)
        return lab

    def intersection_update(self, other):
        self.IN &= other.IN
        self.OUT &= other.OUT
        self._update_undecided()
        return self

    def union(self, other):
        lab = copy.deepcopy(self)
        lab.union_update(other)
        return lab

    def union_update(self, other):
        self.IN |= other.IN - self.OUT
        self.OUT |= other.OUT - self.IN
        self._update_undecided()
        return self

    def is_sublabelling(self, other):
        return (self.IN <= other.IN and
                self.OUT <= other.OUT and
                self.UNDEC <= other.UNDEC)

    def is_legally_out(self, arg):
        return arg.minus & self.IN

    def is_legally_in(self, arg):
        return arg.minus <= self.OUT

    def is_legally_conlictfree_IN(self, arg):
        return arg.minus <= self.OUT and not arg.plus & self.IN

    def is_legally_undecided(self, arg):
        return not arg.minus & self.IN and arg.minus & self.UNDEC

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
        res = Labelling.from_argument(arg, lab)
        return res

    def has_single_label(self):
        """ When the labelling contains arguments with the same label,
            return True. Otherwise, return False.

        """
        try:
            _ = self.label
            return True
        except MethodNotApplicable:
            return False

    @property
    def label(self):
        """ When the labelling contains arguments with the same label, 
            return the label. Otherwise, rais MethodNotApplicable.
            
        """
        if len(self.IN) == len(self):
            return 'IN'
        elif len(self.OUT) == len(self):
            return 'OUT'
        elif len(self.UNDEC) == len(self):
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
        if len(args) != 1:
            raise MethodNotApplicable('Method "argument" invoked on labeling '
                                      'that does not have any arguments: %s' %
                                      str(self))
        return list(args)[0]

    def find_lowest_step(self, labelled_arguments):
        if len(labelled_arguments) == 0:
            raise IllegalArgument

        args = list()
        for la in labelled_arguments:
            args.append((self.steps[la.argument], la))

        args = sorted(args, key=lambda x: x[0])
        return args[0][1]

    def find_argument(self, string):
        return self.framework.find_argument(string)

    def find_arguments_with_conclusion(self, conclusion_str):
        conclusion = Literal.from_str(conclusion_str)
        for arg in self.arguments:
            if arg.conclusion == conclusion:
                yield arg

    def is_valid_conclusion(self, conclusion):
        possible = list(self.find_arguments_with_conclusion(conclusion))
        if len(possible) == 0:
            print('E: No arguments with conclusion "%s"' % conclusion)
        for c in possible:
            if self.label_for(c) == 'IN':
                return True


    def down_admissible_update(self):
        while True:
            illigalIn = set([a for a in self.IN if not self.is_legally_in(a)])
            illigalOut = set([a for a in self.OUT if not self.is_legally_out(a)])
            if not illigalIn and not illigalOut: return self
            self.IN -= illigalIn
            self.OUT -= illigalOut
            self.UNDEC |= illigalIn
            self.UNDEC |= illigalOut

    def up_complete_update(self):
        counter = 0
        while True:
            counter += 1
            legally_IN = set([a for a in self.UNDEC if self.is_legally_in(a)])
            legally_OUT = set([a for a in self.UNDEC if self.is_legally_out(a)])
            if not legally_IN and not legally_OUT:
                for a in self.UNDEC:
                    if a not in self.steps:
                        self.steps[a] = counter
                # done -- notify listeners
                self.updated()
                return self
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
        L = Labelling(self.framework, self.IN, self.OUT, self.UNDEC)
        legally_IN = set([a for a in L.UNDEC if L.is_legally_in(a)])
        if legally_IN:
            L.IN |= legally_IN
            L.UNDEC.difference_update(legally_IN)
            legally_OUT = set([a for a in L.UNDEC if L.is_legally_out(a)])
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
        for a in self.IN:
            LL.append(self.framework.in_labelling([a]))
        for a in self.OUT:
            LL.append(self.framework.out_labelling([a]))
        for a in self.UNDEC:
            LL.append(self.framework.UNDEC_labelling([a]))
        return LL

    def __len__(self):
        return len(self.IN) + len(self.OUT) + len(self.UNDEC)

    def __sub__(self, other):
        return Labelling(self.framework, self.IN - other.IN, self.OUT - other.OUT, self.UNDEC - other.UNDEC)

    def __and__(self, other):
        return Labelling(self.framework, self.IN & other.IN, self.OUT & other.OUT, self.UNDEC & other.UNDEC)


# helpers

# TODO: reverse order of parameters
def is_in(labelling, arg):
    """ Check whether an argument is IN wrt to this labelling. """
    # an argument IN in if all of its attackers are OUT
    return (arg.minus & labelling.OUT) == arg.minus


def is_out(labelling, arg):
    """ Check whether an argument is OUT wrt to this labelling. """
    # argument is OUT if any of its attackers are IN
    return any(arg.minus & labelling.IN)


def is_undec(labelling, arg):
    """ Check whether an argument is UNDEC wrt to this labelling. """
    # an argument is UNDEC if non of its attackers are IN but not all are OUT
    return not is_in(labelling, arg) and not is_out


def assign_label_from(labelling, arg):
    if is_in(labelling, arg):
        return 'IN'
    elif is_out(labelling, arg):
        return 'OUT'
    elif is_undec(labelling, arg):
        return 'UNDEC'
    else:
        return None


def is_justified(lab_arg, labelling):
    """ Return true if the label is justified by the given labelling """
    if len(lab_arg) == 0:
        return True  # empty labelling
    return lab_arg.label == assign_label_from(labelling, lab_arg.argument)


def s2s(s):
    """convert set to string"""
    return "{%s}" % ", ".join([str(x) for x in s])


def arg_to_str(a):
    return '%s(%s)' % (a.name, str(a.rule))
