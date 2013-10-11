import unittest

from argumentation.kb import KnowledgeBase

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



# if the module is loaded on its own, run the test
if __name__ == '__main__':
    unittest.main()

