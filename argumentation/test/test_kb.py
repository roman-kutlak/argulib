import unittest

from argumentation.kb import Literal, Rule, StrictRule, DefeasibleRule
from argumentation.kb import Argument, KnowledgeBase
from argumentation.kb import ParseError


data = KnowledgeBase.from_file('./argumentation/test/data/eg_tandem.txt')

class TestKb(unittest.TestCase):
    pass

# some instances for interactive testing
################################################################################

#a = Literal('a')
#b = Literal('b')
#r = Literal('r')
#nq = Literal('q', True)
#r1 = StrictRule([a, b], nq)
#r2 = DefeasibleRule('r2', [a,nq], r, [b])
#
#sr_str = "-a,b,-c --> -q"
#dr_str = "r1:-a,b =(c,-d)=> r"
#dr2_str = "r2:-a,b ==> r"
#o_str = "r1, r2, r3 < r4, r5 < r6"
#
#sr = strict_rule.parseString(sr_str)
#dr = defeasible_rule.parseString(dr_str)
#o = orderings.parseString(o_str)
#
#s1 = StrictRule.from_str('p --> q')
#s2 = StrictRule.from_str('l --> m')
#s3 = StrictRule.from_str('-r --> r')


#kb = KnowledgeBase.from_file('./test/data/eg_tandem.txt')



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

    def test_basics(self):
        pass





# if the module is loaded on its own, run the test
if __name__ == '__main__':
    unittest.main()

