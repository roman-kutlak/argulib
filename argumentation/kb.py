import logging
import copy
import itertools
import functools
from collections import defaultdict

import pyparsing
from pyparsing import Word, Group, Optional, alphanums, alphas, delimitedList

from .signals import Signal
from .common import Graph


def get_log():
    return logging.getLogger('arg.kb')


""" Structures and functions for reading a knowledge base of rules for 
    constructing argument networks. 

"""


class ParseError(Exception):
    """ Thrown when parsing fails. """
    pass


class RuleError(Exception):
    pass


class TypeError(Exception):
    pass


class Literal:
    """ The class represents a literal (possibly negated).

    The main purpose of the class is to enforce naming conventions.
    Literals follow C naming conventions - start with a letter
    optionally followed by alphanums + '_'.

    To create a Literal instance from string use Literal.from_str(x). If
    a literal is to be negated, the identifier should start with '-' (eg, -p).
    The parser is not smart enough to parse "--p" as "p".

    """
    def __init__(self, name, negated=False):
        """ Create a literal with a name.
        Keyword arguments:
        negated - is the literal negated (eg, not a; default false)
        
        """
        self.name = name
        self.negated = negated
    
    def __eq__(self, other):
        """ Compare with a literal or a string. """
        if isinstance(other, str):
            try:
                other = Literal.from_str(other)
            except Exception:
                return False
        return (isinstance(other, Literal) and
                self.name == other.name and
                self.negated == other.negated)
    
    def __lt__(self, other):
        if self.name == other.name:
            return (self.negated < other.negated)
        else:
            return (self.name < other.name)

    def __neg__(self):
        return Literal(self.name, not self.negated)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        string = ''
        if self.negated: string += '-'
        string += self.name
        return string
    
    def __repr__(self):
        return ("Literal: %s" % str(self))

    @classmethod
    def from_str(cls, data):
        params = data
        if isinstance(data, str):
            data = data.strip()
            try:
                parsed = literal.parseString(data, parseAll=True)
                params = parsed[0]
            except pyparsing.ParseException as ex:
                raise ParseError(ex)
        if (len(params) == 1):
            return cls(params[0])
        elif (len(params) == 2):
            return cls(params[1], True)
        else:
            raise ParseError('Data mallformed: "%s"' % data)


def check_list_of_type(lst, cls, msg=''):
    """ Check that the given list contains only instances of cls.
    Raise TypeException if an element is not of the given type.
    If the list is None, an empty list is returned.

    :param lst: list of items or None
    :param cls: the class of which the elements should be instances
    :returns: the passed list
    """
    if lst is None: return []
    for o in lst:
        if not isinstance(o, cls):
            if not msg:
                msg = ('Elements of the list must be instances of {cls}'
                        .format(cls=str(cls)))
            raise TypeError(msg)
    if not isinstance(lst, list):
        return list(lst)
    return lst


# types of rules

STRICT_RULE = 0
DEFEASIBLE_RULE = 1


class StrictRule:
    """ The class represents a strict rule (a modus ponens). """

    def __init__(self, antecedent, consequent, name=''):
        """ A rule has to have antecedent and a consequent.
        antecedent -- a list of Literals or None
        consequent -- a Literal
        name -- an optional name (default = '')
            
        """
        self.type = STRICT_RULE
        self.name = name
        # do some error checking to be nice
        self.antecedent = check_list_of_type(antecedent, Literal,
                                'Antecedent must be a list of Literals')
        self.antecedent.sort() # it is essential that the list is sorted!
        if consequent is None:
            raise RuleError("Rule has to have a consequence (None provided)")
        else:
            if not isinstance(consequent, Literal):
                raise RuleError("Consequent must be a Literal")
            self.consequent = consequent

    def __eq__(self, other):
        """ Two rules are equal if they are the same type 
        and contain the same antecedent and the same consequent.
        Name does not matter.
        
        """
        return (self.type == other.type and
                self.antecedent == other.antecedent and
                self.consequent == other.consequent)

    def __len__(self):
        """ The length of the rule is given by the number of antecedents. """
        return len(self.antecedent)

    def __hash__(self):
        """ Just like equals, the hash only uses the antecedent and consequent.
        
        """
        if not hasattr(self, 'hash'):
            value = hash(self.consequent)
            for a in self.antecedent:
                value ^= hash(a)
            self.hash = value
        return self.hash

    def __lt__(self, other):
        """ self < other if self has fewer antecedents or if they are
        alphabetically before other.
        
        """
        if other.type == DEFEASIBLE_RULE: return False
        ls = len(self.antecedent)
        lo = len(other.antecedent)
        if ls != lo:
            return ls < lo
        else:
            return str(self) < str(other)

    def __str__(self):
        name = ''
        if self.name:
            name = self.name + ': '
        return ('{name}{antecedent} --> {consequent}'
                .format(name=name,
                        antecedent=', '.join(map(str, self.antecedent)),
                        consequent=str(self.consequent)))

    def __repr__(self):
        return ('StrictRule ' + str(self))

    def is_strict(self):
        return True

    def is_defeasible(self):
        return False

    @classmethod
    def from_str(cls, data):
        if not isinstance(data, str):
            raise ParseError('"%s" is not a string' % repr(data))
        try:
            parsed = strict_rule.parseString(data, parseAll=True)
            if 'name' in parsed:
                name = parsed['name']
            else:
                name = ''
            antecedent = None
            if 'antecedent' in parsed:
                antecedent = list(map(Literal.from_str, parsed['antecedent']))
            else:
                antecedent = []
            consequent = Literal.from_str(parsed['consequent'][0])
            return cls(antecedent, consequent, name)
        except Exception as e:
            raise ParseError('"%s" is not a strict rule\n\t error: %s'
                             % (data, str(e)))


class DefeasibleRule:
    """ The class represents a defeasible rule.
    The difference between a strict and a defeasible rule is that defeasible 
    rule captures "the most frequent case". E.g., A ==> B means that
    A usually implies B.
    
    Defeasible rules can have exceptions (vulnerabilities) specified in 
    parenthesis between the arrow: A =(-C)=> B means that A usually implies B
    unless C is true. (E.g., an object is red if it looks red unless we shine 
    on it a red light.)
        
    """
    
    def __init__(self, antecedent, consequent, vulnerabilities=None, name=''):
        """ A rule has to have antecedent and a consequent.
        antecedent -- a list of Literals or None
        consequent -- a Literal
        vulnerabilities -- a list of Literals or None (default)
        name -- an optional name (default = '')

        """
        self.type = DEFEASIBLE_RULE
        self.name = name
        # do some error checking to be nice
        self.antecedent = check_list_of_type(antecedent, Literal,
                                'Antecedent must be a list of Literals')
        self.antecedent.sort() # it is essential that the list is sorted!
        
        if not isinstance(consequent, Literal):
            raise RuleError('Consequent must be a Literal but was {t}'
                            .format(type(consequent)))
        self.consequent = consequent

        self.vulnerabilities = check_list_of_type(vulnerabilities, Literal,
                  'Vulnerabilities must be list of Literals')
        self.vulnerabilities.sort()

    def __eq__(self, other):
        """ Two rules are equal if they are the same type (rule.type == 
        DEFEASIBLE_RULE) and contain the same antecedent, the same consequent
        and the same vulnerabilities. Name does not matter.
        
        """
        return (self.type == other.type and
                self.antecedent == other.antecedent and
                self.consequent == other.consequent and
                self.vulnerabilities == other.vulnerabilities)
    
    def __len__(self):
        """ The length of the rule is given by the number of antecedents. """
        return len(self.antecedent)
    
    def __hash__(self):
        """ Just like equals, the hash only uses the antecedent and consequent
        and the vulnerabilities.
        
        """
        if not hasattr(self, 'hash'):
            value = hash(self.consequent)
            for a in self.antecedent:
                value ^= hash(a)
            for a in self.vulnerabilities:
                value ^= hash(a)
            self.hash = value
        return self.hash

    def __lt__(self, other):
        """ self < other if self has fewer antecedents, or 
        fewer vulnerabilities or 
        if str(self) is alphabetically before str(other).
        
        """
        if other.type == STRICT_RULE: return True
        ls = len(self.antecedent)
        lo = len(other.antecedent)
        if ls != lo:
            return ls < lo
        else:
            ls = len(self.vulnerabilities)
            lo = len(other.vulnerabilities)
            if ls != lo:
                return ls < lo
            else:
                return str(self) < str(other)
    
    def __str__(self):
        if self.name:
            text = ('%s: ' % self.name)
        else:
            text = ''
        if (len(self.antecedent) > 0):
            text += ', '.join(map(str, self.antecedent))
        if (len(self.vulnerabilities) > 0):
            text += (' =(%s)=> ' % ', '.join(map(str, self.vulnerabilities)))
        else:
            text += ' ==> '
        text += str(self.consequent)
        return text

    def __repr__(self):
        return ('DefeasibleRule %s' % str(self))
        
    def is_strict(self):
        return False

    def is_defeasible(self):
        return True
    
    @classmethod
    def from_str(cls, data):
        if not isinstance(data, str):
            raise ParseError('"%s" is not a string' % repr(data))
        try:
            parsed = defeasible_rule.parseString(data, parseAll=True)
            if 'name' in parsed:
                name = parsed['name']
            else:
                name = ''
            antecedent = None
            if 'antecedent' in parsed:
                antecedent = list(map(Literal.from_str, parsed['antecedent']))
            else:
                antecedent = []
            consequent = Literal.from_str(parsed['consequent'][0])
            if 'vulnerabilities' in parsed:
                vulners = list(map(Literal.from_str, parsed['vulnerabilities']))
            else:
                vulners = list()
            return cls(antecedent, consequent, vulners, name)
        except Exception as e:
            raise ParseError('"%s" is not a defeasible rule\n\tError: %s'
                             % (repr(data), str(e)))


# TODO: implement a class for ordering


def make_rule(rule):
    """ Take a string and create an a Strict or a Defeasible rule. """
    if isinstance(rule, str):
        if '->' in rule:
            rule = StrictRule.from_str(rule)
        elif '=>' in rule:
            rule = DefeasibleRule.from_str(rule)
        else:
            raise ParseError('"%s" is not a valid rule' % rule)
        return rule
    else:
        msg = 'make_rule expects a string but received "%s"'
        raise TypeError(msg % repr(rule))


class Proof:
    """ A proof leading to a particular consequent. """

    def __init__(self, name, rule, proofs):
        """ Create an instance of a proof concluding "consequent" given 
        the rule and proofs for the antecedents of the rule.
        
        """
        self.name = name
        self.rule = rule
        self._proofs = proofs
        self.strict = all(map(lambda x: x.is_strict(), self.rules))

    def __str__(self):
        s = ' ∧ '.join(map(str, self.subproofs))
        if not self.has_empty_antecedent(): s = '(' + s  + ')'+ ' → '
        s += str(self.rule)
        return s.strip()

    __repr__ = __str__
    
    def __eq__(self, other):
        """ Two proofs are equal if they have the same top rule and the same 
        sub-proofs.
        
        """
        return (self.rule == other.rule and
                self._proofs == other._proofs)

    def __hash__(self):
        if not hasattr(self, 'hash'):
            value = hash(self.rule)
            for p in self._proofs.values():
                value ^= hash(p)
            self.hash = value
        return self.hash
        
    def __len__(self):
        """ Return the number of rules involved in this proof. """
        max_len = list(map(len, self.subproofs))
        return 1 + max(max_len + [0])

    def __lt__(self, other):
        """ Order by length, name. """
        l1 = len(self)
        l2 = len(other)
        if l1 == l2:
            return self.name < other.name
        else:
            return l1 < l2

    @property
    def antecedents(self):
        """ Yield the antecedents of this proof. """
        return self.rule.antecedents

    @property
    def consequent(self):
        """ Return the consequent of this proof. """
        return self.rule.consequent

    @property
    def conclusion(self):
        """ Return the consequent of this proof. """
        return self.rule.consequent

    @property
    def vulnerabilities(self):
        """ Return the vulnerabilities of this proof.
        
        """
        if self.rule.is_strict(): return []
        return self.rule.vulnerabilities

    @property
    def subproofs(self):
        """ Yield the proofs used by the top rule only. """
        return self._proofs.values()

    @property
    def proofs(self):
        """ Return the set of all proofs used by this proof. """
        tmp = map(lambda x: x.proofs, self.subproofs) # sets of subproofs
        proofs = functools.reduce(lambda x, y: x | y, tmp, set()) # collect them
        proofs.add(self) # add self
        return proofs

    @property
    def rules(self):
        """ Return the generator of all rules including the top one. """
        return map(lambda x: x.rule, self.proofs)
    
    @property
    def strict_rules(self):
        """ Return all strict rules used in this proof and its subproofs. """
        return filter(lambda r: r.type == STRICT_RULE, self.rules)
            
    @property
    def defeasible_rules(self):
        """ Return all defeasible rules used in this proof and its subproofs."""
        return filter(lambda r: r.type == DEFEASIBLE_RULE, self.rules)
    
    def has_empty_antecedent(self):
        """ Return True if the proof does not have any antecedents. """
        return len(self._proofs) == 0

    def is_strict(self):
        """ Return true if the proof only uses strict rules. 
        A proof is strict if all of the antecedents are strict and the rule 
        is strict.
        """
        return self.strict

    def is_defeasible(self):
        """ Return True if the proof is not strict. """
        return (not self.is_strict())

    def uses_rule(self, rule):
        """ Returns True if any of the proofs use the given rule. """
        return any(map(lambda x: x == rule, self.rules))

    def uses_consequent(self, consequent):
        """ Returns True if any of the proofs leads to the given consequent. """
        return any(map(lambda x: x.consequent == consequent, self.rules))


class KnowledgeBaseError(Exception):
    """ Thrown when construction of knowledge base fails. """
    pass

class KnowledgeBase:
    """ A class that represents the knowledge base of rules. """

    def __init__(self, name=''):
        self.name = name
        self._rules  = defaultdict(set) # consequent : [rule]
        self._prefs  = Graph() # directed acyclic graph storing partial order
        self._proofs = defaultdict(set) # consequent : [proofs]
        # working memory -- inferred rules + user rules
        self._wm = defaultdict(set) # consequent : [rule]
        # signals
        self.rules_added = Signal()
        self.rules_deleted = Signal()
        self.updated = Signal()
        # index for creating proofs
        self.proof_idx = 0
        # if True, proofs are not generated -- for batch adding/deleting
        self.batch = False
    
    @classmethod
    def from_file(cls, file_name):
        if file_name is None:
            return cls()
        kb = cls(file_name)
        kb.read_file(file_name)
        return kb
    
    def __eq__(self, other):
        # it is easier to compare the stirngs as the KBs can differ in proofs
        # because removing a proof still leaves the key with an empty set in
        # the `_proofs` dict.
        return (str(self) == str(other))

    def __str__(self):
        strict = list(self.get_strict_rules())
        defeasible = list(self.get_defeasible_rules())
        proofs = list(self.proofs)
        # sort the rules for easy reading
        defeasible.sort()
        strict.sort()
        proofs.sort()
    
        s = 'Name: "%s"\n' % self.name
        s += ('Strict Rules:\n\t%s\n' %
              '\n\t'.join(map(str, strict)))
        s += ('Defeasible Rules:\n\t%s\n' %
              '\n\t'.join(map(str, defeasible)))
        s += ('Proofs:\n\t%s\n' %
              '\n\t'.join(map(str, proofs)))
        s += ('Preferences:\n\t%s' %
              '\n\t'.join(map(lambda x: '%s > %s' % x, self._prefs.edges)))
        return s
    
    __repr__ = __str__
    
    @property
    def rules(self):
        """ Return a generator of rules in the KB (in working memory). """
        for rules in self._wm.values():
            for r in rules:
                yield r

    @property
    def proofs(self):
        """ Return a generator of proofs in the knowledge base. """
        for proofs in self._proofs.values():
            for p in proofs:
                yield p

    def proofs_for(self, conclusion):
        """Return the set of proofs for `conclusion`. """
        return self._proofs[conclusion]

    def construct_rule(self, line):
        """ Construct a new rule from the given string and add it to the kb. 
        
        either string describing a rule (a parse error thrown if
        not formatted correctly) or a Rule (strict or defeasible).
        
        """
        if '->' in line:
            self.add_rule(make_rule(line))
        elif '=>' in line:
            self.add_rule(make_rule(line))
        elif '<' in line:
            self.add_preference_rules(line)
        else:
            raise KnowledgeBaseError('"%s" is not a rule.' % line)
    
    def add_rule(self, rule, recalc=True):
        """ Try to add a new rule in the knowledge base.
        
        Strict rule might raise KBError if it would
        make the knowledge base inconsistent.
        
        rule --  Stric or Defeasible rule
        
        """
        get_log().debug('adding rule "%s"' % str(rule))
        if STRICT_RULE == rule.type:
            self._add_strict_rule(rule)
        elif DEFEASIBLE_RULE == rule.type:
            self._add_defeasible_rule(rule)
        else:
            msg = 'Unknown rule type for rule "%s"'
            raise KnowledgeBaseError(msg % str(rule))
    
    def _add_strict_rule(self, rule):
        get_log().debug('  _adding strict rule "%s"' % str(rule))
        if not rule.type == STRICT_RULE:
            raise KnowledgeBaseError('Tried to insert a non strict rule.')
        closure = self.contrapositions(rule)
        all = {rule} | closure
        # create new proofs
        new_proofs = self.construct_proofs(self._proofs, all)
        # check that the new proofs are consistent with the current KB
        self.check_consistency(new_proofs)
        # add to the list of rules
        self._rules[rule.consequent].add(rule)
        # add to the working memory
        for r in all:
            self._wm[r.consequent].add(r)
        # add the proofs
        for p in new_proofs:
             self._proofs[p.conclusion].add(p)
        # emit signals
        self.rules_added(all)
        self.updated(new_proofs)

    def _add_defeasible_rule(self, rule):
        get_log().debug('  _adding defeasible rule "%s"' % str(rule))
        if not rule.type == DEFEASIBLE_RULE:
            raise KnowledgeBaseError('Tried to insert a non defeasible rule.')
        self._rules[rule.consequent].add(rule)
        self._wm[rule.consequent].add(rule)
        # create new proofs
        new_proofs = self.construct_proofs(self._proofs, {rule})
        # add the proofs
        for p in new_proofs:
             self._proofs[p.conclusion].add(p)
        # emit signals
        self.rules_added({rule})
        self.updated(new_proofs)

    def del_rule(self, rule):
        """ Delete the given rule and all proofs that use this rule. """
        # if passed as a string, parse it first
        if isinstance(rule, str): rule = make_rule(rule.strip())
        get_log().debug('_deleting rule "%s"' % str(rule))
        if STRICT_RULE == rule.type: self._del_strict_rule(rule)
        elif DEFEASIBLE_RULE == rule.type: self._del_defeasible_rule(rule)
        else:
            msg = 'Unknown rule type for rule "%s"'.format(str(rule))
            raise KnowledgeBaseError(msg)

    def _del_strict_rule(self, rule):
        get_log().debug('  _deleting strict rule "%s"' % str(rule))
        if not rule.consequent in self._rules: return
        # if the rule is in _rules, it has to be in _wm as well
        closure = self.contrapositions(rule)
        all = {rule} | closure
        # proofs that use the rule should also be deleted
        proofs = set()
        # delete the rule + contrapositions from working memory
        for r in all:
            if r.consequent in self._wm:
                self._wm[r.consequent].remove(r)
                for p in self.proofs:
                    if p.uses_rule(r):
                        proofs.add(p)
        for p in proofs:
            self._proofs[p.consequent].remove(p)
        # delete the rule
        self._rules[rule.consequent].remove(rule)
        # emit signals
        self.rules_deleted(closure)
        self.updated(proofs)

    def _del_defeasible_rule(self, rule):
        get_log().debug('  _deleting defeasible rule "%s"' % str(rule))
        if not rule.consequent in self._rules: return
        # if the rule is in _rules, it has to be in _wm as well
        self._wm[rule.consequent].remove(rule)
        proofs = set()
        for p in self.proofs:
            if p.uses_rule(rule):
                proofs.add(p)
        for p in proofs:
            self._proofs[p.consequent].remove(p)
        self._rules[rule.consequent].remove(rule)
        # emit signals
        self.rules_deleted({rule})
        self.updated(proofs)

    def contrapositions(self, rule):
        """ Create a set of contraposition rules.
        Every strict rule have corresponding contraposition rules.
        For example:
            a --> b also means that -b --> -a
            p, q --> r has p, -r --> -q and -r, q --> -p
        
        """
        get_log().debug('  contrapositions for rule: %s' % rule)
        rules = set()
        nc = -(rule.consequent) # negation of the consequent
        idx = 0
        for a in rule.antecedent:
            idx += 1
            antecedent = [i for i in rule.antecedent if i != a]
            antecedent.append(nc)
            r = StrictRule(antecedent, -a)
            if r.name != '':
                r.name = '%s-%d' % (rule.name, idx)
            rules.add(r)
            get_log().debug('\tcreated contraposition : %s' % r)
        return rules

    def construct_proofs(self, existing_proofs, rules):
        """ Return the set of new proofs given the existing proofs 
        and new rules.
        
        existing_proofs -- a dict of proofs: {conclusion: {proofs} }
        rules -- a set of rules: {rule}
        """
        # if we are batch processing, don't add any proofs
        if self.batch: return set()
        get_log().debug('constructing proofs for rules \n\t%s'
                        % '\n\t'.join(map(str, rules)))
        new_proofs = set()
        inferred = set() # new conclusions
        old_size = -1
        rules = sorted(rules)
        all_proofs = copy.copy(existing_proofs) # shallow copy is sufficient
        num_steps = 0
        while (old_size != len(new_proofs)):
            # how many proofs we are starting from in this iteration
            old_size = len(new_proofs)
            num_steps += 1
            for r in rules:
                get_log().debug('Current rule %s' % repr(r))
                # can we skip this rule, because no new conclusions affect it?
                if num_steps > 1 and (not inferred & set(r.antecedent)):
                    # none of the inferred conclusions is in the antecedent
                    get_log().debug('...this rule has no new proofs')
                    continue
                get_log().debug('...this rule might have new proofs')
                # find a proof for each antecedent
                subproofs = dict()
                for a in r.antecedent:
                    if a in all_proofs:
                        subproofs[a] = all_proofs[a]
                    else:
                        break
                # do we have a proof for all antecedents?
                if len(subproofs) == len(r.antecedent):
                    tmp = self._create_proofs(r, subproofs)
                    new_proofs |= tmp
                    inferred |= set(map(lambda p: p.conclusion, new_proofs))
                    all_proofs[r.consequent] |= tmp
            # we started only with the new rules;
            # now add other rules that might be applicable
            if num_steps == 1 and new_proofs:
                rules = sorted((set(rules) | set(self.rules)))
        get_log().debug('Constructed proofs in %d iterations.' % num_steps)
        return new_proofs

    def _create_proofs(self, rule, subproofs):
        """ Insert new proofs based on the rule and the subproofs. 
        Subproofs have the format of a dictionary with Literals as kees and
        sets of proofs as values. Because there can be many ways to reach 
        a consequent (conclusion) a proof for each of the subproofs should
        be created.
        
        """
        get_log().debug('\tadding proofs with rule %s' % str(rule))
        get_log().debug('\t\tsubproofs: %s' % str(subproofs))
        new_proofs = set()
        # we need a proof for each subproof so create a cartesian product
        # to find the possible combinations
        product = itertools.product(*subproofs.values())
        for combination in product:
            contains_loop = False
            for subproof in combination:
                if subproof.uses_rule(rule):
                    # avoid loops - in case one of the subproofs uses the rule
                    contains_loop = True
                    break
            if contains_loop: continue
            proofs = dict()
            for sp in combination:
                proofs[sp.consequent] = sp
            p = Proof('', rule, proofs)
            name = self.generate_proof_name(p)
            p.name = name
            get_log().debug('\t\tfound proof "%s"' % str(p))
            new_proofs.add(p)
        return new_proofs
    
    def recalculate(self):
        """ Recalculate all proofs. """
        # create new proofs
        self._proofs.clear()
        self.proof_idx = 0
        new_proofs = self.construct_proofs(self._proofs, set(self.rules))
        # add the proofs
        for p in new_proofs:
             self._proofs[p.conclusion].add(p)
        return new_proofs
    
    def get_rules(self):
        """ Return a generator of all rules in working memory.
        These include not only user defined rules but also contrapositions.
        
        """
        for rule_set in self._wm.values():
            for r in rule_set:
                yield r
    
    def get_defeasible_rules(self):
        """ Return a generator of defeasible rules. """
        for r in self.get_rules():
            if isinstance(r, DefeasibleRule):
                yield r

    def get_strict_rules(self):
        """ Return a generator of strict rules. """
        for r in self.get_rules():
            if isinstance(r, StrictRule):
                yield r

    def get_rule_with_name(self, name):
        """ Return a rule with given name or None. """
        for r in self.get_rules():
            if r.name == name:
                return r
        return None

    def rules_with_consequent(self, consequent):
        """ Return all rules with the given consequent or None. """
        if isinstance(consequent, str):
            consequent = Literal.from_str(consequent)
        if consequent not in self._rules:
            return set()
        else:
            return self._rules[consequent]

    def get_proofs_for_rule(self, rule):
        """ Return a proofs that uses `rule` as the top rule or `set()`."""
        # only look at the proofs with the same consequent
        result = set()
        for p in self._proofs[rule.consequent]:
            if p.rule == rule:
                result.add(p)
        return result

    def add_preference_rules(self, line):
        """ Parse the line containing names of rules and their preferences. 
        format: r1, r2 < r3 < r4, r5 ...
        Throws ParseError when the format is wrong and 
        KnowledgeBaseError when preferences are inconsistent.
        
        """
        ords = orderings.parseString(line)
        get_log().debug('Adding preferences: %s' % str(ords))
        for i in range(len(ords) - 1):
            self.add_preference_rule(ords[i], ords[i+1])

    def add_preference_rule(self, lower, higher):
        """ Insert preferences for defeasible rules.
        lower, higher - iterable of rule names; higher is preferred over lower.
        
        """
        # self._prefs stores the preferences (partial order) as a DAG
        # NOTE: the order is specified across defeasible rule names
        # on inserting, check that we are not creating inconsistencies
        #   and raise KBError if we are
        edges = list(itertools.product(higher, lower))
        get_log().debug('  preference edges: %s' % str(edges))
        # be exception safe - first check for consistency and then add
        tmp = copy.deepcopy(self._prefs)
        for e in edges:
            po = tmp.find_path(e[1], e[0]) # possible preference order (path)
            # if po exists than this edge is inconsistent
            if po is not None:
                # inconsistency - be nice and include extra info
                ps = ' > '.join(map(str, po))
                msg = ('The preference rule "%s < %s" is not consistent with'
                       'the existing preference order: %s' % (e[0], e[1], ps))
                raise KnowledgeBaseError(msg)
            # if the rule is consistent, tentatively add it
            tmp.add_edge(*e)
        # all edges are consistent with respect to
        #   the existing prefs and each other
        for e in edges:
            get_log().debug('  Adding preference: %s > %s' % e)
            self._prefs.add_edge(*e)

    def more_preferred(self, rule_a, rule_b):
        """ Return True if rule 'a' is more preferred than rule 'b'. """
        # a is preferred over b if there is a path from a to b
        return (self._prefs.find_path(rule_a.name, rule_b.name) is not None)

    def preference_order(self, rule_a, rule_b):
        """ Return the order of preferences between rule_a and rule_b or None.
        
        """
        return self._prefs.find_path(rule_a.name, rule_b.name)
    
    def has_preference_for(self, rule):
        """ Return True if the rule has any preference weight. """
        return (rule.name in self._prefs)

    def check_consistency(self, proofs):
        """ Check that none of the strict proofs interferes
        with the existing knowledge base. 
        
        """
        for p in proofs:
            # consistency only applies to strict proofs
            if not p.is_strict(): continue
            if -p.consequent in self._proofs:
                counterproofs = self._proofs[-p.consequent]
                for cp in counterproofs:
                    if cp.is_strict():
                        # cp is a strict proof with an opposite conclusion
                        # which is not consistent with the proof p
                        msg = ('The proof %s is inconsistent with an existing '
                               'proof %s' % (str(p), str(cp)))
                        raise KnowledgeBaseError(msg)

    def generate_proof_name(self, proof):
        """ Return a name for an argument. """
        name = 'P%d' % self.proof_idx
        self.proof_idx += 1
        return name

    def read_file(self, file_name):
        with open(file_name, "r") as f:
            self.parse_file(f)

    def save_into_file(self, file_name):
        with open(file_name, "w") as f:
            for consequent, rules in self._rules.items():
                f.write('# rules with consequent "%s":\n' % str(consequent))
                for r in rules:
                    f.write(str(r) + '\n')
            for k, vs in self._prefs.items():
                if vs:
                    f.write('{k} < {vs}\n'.format(k=k, vs=', '.join(vs)))
            
    def parse_file(self, file):
        line_no = 0
        self.batch = True
        for line in file:
            line_no += 1
            line = line.partition('#')[0].strip() # remove comments
            if line == '': continue
            try:
                self.construct_rule(line)
            except Exception as e:
                msg = 'Exception on line %d: %s'
                get_log().exception(msg % (line_no, str(e)))
        self.batch = False
        self.recalculate()


# little helpers
def print_proofs(proofs):
    for c, ps in proofs.items():
        print(str(c) + ':')
        for p in ps:
            print('  ' + str(p))


############################ parsing related functions #########################

literal = Group(Optional(Word('-')) + Word(alphas, alphanums + '_'))
literals = delimitedList(literal)
antecedent = literals
vulnerabilities = literals
consequent = literal
ruleName = Word(alphas + '_', alphanums + '_')
ruleNames = delimitedList(ruleName)

strict_rule = Optional(ruleName.setResultsName("name") + ':') + \
    Optional(Group(antecedent).setResultsName("antecedent"))  + \
    "-->" + Group(consequent).setResultsName("consequent")

defeasible_rule = Optional(ruleName.setResultsName("name") + ':') + \
    Optional(Group(antecedent).setResultsName("antecedent")) + '=' + \
    Optional('(' + \
         Group(vulnerabilities).setResultsName("vulnerabilities") + ')') + \
    '=>' + Group(consequent).setResultsName("consequent")

orderings = delimitedList(Group(ruleNames), "<")


################################################################################
