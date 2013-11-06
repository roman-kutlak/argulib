import unittest

from argumentation.common import Move, PlayerType
from argumentation.common import IllegalMove, NoMoreMoves, NotYourMove
from argumentation.discussions import GroundedDiscussion, GroundedDiscussion2
from argumentation.discussions import Dialog
from argumentation.kb import KnowledgeBase, Argument
from argumentation.kb import  Rule, StrictRule, DefeasibleRule, Literal
from argumentation.aal import ArgumentationFramework, Labelling
from argumentation.players import Player, SmartPlayer, ScepticalPlayer


class GroundedDiscussionTest(unittest.TestCase):
    """ Test the discussion protocol. """

    def setUp(self):
        """ Testing the class requires an abstract AF and the labelling. """
        a = Argument('A', StrictRule.from_str('--> a'), dict())
        b = Argument('B', DefeasibleRule.from_str('=(-a)=> b'), dict())
        c = Argument('C', DefeasibleRule.from_str('==> -b'), dict())
        d = Argument('D', DefeasibleRule.from_str('=(-a)=> b'), dict())
        e = Argument('E', DefeasibleRule.from_str('b ==> d'), dict())
        args = dict()
        args['a'] = a
        args['b'] = b
        args['c'] = c
        args['d'] = d
        self.af = ArgumentationFramework.from_arguments(args)
        self.l = Labelling.grounded(self.af)
        # players
        self.p = Player(PlayerType.PROPONENT)
        self.o = Player(PlayerType.OPPONENT)

        self.la = self.l.labelling_for(a)
        # moves
        self.p_claim_a = (self.p, Move.CLAIM, self.la)
        self.o_claim_a = (self.o, Move.CLAIM, self.la)
        self.p_why_a = (self.p, Move.WHY, self.la)
        self.o_why_a = (self.o, Move.WHY, self.la)
        self.p_because_a = (self.p, Move.BECAUSE, self.la)
        self.o_because_a = (self.o, Move.BECAUSE, self.la)
        self.p_concede_a = (self.p, Move.CONCEDE, self.la)
        self.o_concede_a = (self.o, Move.CONCEDE, self.la)

    def test_claim(self):
        """ Test the rules for 'claim' speech act. """
        d = GroundedDiscussion(self.l, self.p, self.o)

        # test that only the proponent can 'claim'
        self.assertRaises(NotYourMove, d.move, *self.o_claim_a)
        # test that 'claim' has to be played before other moves
        self.assertRaises(IllegalMove, d.move, *self.o_why_a)
        self.assertRaises(IllegalMove, d.move, *self.p_because_a)
        self.assertRaises(IllegalMove, d.move, *self.o_concede_a)

        d.move(*self.p_claim_a)
        self.assertGreater(len(d.moves), 0)
        self.assertEqual(d.open_issues[0], self.la)

    def test_why(self):
        """ Test the rules for 'why' speech act. """
        d = GroundedDiscussion(self.l, self.p, self.o)

        # test that only the oponent can use 'why'
        self.assertRaises(NotYourMove, d.move, *self.p_why_a)
        # test that 'why' addresses the last open issue
        self.assertRaises(IllegalMove, d.move, self.o, Move.WHY,
            self.l.labelling_for(self.af.find_argument('B')))

        d.move(*self.p_claim_a)

        d.move(*self.o_why_a)
        self.assertGreater(len(d.moves), 1)
        self.assertEqual(d.open_issues[0], self.la)

    def test_because(self):
        """ Test the rules for 'why' speech act. """
        d = GroundedDiscussion(self.l, self.p, self.o)

        # test that only the proponent can use 'because'
        self.assertRaises(NotYourMove, d.move, *self.o_because_a)
        # test that 'because' addresses the last open issue
        self.assertRaises(IllegalMove, d.move, self.p, Move.BECAUSE,
            self.l.labelling_for(self.af.find_argument('B')))

        d.move(*self.p_claim_a)
        d.move(*self.o_why_a)

        # using an argument that is an open issue is prohibited
        self.assertRaises(IllegalMove, d.move, *self.p_because_a)

        d.move(self.p, Move.BECAUSE, Labelling(None, set(), set(), set()))
        self.assertGreater(len(d.moves), 2)
        self.assertEqual(d.open_issues[0], self.la)

    def test_concede(self):
        """ Test the rules for 'why' speech act. """
        d = GroundedDiscussion(self.l, self.p, self.o)
        d.move(*self.p_claim_a)
        d.move(*self.o_why_a)
        d.move(self.p, Move.BECAUSE, Labelling(None, set(), set(), set()))

        # test that only the oponent can use 'why'
        self.assertRaises(NotYourMove, d.move, *self.p_concede_a)

        # test that 'why' can't be played as it already is an open issue
        # self.assertRaises(IllegalMove, d.move, *self.o_why_a)
        # actually, the above does not work because I allow the oponent
        # to open an issue to which the proponent commited (to allow
        # 'because' to show only one answer at a time

        # test that 'because' can not be played
        self.assertRaises(IllegalMove, d.move, self.p, Move.BECAUSE,
            self.l.labelling_for(self.af.find_argument('B')))

        self.assertEqual(len(d.open_issues), 2)
        d.move(self.o, Move.CONCEDE, Labelling(None, set(), set(), set()))

        self.assertGreater(len(d.moves), 3)
        self.assertEqual(len(d.open_issues), 1)


def discuss(arg=None):
    kb = KnowledgeBase.from_file('./argumentation/test/data/UAV_1.kb.txt')
    af = ArgumentationFramework(kb)
    l = Labelling.grounded(af)
    d = GroundedDiscussion(l,
                           Player(PlayerType.PROPONENT),
                           Player(PlayerType.OPPONENT))
    af.save_graph()

    if arg is not None:
        lab = d.question(af.find_argument(arg))
        d.move(d.proponent, Move.CLAIM, lab)
        d.move(*d.opponent.make_move(d))
    try:
        while True:
            m = d.proponent.make_move(d)
            if m is not None: d.move(*m)
            m = d.opponent.make_move(d)
            if m is not None: d.move(*m)
    except NoMoreMoves:
        return d
    except Exception as e:
        print('Exception: %s' % str(e))
        print(d)
        raise e

    return d

def discuss2(arg=None):
    kb = KnowledgeBase.from_file('./argumentation/test/data/UAV_1.kb.txt')
    af = ArgumentationFramework(kb)
    l = Labelling.grounded(af)
    d = GroundedDiscussion(l,
                           ScepticalPlayer(PlayerType.PROPONENT),
                           ScepticalPlayer(PlayerType.OPPONENT))
    af.save_graph()

    if arg is not None:
        lab = d.question(af.find_argument(arg))
        d.move(d.proponent, Move.CLAIM, lab)
        d.move(*d.opponent.make_move(d))
    try:
        while True:
            m = d.proponent.make_move(d)
            if m is not None: d.move(*m)
            m = d.opponent.make_move(d)
            if m is not None: d.move(*m)
    except NoMoreMoves:
        return d
    except Exception as e:
        print('Exception: %s' % str(e))
        print(d)
        raise

    return d

def discuss3(arg=None):
    kb = KnowledgeBase.from_file('./argumentation/test/data/UAV_1.kb.txt')
    af = ArgumentationFramework(kb)
    l = Labelling.grounded(af)
    d = GroundedDiscussion2(l,
                           SmartPlayer(PlayerType.PROPONENT),
                           SmartPlayer(PlayerType.OPPONENT))
    af.save_interesting_graph()

    if arg is not None:
        lab = d.question(af.find_argument(arg))
        d.move(d.proponent, Move.CLAIM, lab)
        d.move(*d.opponent.make_move(d))
    try:
        while True:
            m = d.proponent.make_move(d)
            if m is not None: d.move(*m)
            m = d.opponent.make_move(d)
            if m is not None: d.move(*m)
    except NoMoreMoves:
        return d
    except Exception as e:
        print('Exception: %s' % str(e))
        print(d)
        raise e

    return d

#print(discuss3('A0'))


test_kb_path = './argumentation/test/data/test.kb.txt'

class DialogTest(unittest.TestCase):
    """ A test harness for the Dialog class. """

    def test_load(self):
        """ Test constructing a new Dialog instance and loading a KB. """
        d = Dialog()
        self.assertIsNotNone(d)
        d = Dialog(test_kb_path)
        self.assertIsNotNone(d)
        self.assertRaises(Exception, lambda: Dialog(''))

    def test_find_rule(self):
        """ Test finding a rule with a particular conclusion. """
        d = Dialog()
        conclusion = Literal.from_str('sa')
        self.assertEqual(None, d.find_rule(conclusion))
        d.load_kb(test_kb_path)
        self.assertEqual(StrictRule.from_str('--> sa'),
                            d.find_rule(conclusion))
        self.assertEqual(StrictRule.from_str('--> sa'),
                            d.find_rule('sa'))
        self.assertEqual(StrictRule.from_str('sa --> sb'),
                            d.find_rule('sb'))

    def test_find_argument(self):
        """ Test finding an argument with a particular conclusion. """
        d = Dialog()
        conclusion = Literal.from_str('sa')
        self.assertEqual(None, d.find_argument(conclusion))
        d.load_kb(test_kb_path)
        self.assertEqual(StrictRule.from_str('--> sa'),
                            d.find_argument(conclusion).rule)
        self.assertEqual(StrictRule.from_str('--> sa'),
                            d.find_argument('sa').rule)
        self.assertEqual(StrictRule.from_str('sa --> sb'),
                            d.find_argument('sb').rule)

    def test_assert(self):
        """ Test adding new knowledge into the knowledge base. """
        d = Dialog()
        self.assertEqual(None, d.find_rule('b'))
        # test adding a rule from string
        d.add(' a --> b ')
        self.assertEqual(StrictRule.from_str('a --> b'), d.find_rule('b'))
        # test adding a rule as a Rule instance
        d.add(StrictRule.from_str('b --> c'))
        self.assertEqual(StrictRule.from_str('b --> c'), d.find_rule('c'))

    def test_justify(self):
        """ Test justifying a conclusion. """
        msg = 'There is no argument with conclusion "b"'
        d = Dialog(test_kb_path)
        m = d.do_justify('b')
        self.assertEqual(msg, m)

        m = d.do_justify('sb')
        expected = [StrictRule.from_str(x) for x in
                        [' --> sa', ' sa --> sb']]
        expected.sort(key=lambda x: x.name)
        self.assertEqual(expected, m)

        m = d.do_justify('sc')
        expected = [StrictRule.from_str(x) for x in
                        ['   --> sa',
                         '   --> sa',
                         'sa --> sb',
                         'sa,sb --> sc']]
        self.assertEqual(expected, m)

    def test_explain(self):
        """ Test explaining why a conclusion is not true. """
        assertion = DefeasibleRule.from_str('==> bar')
        rule = DefeasibleRule.from_str('bar ==> foo')
        d = Dialog()

        # dialog kb empty
        self.assertEqual(None, d.find_rule('foo'))
        self.assertEqual(None, d.find_argument('foo'))

        # now we have a rule but there is no argument for it (no antecedant)
        d.add('bar ==> foo')
        self.assertEqual(rule, d.find_rule('foo'))
        self.assertEqual(None, d.find_argument('foo'))
        res = d.do_explain('foo')
        self.assertEqual([Literal('bar')], res)

    def test_question(self):
        """ Test questionning a status of a conclusion """
        msg = 'There is no argument with conclusion "b"'
        d = Dialog(test_kb_path)

        m = d.do_question('IN', 'b')
        self.assertEqual(msg, m)

        m = d.do_question('IN', 'sb')
        self.assertIsNotNone(m)
        # there should be no attackers against 'sb'
        self.assertEqual('The argument "sb" has no attackers.', m)

        m = d.do_question('OUT', '-at')
        self.assertIsNotNone(m)
        # there should be no attackers against 'sb'
        self.assertEqual(StrictRule.from_str('--> at'), m[2].argument.rule)

    def test_do_assert(self):
        """ Test adding new rules. """
        d = Dialog(test_kb_path)
        res = d.do_assert('bad rule')
        self.assertEqual('"bad rule" is not a valid rule', res)

        self.assertEqual(None, d.find_rule('bar'))
        res = d.do_assert('foo --> bar')
        self.assertEqual(StrictRule.from_str('foo --> bar'),
                        d.find_rule('bar'))

    def test_do_retract(self):
        """ Test removing rules. """
        d = Dialog()
        res = d.do_retract(Rule.from_str('foo --> bar'))
        msg = 'no rule "foo --> bar" found'
        self.assertEqual(msg, res)
        d.do_assert('foo --> bar')
        res = d.do_retract(Rule.from_str('foo --> bar'))
        msg = 'rule "foo --> bar" deleted'
        self.assertEqual(msg, res)


    def test_parse(self):
        """ Test parsing commands. """
        assertion = DefeasibleRule.from_str('==> bar')
        rule = DefeasibleRule.from_str('bar ==> foo')
        d = Dialog()

        # dialog kb empty
        self.assertEqual(None, d.find_rule('foo'))
        self.assertEqual(None, d.find_argument('foo'))

        # now we have a rule but there is no argument for it (no antecedant)
        d.parse('assert bar ==> foo')
        self.assertEqual(rule, d.find_rule('foo'))
        self.assertEqual(None, d.find_argument('foo'))

        # finally have an argument
        d.parse('assert ==> bar')
        self.assertEqual(rule, d.find_rule('foo'))
        self.assertEqual(rule, d.find_argument('foo').rule)

        res = d.parse('why foo')
        self.assertEqual([assertion, rule], res)

        res = d.parse('why in foo')
        self.assertEqual('The argument "foo" has no attackers.', res)



if __name__ == '__main__':
    unittest.main()

