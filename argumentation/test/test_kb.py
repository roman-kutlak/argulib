import unittest

from argumentation.kb import Literal, StrictRule, DefeasibleRule, make_rule
from argumentation.kb import Proof, KnowledgeBase
from argumentation.kb import ParseError


test_kb_path = './argumentation/test/data/tandem.kb.txt'

#o_str = "r1, r2, r3 < r4, r5 < r6"


######################### Test parsing functions ###############################


class TestLiteral(unittest.TestCase):
    """ Test the clas storing information about literals. """

    def test_basics(self):
        l1 = Literal('a')
        l2 = Literal.from_str('a')
        l3 = Literal.from_str('b')
        l4 = Literal('a', negated=True)

        self.assertEqual(l1, 'a')
        self.assertEqual(l4, '-a')
        self.assertEqual(l1, l2)
        self.assertNotEqual(l1, l3)
        self.assertNotEqual(l1, l4)
        self.assertNotEqual(l1, 34)

        self.assertRaises(ParseError, Literal.from_str, '!@#')
        self.assertRaises(ParseError, Literal.from_str, '  no-dashes  ')
        self.assertRaises(ParseError, Literal.from_str, '  no spaces  ')

    def test_hash(self):
        l1 = Literal('a')
        l2 = Literal.from_str('a')
        l3 = Literal.from_str('b')
        l4 = Literal('a', negated=True)
        self.assertEqual(hash(l1), hash(l2))
        self.assertNotEqual(hash(l1), hash(l3))
        self.assertNotEqual(hash(l1), hash(l4))

    def test_negation(self):
        l1 = Literal('a', False)
        l2 = Literal('a', True)
        self.assertNotEqual(l1, l2)
        self.assertEqual(l1, -l2)
        self.assertEqual(-l1, l2)

    def test_printing(self):
        l1 = Literal('a', False)
        l2 = Literal('a', True)
        self.assertEqual('a', str(l1))
        self.assertEqual('-a', str(l2))
        self.assertEqual(l1, Literal.from_str(str(l1)))
        self.assertEqual(l2, Literal.from_str(str(l2)))
        self.assertNotEqual(l1, Literal.from_str(str(l2)))
        self.assertNotEqual(l2, Literal.from_str(str(l1)))

        self.assertEqual('Literal: a', repr(l1))
        self.assertEqual('Literal: -a', repr(l2))

    def test_order(self):
        l1 = Literal('a')
        l2 = Literal.from_str('a')
        l3 = Literal.from_str('b')
        l4 = Literal('a', negated=True)
        lits = [l1, l2, l3, l4]
        lits.sort()
        self.assertEqual([l1, l2, l4, l3], lits)


class TestStrictRule(unittest.TestCase):
    """ Test harness for class StrictRule. """

    @classmethod
    def setUpClass(cls):
        cls.a = Literal('a')
        cls.b = Literal('b')
        cls.c = Literal('c')
        cls.nc = Literal('c', negated=True)

    def test_basics(self):
        r1 = StrictRule([self.a, self.b], self.nc, '')
        r2 = StrictRule.from_str('a, b --> -c')
        r3 = StrictRule.from_str('a, b --> c')
        r4 = StrictRule.from_str('a --> -c')
        self.assertEqual(r1, r2)
        self.assertNotEqual(r1, r3)
        self.assertNotEqual(r1, r4)


class TestDefeasibleRule(unittest.TestCase):
    """ Tests for class DefeasibleRule. """

    @classmethod
    def setUpClass(cls):
        cls.a = Literal('a')
        cls.b = Literal('b')
        cls.c = Literal('c')
        cls.d = Literal('d')
        cls.nc = Literal('c', negated=True)

    def test_basics(self):
        r1 = DefeasibleRule([self.a, self.b], self.nc, name='r1')
        r2 = DefeasibleRule.from_str('a, b ==> -c')
        r3 = DefeasibleRule.from_str('a, b ==> c')
        r4 = DefeasibleRule.from_str('a ==> -c')
        r5 = DefeasibleRule.from_str('a, b =(d)=> -c')
        self.assertEqual(r1, r2)
        self.assertNotEqual(r1, r3)
        self.assertNotEqual(r1, r4)
        self.assertNotEqual(r1, r5)

        self.assertEqual([self.a, self.b], r5.antecedent)
        self.assertEqual([self.d], r5.vulnerabilities)
        self.assertEqual(self.nc, r5.consequent)


class TestKb(unittest.TestCase):
    """ Tests for KnowledgeBase functionality. """

    def test_basics(self):
        kb = KnowledgeBase()
        self.assertIsNotNone(kb)
        kb = KnowledgeBase.from_file(test_kb_path)
        self.assertIsNotNone(kb)
        self.assertRaises(Exception, KnowledgeBase.from_file, 'foo')

    def test_add_rule(self):
        kb = KnowledgeBase()
        rule = make_rule('--> p')
        kb.add_rule(rule)
        p = Proof('', rule, {})
        self.assertEqual({p}, kb.proofs_for(Literal('p')))
    
    def test_del_rule(self):
        """ Test removing a rule. """
        kb = KnowledgeBase()
        r = kb.rules_with_consequent('bar')
        self.assertEqual(set(), r)
        kb.construct_rule('foo --> bar')
        r = kb.rules_with_consequent('bar')
        self.assertEqual({make_rule('foo --> bar')}, r)
        kb.del_rule(make_rule('foo --> bar'))
        r = kb.rules_with_consequent('bar')
        self.assertEqual(set(), r)

################################################################################

# if the module is loaded on its own, run the test
if __name__ == '__main__':
    import logging.config
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()


p = make_rule('--> p')
q = make_rule('--> q')
r = make_rule('p, q --> r')

p1 = Proof('p1', p, {})
p2 = Proof('p2', q, {})
p3 = Proof('p3', r, { Literal('p') : p1, Literal('q') : p2 })

p4 = Proof('p4', make_rule('r --> s'), { Literal('r') : p3 })

kb = KnowledgeBase()
kb.construct_rule('==> p')
kb.construct_rule('--> r')
kb.construct_rule('p ==> q')
kb.construct_rule('r --> q')
kb.construct_rule('foo --> bar')
kb.construct_rule('q =(-baz)=> bar')
kb.construct_rule('q ==> foo')
kb.construct_rule(' ==> -baz')
