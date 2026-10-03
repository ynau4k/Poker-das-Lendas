import os
os.environ['SDL_VIDEODRIVER']='dummy'
import sys
import hashlib
import random
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from treys import Card
from gui_pygame import PokerPygameApp, CardRenderer
from game_view import CardFlight


class GameViewTests(unittest.TestCase):
    def setUp(self):
        self.app=PokerPygameApp()
        self.view=self.app.game_view
        self.app.ai.simulations=80
        self.view.update(1,self.app.engine)
        self.app.state='GAME'
        self.app.draw()

    def test_complete_deck_and_rng(self):
        CardRenderer._design=None
        CardRenderer._card_cache.clear()
        rng=random.getstate()
        hashes=set()
        for kind in 'shdc':
            for rank in 'A23456789TJQK':
                image=CardRenderer.get_card_front(Card.new(rank+kind))
                self.assertEqual(image.get_size(),(68,98))
                hashes.add(hashlib.sha256(pygame.image.tobytes(image,'RGBA')).hexdigest())
        self.assertEqual(len(hashes),52)
        self.assertEqual(random.getstate(),rng)
        self.assertEqual(CardRenderer.get_card_back().get_size(),(68,98))

    def test_board_flights_and_turn_lock(self):
        self.app.engine.community_cards=self.app.engine.deck.draw(3)
        self.view.queue_board(self.app.engine,3,1)
        self.assertEqual(len(self.view.flights),3)
        self.assertEqual(self.view.board_count,0)
        first=self.view.flights[0]
        self.assertEqual(first.origin,self.view.hand_centers[3])
        self.assertEqual(first.progress,0)
        before=(self.app.engine.current_player_idx,self.app.engine.pot)
        self.app.execute_next_step()
        self.assertEqual(before,(self.app.engine.current_player_idx,self.app.engine.pot))
        self.view.update(.4,self.app.engine)
        self.assertGreater(first.progress,0)
        self.assertLess(first.progress,1)
        self.app.draw()
        self.view.update(5,self.app.engine)
        self.assertFalse(self.view.busy)
        self.assertEqual(self.view.board_count,3)
        self.app.draw()
        board=[region for region in self.view.hit_regions if region[1][0]=='board']
        self.assertEqual(len(board),3)
        self.assertEqual([r[2] for r in board],self.app.engine.community_cards)

    def test_click_callback_and_hidden_cards(self):
        self.app.god_mode=False
        self.app.draw()
        region=self.view.hit_regions[0]
        events=[]
        self.view.on_card_click=events.append
        self.assertTrue(self.view.click(region[0].center))
        self.assertTrue(events[0]['hidden'])
        self.assertEqual(events[0]['identity'],('hand',0,0))
        state=(self.app.engine.pot,self.app.engine.current_player_idx)
        self.assertEqual(state,(self.app.engine.pot,self.app.engine.current_player_idx))
        self.app.god_mode=True
        self.app.draw()
        self.view.click(self.view.hit_regions[0][0].center)
        self.assertFalse(events[-1]['hidden'])

    def test_play_runs_to_completion(self):
        class Clock:
            def get_time(self): return 50
        self.app.clock=Clock()
        random.seed(41)
        with patch('gui_pygame.time.time') as now:
            now.return_value=0
            self.app.menu_screen.click(self.app.menu_screen.play.center,self.app)
            self.assertTrue(self.app.auto_play)
            self.assertEqual(self.app.state,'GAME')
            for frame in range(3000):
                now.return_value=frame*.05
                self.app.update()
                if self.app.engine.hand_ended and not self.view.busy:
                    break
            else:
                self.fail('Automatic hand did not finish')
            self.assertFalse(self.app.auto_play)
            self.assertTrue(self.app.engine.winners_info)
            self.assertEqual(sum(p.stack for p in self.app.engine.players),4000)
            hand=self.app.engine.hand_count
            for _ in range(30):
                self.app.update()
            self.assertEqual(self.app.engine.hand_count,hand)
            self.assertEqual([p.personality for p in self.app.engine.players],['equilibrado','agressivo','conservador','blefador'])

    def test_table_aspect_and_resized_hit_mapping(self):
        self.assertAlmostEqual(self.view.table.get_width()/self.view.table.get_height(),1.5,delta=.002)
        for size in ((1280,800),(1920,1080),(800,600),(390,844)):
            self.app.screen=pygame.display.set_mode(size,pygame.RESIZABLE)
            self.app.draw()
            scale=min(size[0]/1280,size[1]/800)
            logical=self.view.hit_regions[0][0].center
            physical=(logical[0]*scale+(size[0]-1280*scale)/2,logical[1]*scale+(size[1]-800*scale)/2)
            mapped=self.app.game_coordinates(physical)
            self.assertTrue(self.view.click(mapped))
            self.assertEqual(self.view.selected,('hand',0,0))

    def test_reset_discards_pending_visual_state(self):
        self.app.engine.community_cards=self.app.engine.deck.draw(3)
        self.view.queue_board(self.app.engine,0,1)
        self.view.pending_highlight=True
        self.app.reset_match()
        self.assertEqual(self.view.flights,[])
        self.assertFalse(self.view.pending_highlight)
        self.assertEqual(self.view.board_count,0)
        self.assertFalse(self.app.auto_play)


if __name__=='__main__':
    unittest.main()
