import unittest

from argumentation.common import Move, PlayerType
from argumentation.common import IllegalMove, NoMoreMoves, NotYourMove
from argumentation.discussions import GroundedDiscussion, GroundedDiscussion2
from argumentation.discussions import Dialog
from argumentation.kb import KnowledgeBase, Argument
from argumentation.kb import  StrictRule, DefeasibleRule, Literal
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
        self.o = Player(PlayerType.OPONENT)

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
                           Player(PlayerType.OPONENT))
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
                           ScepticalPlayer(PlayerType.OPONENT))
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

def discuss3(arg=None):
    kb = KnowledgeBase.from_file('./argumentation/test/data/UAV_1.kb.txt')
    af = ArgumentationFramework(kb)
    l = Labelling.grounded(af)
    d = GroundedDiscussion2(l,
                           SmartPlayer(PlayerType.PROPONENT),
                           SmartPlayer(PlayerType.OPONENT))
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


test_kb_path = './argumentation/test/data/UAV_1.kb.txt'

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
        conclusion = Literal.from_str('lvA')
        self.assertEqual(None, d.find_rule(conclusion))
        d.load_kb(test_kb_path)
        self.assertEqual(StrictRule.from_str('--> lvA'),
                            d.find_rule(conclusion))
        self.assertEqual(StrictRule.from_str('--> lvA'),
                            d.find_rule('lvA'))

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

    def test_question(self):
        """ Test questionning a status of a conclusion """
        d = Dialog(test_kb_path)
        self.assertEqual('IN', d.question('lvA'))
        self.assertEqual('OUT', d.question('landA'))
        self.assertEqual('UNDEC', d.question('landA'))
        self.assertEqual(None, d.question('landA'))



if __name__ == '__main__':
    unittest.main()

