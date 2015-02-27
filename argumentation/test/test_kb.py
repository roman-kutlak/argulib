import unittest

from argumentation.kb import Literal, Rule, StrictRule, DefeasibleRule
from argumentation.kb import Argument, KnowledgeBase
from argumentation.kb import ParseError


test_kb_path = './argumentation/test/data/test.kb.txt'

#o_str = "r1, r2, r3 < r4, r5 < r6"


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
        r1 = StrictRule('', [self.a, self.b], self.nc)
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
        r1 = DefeasibleRule('r1', [self.a, self.b], self.nc)
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


class TestArgument(unittest.TestCase):
    """ Test the functionality of class Argument. """

    def test_basics(self):
        pass


# TODO: add type checking to the KnowledgeBase
class TestKb(unittest.TestCase):
    """ Tests for KnowledgeBase functionality. """

    def test_basics(self):
        kb = KnowledgeBase()
        self.assertIsNotNone(kb)
        kb = KnowledgeBase.from_file(test_kb_path)
        self.assertIsNotNone(kb)
        self.assertRaises(Exception, KnowledgeBase.from_file, 'foo')

    def test_del_rule(self):
        """ Test removing a rule. """
        kb = KnowledgeBase()
        r = kb.rules_with_consequent('bar')
        self.assertEqual(set(), r)
        kb.add_rule(Rule.from_str('foo --> bar'))
        r = kb.rules_with_consequent('bar')
        self.assertEqual(Rule.from_str('foo --> bar'), list(r)[0])
        kb.del_rule(Rule.from_str('foo --> bar'))
        r = kb.rules_with_consequent('bar')
        self.assertEqual(set(), r)


# if the module is loaded on its own, run the test
if __name__ == '__main__':
    unittest.main()

