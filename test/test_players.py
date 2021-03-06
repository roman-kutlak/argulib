import unittest

from argulib.discussions import GroundedDiscussion2
from argulib.players import HumanPlayer, ScepticalPlayer
from argulib.kb import KnowledgeBase
from argulib.aal import ArgumentationFramework, Labelling
from argulib.common import *


class HumanPlayerTest(unittest.TestCase):

    def test_parsing(self):
        kb = KnowledgeBase.from_file('./test/data/UAV.kb.txt')
        af = ArgumentationFramework(kb)
        l = Labelling.grounded(af)
        human = HumanPlayer(PlayerType.OPPONENT)
        d = GroundedDiscussion2(l,
                           ScepticalPlayer(PlayerType.PROPONENT),
                           human)
        move = human.parse_command('why in flyToLandingSiteB', d)
        self.assertIsNotNone(move)



kb = KnowledgeBase.from_file('./test/data/UAV.kb.txt')
af = ArgumentationFramework(kb)
l = Labelling.grounded(af)
human = HumanPlayer(PlayerType.OPPONENT)
d = GroundedDiscussion2(l,
           ScepticalPlayer(PlayerType.PROPONENT), human)
           
move = human.parse_command('why in flyToLandingSiteB', d)

# if the module is loaded on its own, run the test
if __name__ == '__main__':
    unittest.main()

