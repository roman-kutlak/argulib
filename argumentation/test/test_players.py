import sys

# we are assuming that the file runs from $(ASPIC-_ROOT)/tests
sys.path.insert(0, '../src')
sys.path.insert(1, '../src/arg')

from discussions import GroundedDiscussion2
from players import HumanPlayer, ScepticalPlayer
from kb import KnowledgeBase
from aal import ArgumentationFramework, Labelling
from common import *

import unittest


class HumanPlayerTest(unittest.TestCase):

    def test_parsing(self):
        kb = KnowledgeBase.from_file('/Users/roman/Work/Aspic-/data/UAV_2.kb.txt')
        af = ArgumentationFramework(kb)
        l = Labelling.grounded(af)
        human = HumanPlayer(PlayerType.OPONENT)
        d = GroundedDiscussion2(l,
                           ScepticalPlayer(PlayerType.PROPONENT),
                           human)
        move = human.parse_command('why in flyToLandingSiteB')
        self.assertNotNone(move)



kb = KnowledgeBase.from_file('/Users/roman/Work/Aspic-/data/UAV_2.kb.txt')
af = ArgumentationFramework(kb)
l = Labelling.grounded(af)
human = HumanPlayer(PlayerType.OPONENT)
d = GroundedDiscussion2(l,
           ScepticalPlayer(PlayerType.PROPONENT), human)
           
move = human.parse_command('why in flyToLandingSiteB', d)

