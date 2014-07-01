import logging
import copy
from collections import defaultdict

import pyparsing
from pyparsing import Word, Group, Optional, alphanums, alphas, delimitedList


def get_log():
    return logging.getLogger('arg')


""" Structures and functions for reading a knowledge base of rules for 
    constructing argument networks. 

"""

class KnowledgeBaseError(Exception):
    pass


class ParseError(Exception):
    pass


class RuleError(Exception):
    pass


class Literal:
    """ The class represents a literal (possibly negated).

    The main purpose of the class is to enforce naming conventions.
    Literals are not allowed any other characters except for alphabet + '_'.

    To create a Literal instance from string use Literal.from_str(x). If
    a literal is to be negated, the identifier should start with '-' (eg, -p).
    The parser is not smart enough to parse "--p" as "p".

    """
    def __init__(self, name, negated=False):
        """ Create a literal with a name.
        Keyword arguments:
        negated -- is the literal negated (eg, not a; default false)
        
        """
        self.name = name
        self.negated = negated
    
    def __eq__(self, other):
        """ Compare with a literal or a string. """
        if isinstance(other, str):
            try:
                other = Literal.from_str(other)
            except Exception:
                return false
        return (isinstance(other, Literal) and
                self.name == other.name and
                self.negated == other.negated)
    
    def __lt__(self, other):
        if self.name == other.name:
            return (self.negated < other.negated)
        else:
            return (self.name < other.name)

    def __neg__(self):
        l = Literal(self.name, not self.negated)
        return l

    def __hash__(self):
        return hash('%s%d' % (self.name, self.negated))

    def __str__(self):
        str = ""
        if self.negated: str += "-"
        str += self.name
        return str
    
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
#                raise ParseError(str(ex)) from ex
                print(ex)
        if (len(params) == 1):
            return cls(params[0])
        elif (len(params) == 2):
            return cls(params[1], True)
        else:
            raise ParseError('Data mallformed: "%s"' % data)


class Rule:
    """ The class represents a rule for constructing arguments.
        This is a base class for Strict and Defesible rules.
        
    """
    def __init__(self, antecedent, consequent):
        """ A rule has to have antecedent and a consequent. 
        
            antecedent -- a list of Literals
            consequent -- a Literal
        """
        self.name = ""
        if antecedent is None:
            antecedent = list()
        else:
            self.antecedent = list(antecedent)
            for a in self.antecedent:
                if not isinstance(a, Literal):
                    raise RuleError("antecedent must be a list of Literals")
            self.antecedent.sort() # it is essential that the list is sorted!
        if consequent is None:
            raise RuleError("Rule has to have a consequence (None provided)")
        else:
            if not isinstance(consequent, Literal):
                raise RuleError("Consequent must be a Literal")
            self.consequent = consequent

    def __eq__(self, other):
        return (isinstance(other, Rule) and
                self.antecedent == other.antecedent and
                self.consequent == other.consequent)
    
    def __len__(self):
        return len(self.antecedent)
    
    def __hash__(self):
        value = hash(self.name)
        for a in self.antecedent:
            value ^= hash(a)
        value ^= hash(self.consequent)
        return value

    def __str__(self):
        if self.name != '':
            text = ('%s: ' % self.name)
        else:
            text = ''
        return ('%s%s --> %s' %
                (text,
                ','.join(map(str, self.antecedent)),
                str(self.consequent)))

    def __repr__(self):
        return ("Rule: %s" % str(self))

    @classmethod
    def from_str(Klass, rule):
        if isinstance(rule, str):
            if '->' in rule:
                rule = StrictRule.from_str(rule)
            elif '=>' in rule:
                rule = DefeasibleRule.from_str(rule)
            else:
                raise ParseError('"%s" is not a valid rule' % rule)
            return rule
        return None


class StrictRule(Rule):
    """ A strict rule is essentially the same as the Rule. """
    def __init__(self, antecedent, consequent):
        super().__init__(antecedent, consequent)

    def __repr__(self):
        return ('StrictRule %s' % str(self))
    
    def __lt__(self, other):
        return False
    
    @classmethod
    def from_str(cls, data):
        if not isinstance(data, str):
            raise ParseError('"%s" is not a string' % repr(data))
        try:
            parsed = strict_rule.parseString(data, parseAll=True)
            antecedent = None
            if 'antecedent' in parsed:
                antecedent = list(map(Literal.from_str, parsed['antecedent']))
            else:
                antecedent = []
            consequent = Literal.from_str(parsed['consequent'][0])
            return cls(antecedent, consequent)
        except Exception as e:
            raise ParseError('"%s" is not a strict rule\n\t error: %s'
                             % (data, str(e)))


class DefeasibleRule(Rule):
    def __init__(self, name, antecedent, consequent, vulnerabilities=None):
        super().__init__(antecedent, consequent)
        if vulnerabilities is None:
            self.vulnerabilities = list()
        else:
            for a in vulnerabilities:
                if not isinstance(a, Literal):
                    raise RuleError('Vulnerabilities must be list of Literals')
            self.vulnerabilities = list(vulnerabilities)
            self.vulnerabilities.sort()
        self.name = name
        self.weight = 0

    def __eq__(self, other):
        return (isinstance(other, DefeasibleRule) and
                self.vulnerabilities == other.vulnerabilities and
                super().__eq__(other))

    def __lt__(self, other):
        return self.weight < other.weight

    def __hash__(self):
        value = super().__hash__()
        for a in self.vulnerabilities:
            value ^= hash(a)
        return value

    def __str__(self):
        if self.name != '':
            text = ('%s: ' % self.name)
        else:
            text = ''
        if (len(self.antecedent) > 0):
            text += ('%s ' % ','.join(map(str, self.antecedent)))
        if (len(self.vulnerabilities) > 0):
            text += ('=(%s)=> ' % ','.join(map(str, self.vulnerabilities)))
        else:
            text += '==> '
        text += str(self.consequent)
        return text

    def __repr__(self):
        return ('DefeasibleRule %s' % str(self))

    @classmethod
    def from_str(cls, data):
        if not isinstance(data, str):
            raise ParseError('"%s" is not a string' % repr(data))
        try:
            parsed = defeasible_rule.parseString(data, parseAll=True)
            if 'name' in parsed:
                name = parsed['name']
            else:
                name = ""
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
            return cls(name, antecedent, consequent, vulners)
        except Exception as e:
            raise ParseError('"%s" is not a defeasible rule\n\tError: %s'
                             % (repr(data), str(e)))


class KnowledgeBase:
    """ A class that represents the knowledge base of rules. """

    def __init__(self, name=''):
        self.name = name
        self.defeasible_rules = dict() # temporary dict for name:rule
        self.rules = dict() # actual rules
        self.orderings = list()
        self.defeasible_idx = 0
        self.strict_idx = 0
        self.argument_idx = 0
        self._arguments = defaultdict(set)
    
    @classmethod
    def from_file(cls, file_name):
        if file_name is None:
            return cls()
        kb = cls(file_name)
        kb.read_file(file_name)
        kb.order() # order before computing transpositions
        kb.close() # close under transposition
        kb.check_consistency() # raises exc. if not consistent
        # delete redundant info
        del kb.defeasible_rules
        kb.construct_arguments()
        return kb
    
    def __eq__(self, other):
        return (self.name == other.name and
                self.rules == other.rules)

    def __str__(self):
        strict = list(self.get_strict_rules())
        defeasible = list(self.get_defeasible_rules())
        # sort the rules for easy reading
        defeasible.sort(key=lambda x: x.name)
        strict.sort(key=lambda x: x.name)
    
        s = 'Name: %s\n' % self.name
        s += ('Strict Rules:\n\t%s\n' %
              '\n\t'.join(map(str, strict)))
        s += ('Defeasible Rules:\n\t%s\n' %
              '\n\t'.join(map(str, defeasible)))
        s += ('Arguments:\n\t%s\n' %
              '\n\t'.join(map(str, sorted(self.arguments, key=lambda x: x.name))))
        
        return s
    
    __repr__ = __str__
    
    def __iter__(self):
        self.iterator = self.get_rules()
        return self
    
    def __next__(self):
        return next(self.iterator)

    def get_rules(self):
        for rule_set in self.rules.values():
            for r in rule_set:
                yield r
    
    def get_defeasible_rules(self):
        for r in self.get_rules():
            if isinstance(r, DefeasibleRule):
                yield r

    def get_strict_rules(self):
        for r in self.get_rules():
            if isinstance(r, StrictRule):
                yield r

    def close(self):
        rules_to_add = list()
        for r in self.get_rules():
            rules = self.transpositions(r)
            for tp in rules:
                rules_to_add.append(tp)
        for r in rules_to_add:
            self.add_rule(r, recalc=False)

    def check_consistency(self):
        pass

    def order(self):
#        print(self.orderings)
        for n, r in self.defeasible_rules.items():
            found = False
            w = 0
            for g in self.orderings:
                if n in g:
                    r.weight = w
                    found = True
                    break
                w += 1

    def add_rule(self, rule, recalc=True):
        """ Add a new rule to the knowledge base. """
        if not isinstance(rule, Rule): raise TypeError()
        get_log().debug('adding rule "%s"' % str(rule))
        if rule.consequent not in self.rules:
            rules = set()
            rules.add(rule)
            self.rules[rule.consequent] = rules
        else:
            self.rules[rule.consequent].add(rule)
        # re-compute arguments...
        if recalc: self.construct_arguments()

    def rule_with_consequent(self, consequent):
        """ Return a rule with the given consequent or None. """
        if isinstance(consequent, str):
            consequent = Literal.from_str(consequent)
        if consequent not in self.rules:
            return None
        else:
            for r in self.rules[consequent]: return r

    def del_rule(self, rule):
        """ Remove a rule from the knowledge base. 
        Returns True on success, False if no such rule found.
        """
        if not isinstance(rule, Rule): raise TypeError()
        if rule.consequent not in self.rules: return False
        rules = self.rules[rule.consequent]
        toRemove = None
        # do not match on name, just find the rule
        for r in rules:
            if (r.antecedent == rule.antecedent and
                r.consequent == rule.consequent and
                isinstance(rule, type(r))):
                toRemove = r
                break
        print('deleting rule: ' + str(toRemove))
        rules.remove(toRemove)
        # reconstruct the arguments
        self._arguments = defaultdict(set)
        self.construct_arguments()
        return True

    def get_rule(self, name):
        """ Return a rule with given name or None. """
        for r in self.get_rules():
            if r.name == name:
                return r
        return None
    
    def construct_arguments(self):
        get_log().debug('constructing arguments')
        done = set()
        old_size = -1
        rules = list(self.get_rules())
        rules.sort(key=lambda x: x.name)
        while (old_size != len(self)):
            # how many proofs we are starting from in this iteration
            old_size = len(self)
            for r in rules:
                get_log().debug('Current rule %s' % repr(r))
                if r in done:
                    get_log().debug('\t...already done')
                    continue
                proofs = dict()
                try:
                    for a in r.antecedent:
                        if a in self._arguments:
                            proofs[a] = self._arguments[a]
                        else:
    #                        get_log().debug('\tno proof for antecedent %s' % str(a))
                            break
                    # do we have a proof for all antecedents?
                    if len(proofs) == len(r.antecedent):
                        get_log().debug('\tadding argument with conclusion %s'
                                        % str(r.consequent))
                        self.add_argument(r, proofs)
                        done.add(r)
                except KeyError as e:
                    get_log().debug('\tno proof for antecedent %s' % str(e))
                except Exception as e:
                    get_log().exception(e)

    def __len__(self):
        """Return the number of arguments. """
        return seq_len(self.arguments)

    def add_argument(self, rule, prfs):
        get_log().debug('adding an argument for rule "%s" '
                        'using the following proofs: %s' %
                         (str(rule), str(prfs)))
        for c, p in prfs.items():
            get_log().debug('proof of "%s": "%s"' % (str(c), str(p)))
            for a in p:
                print(a.name)
        # check if there exists an argument with the rule
        for a in self.arguments:
            if a.rule == rule:
                return

        name = self.generate_argument_name(rule)
        # FIXME: the following line throws an exception!!!!!!!!!
#        proofs = copy.deepcopy(prfs)
        proofs = prfs # is this correct?
        # if the consequent appears as any of the antecedents break (rule loop)
        for proof_set in proofs.values():
            to_delete = list()
            for p in proof_set:
                if rule.consequent in p.antecedents:
                    to_delete.append(p)
            for p in to_delete:
#                print('deleting %s --from proof_set-- %s'
#                      % (str(p), str(proof_set)))
                proof_set.remove(p)
            if len(proof_set) == 0:
#                print('____rule %s not applied to avoid a circular arg. '
#                      % str(rule))
                return

        a = Argument(name, rule, prfs)
        get_log().debug('Created a new argument: %s' % repr(a))
        self._arguments[rule.consequent].add(a)

    @property
    def arguments(self):
        for c, args in self._arguments.items():
            for a in args:
                yield a

    def construct_strict_rule(self, string, recalc=False):
        try:
            rule = StrictRule.from_str(string)
            if (rule.name == ""):
                rule.name = self.generate_str_rule_name(rule)
            self.add_rule(rule, recalc=recalc)
        except Exception as e:
            get_log().exception('CSR: Exception: %s' % e)

    def construct_defeasible_rule(self, string, recalc=False):
        try:
            rule = DefeasibleRule.from_str(string)
            if (rule.name == ""):
                rule.name = self.generate_def_rule_name(rule)
            if (rule.name in self.defeasible_rules and
                rule != self.defeasible_rules[rule.name]):
                raise KnowledgeBaseError(
                    'Two different defeasible rules with same the name: %s'
                     % rule.name)
            self.defeasible_rules[rule.name] = rule
            self.add_rule(rule, recalc=recalc)
        except Exception as e:
            get_log().exception('CDR: Exception: %s' % e)

    def construct_ordering_rule(self, string):
    # assuming that the next batch of orderings follows the current
        try:
            ords = orderings.parseString(string)
            for o in ords: # iterate through the tuples
                self.orderings.append(list(o))
        except Exception as e:
            print('Ord: Exception: %s' % e)

    def generate_def_rule_name(self, rule):
        for r in self.get_defeasible_rules():
            if r == rule:
                return r.name
        name = 'D%d' % self.defeasible_idx
        self.defeasible_idx += 1
        return name

    def generate_str_rule_name(self, rule):
        for r in self.get_strict_rules():
            if r == rule:
                return r.name
        name = 'S%d' % self.strict_idx
        self.strict_idx += 1
        return name
    
    def generate_argument_name(self, rule):
        name = 'A%d' % self.argument_idx
        self.argument_idx += 1
        return name

    def read_file(self, file_name):
        with open(file_name, "r") as f:
            self.parse_file(f)

    def save_into_file(self, file_name):
        with open(file_name, "w") as f:
            for conclusion, rules in self.rules.items():
                f.write('# rules with conclusion "%s":\n' % str(conclusion))
                for r in rules:
                    f.write(str(r) + '\n')
            for o in self.orderings:
                f.write(str(o))
            
    def parse_file(self, file):
        line_no = 0
        for line in file:
            line_no += 1
            line = line.partition('#')[0] # remove comments
            if line == '' or line == '\n':
                continue
            
            if '->' in line:
                self.construct_strict_rule(line)
            elif '=>' in line:
                self.construct_defeasible_rule(line)
            elif '<' in line:
                self.construct_ordering_rule(line)
            else:
                print('Mallformed line %d: %s' % (line_no, line))


    def transpositions(self, rule):
        rules = list()
        nc = -(rule.consequent) # negation of the consequent
        if (isinstance(rule, StrictRule)):
            for a in rule.antecedent:
                antecedent = [i for i in rule.antecedent if i != a]
                antecedent.append(nc)
                r = StrictRule(antecedent, -a)
                r.name = self.generate_str_rule_name(r)
                rules.append(r)
        elif (isinstance(rule, DefeasibleRule)):
            # defeasible rules don't get closed under transposition
            return []
        else:
            raise TypeError('Expected a Rule subclass but received %s.'
                            % type(rule).__name__)
        return rules


class Argument:
    """ Argument - based on Mikolaj Podlaszewski's code. """
    
    def __init__(self, name, rule, arguments):
        self._framework = None
        self.name = name
        self.rule = rule
        self._arguments = arguments
        self.plus = set()  # set of arguments being attacked by this argument
        self.minus = set() # set of arguments attacking this argument
        self.is_strict = (isinstance(rule, StrictRule) and
                          self._arguments_are_strict())
    
    @property
    def conclusion(self):
        return self.rule.consequent
    
    @property
    def vulnerabilities(self):
        if isinstance(self.rule, DefeasibleRule):
            return self.rule.vulnerabilities
        return []
    
    @property
    def antecedents(self):
        for arg in self.subarguments:
            if arg != self:
                for a in arg.antecedents:
                    yield a
        for a in self.rule.antecedent:
            yield a
    
    def get_arguments(self):
        for c, args in self._arguments.items():
            for a in args:
                yield a
    
    @property
    def subarguments(self):
        for a in self.get_arguments():
            for a_i in a.subarguments:
                yield a_i
        yield self
    
    def get_defeasible_rules(self):
        for a in self.subarguments:
            if isinstance(a.rule, DefeasibleRule):
                yield a.rule
    
    def _arguments_are_strict(self):
        for a in self.get_arguments():
            if not a.is_strict:
                return False
        return True
    
    def __iter__(self):
        self.iterator = self.subarguments
        return self
    
    def __next__(self):
        return next(self.iterator)
    
    def __hash__(self):
        value = hash(self.name)
        value ^= hash(self.rule)
        value ^= hash(tuple(sorted(self._arguments)))
        return value
    
    def __eq__(self, other):
        return (self.name == other.name and
                self.rule == other.rule and
                self._arguments == other._arguments)
    
    def __lt__(self, other):
        # TODO: this is interesting...lets order them based on the first
        # defeasible rule
        l1 = list(reversed(list(self.get_defeasible_rules())))
        l2 = list(reversed(list(other.get_defeasible_rules())))
        # as both arguments are not strict, they have to have at least 1 element
        return l1[0] < l2[0]
    
    def __str__(self):
#        t = 'S_' if self.is_strict else 'D_'
        t = ''
        return ('%s%s: (%s)' % (t, self.name, str(self.rule)))
    
    def __repr__(self):
        return 'Argument %s' % str(self)

# parsing related functions
################################################################################

literal = Group(Optional(Word('-')) + Word(alphanums + '_'))
literals = delimitedList(literal)
antecedent = literals
vulnerabilities = literals
consequent = literal
ruleName = Word(alphanums + '_')
ruleNames = delimitedList(ruleName)

strict_rule = Optional(
       Group(antecedent).setResultsName("antecedent")) \
        + "-->" + Group(consequent).setResultsName("consequent")

defeasible_rule = Optional(ruleName.setResultsName("name") + ':') + \
    Optional(Group(antecedent).setResultsName("antecedent")) + '=' + \
    Optional('(' + \
         Group(vulnerabilities).setResultsName("vulnerabilities") + ')') + \
    '=>' + Group(consequent).setResultsName("consequent")

orderings = delimitedList(Group(ruleNames), "<")



# helpers
################################################################################

def seq_len(seq):
    return sum(1 for i in seq)



