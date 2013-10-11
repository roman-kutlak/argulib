import unittest

from argumentation.discussions import GroundedDiscussion2
from argumentation.players import HumanPlayer, ScepticalPlayer
from argumentation.kb import KnowledgeBase
from argumentation.aal import ArgumentationFramework, Labelling
from argumentation.common import *


class HumanPlayerTest(unittest.TestCase):

    def test_parsing(self):
        kb = KnowledgeBase.from_file('./argumentation/test/data/UAV_1.kb.txt')
        af = ArgumentationFramework(kb)
        l = Labelling.grounded(af)
        human = HumanPlayer(PlayerType.OPONENT)
        d = GroundedDiscussion2(l,
                           ScepticalPlayer(PlayerType.PROPONENT),
                           human)
        move = human.parse_command('why in flyToLandingSiteB')
        self.assertNotNone(move)



kb = KnowledgeBase.from_file('./argumentation/test/data/UAV_1.kb.txt')
af = ArgumentationFramework(kb)
l = Labelling.grounded(af)
human = HumanPlayer(PlayerType.OPONENT)
d = GroundedDiscussion2(l,
           ScepticalPlayer(PlayerType.PROPONENT), human)
           
move = human.parse_command('why in flyToLandingSiteB', d)

# if the module is loaded on its own, run the test
if __name__ == '__main__':
    unittest.main()

