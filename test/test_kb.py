import unittest

from argulib.kb import Literal, StrictRule, DefeasibleRule, mk_rule
from argulib.kb import Proof, KnowledgeBase
from argulib.kb import ParseError


test_kb_path = './argulib/test/data/tandem.kb.txt'

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
        r = mk_rule('--> r')
        kb.add_rule(r)
        p = Proof('', r, {}, None)
        self.assertEqual({p}, kb.proofs_for(Literal('r')))
        rs = mk_rule('r --> s')
        kb.add_rule(rs)
        # added a contraposition
        self.assertEqual(3, len(list(kb.rules)))
        tmp = kb.rules_with_consequent(Literal('r', negated=True))
        self.assertEqual(tmp, {mk_rule('-s --> -r')})
        kb.add_rule('s ==> t')
        self.assertEqual(4, len(list(kb.rules)))
    
    def test_del_rule(self):
        """ Test removing a rule. """
        kb = KnowledgeBase()
        r = kb.rules_with_consequent('bar')
        self.assertEqual(set(), r)
        kb.add_rule('foo --> bar')
        r = kb.rules_with_consequent('bar')
        self.assertEqual({mk_rule('foo --> bar')}, r)
        kb.del_rule(mk_rule('foo --> bar'))
        r = kb.rules_with_consequent('bar')
        self.assertEqual(set(), r)

    def test_add_ordering(self):
        kb = KnowledgeBase()
        r1 = kb.add_rule('R1: p ==>  q')
        r2 = kb.add_rule('R2: r ==> -q')
        res = kb.more_preferred(r1, r2)
        self.assertFalse(res)
        res = kb.more_preferred(r2, r1)
        self.assertFalse(res)

        kb.add_rule('R1 < R2')
        self.assertFalse(kb.more_preferred(r1, r2))
        self.assertTrue(kb.more_preferred(r2, r1))

        kb.add_rule('R1 < R2, R3, R4 < R5, R6')
        r3 = kb.add_rule('R3: ==> r3')
        r4 = kb.add_rule('R4: ==> r4')
        r5 = kb.add_rule('R5: ==> r5')
        r6 = kb.add_rule('R6: ==> r6')
        # r6 beats almost anything
        self.assertTrue(kb.more_preferred(r6, r1))
        self.assertTrue(kb.more_preferred(r6, r2))
        self.assertTrue(kb.more_preferred(r6, r3))
        self.assertTrue(kb.more_preferred(r6, r4))
        self.assertFalse(kb.more_preferred(r6, r5))
        self.assertFalse(kb.more_preferred(r6, r6))
        # r6 beats almost anything
        self.assertTrue(kb.more_preferred(r5, r1))
        self.assertTrue(kb.more_preferred(r5, r2))
        self.assertTrue(kb.more_preferred(r5, r3))
        self.assertTrue(kb.more_preferred(r5, r4))
        self.assertFalse(kb.more_preferred(r5, r5))
        self.assertFalse(kb.more_preferred(r5, r6))
        # r3 is more preferred than r1 but less than r5, r6
        self.assertTrue(kb.more_preferred(r3, r1))
        self.assertFalse(kb.more_preferred(r3, r2))
        self.assertFalse(kb.more_preferred(r3, r3))
        self.assertFalse(kb.more_preferred(r3, r4))
        self.assertFalse(kb.more_preferred(r3, r5))
        self.assertFalse(kb.more_preferred(r3, r6))

    def test_del_ordering(self):
        kb = KnowledgeBase()
        r1 = kb.add_rule('R1: ==> r1')
        r2 = kb.add_rule('R2: ==> r2')
        r3 = kb.add_rule('R3: ==> r3')
        r4 = kb.add_rule('R4: ==> r4')
        r5 = kb.add_rule('R5: ==> r5')
        r6 = kb.add_rule('R6: ==> r6')
        self.assertFalse(kb.more_preferred(r1, r2))
        self.assertFalse(kb.more_preferred(r2, r1))
        
        kb.add_rule('R1 < R2, R3, R4 < R5, R6')
        self.assertFalse(kb.more_preferred(r1, r2))
        self.assertTrue(kb.more_preferred(r2, r1))
        self.assertTrue(kb.more_preferred(r5, r2))

        kb.del_rule('R1 < R2 < R5')
        self.assertFalse(kb.more_preferred(r1, r2))
        self.assertFalse(kb.more_preferred(r2, r1))
        self.assertTrue(kb.more_preferred(r5, r1))
        self.assertFalse(kb.more_preferred(r5, r2))
        self.assertTrue(kb.more_preferred(r5, r3))
        self.assertTrue(kb.more_preferred(r5, r4))
        self.assertFalse(kb.more_preferred(r5, r5))
        self.assertFalse(kb.more_preferred(r5, r6))
        self.assertTrue(kb.more_preferred(r6, r1))
        kb.del_rule('R1 < R6')
        self.assertTrue(kb.more_preferred(r6, r1))
        print(kb)



################################################################################

# if the module is loaded on its own, run the test
if __name__ == '__main__':
    import logging.config
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
