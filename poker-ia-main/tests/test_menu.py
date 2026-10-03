import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from gui_pygame import PokerPygameApp


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.app = PokerPygameApp()
        self.menu = self.app.menu_screen
        self.surface = pygame.Surface((1280,800))
        self.menu.draw(self.surface,self.app)

    def settle(self,pointer,frames=32):
        for _ in range(frames):
            self.menu.update(.05,pointer)
            self.menu.draw(self.surface,self.app)

    def test_hover_and_return_every_player(self):
        for i in range(4):
            with self.subTest(player=self.menu.names[i]):
                origin=self.menu.home_rects[i].center
                self.menu.update(.05,origin)
                self.assertGreater(self.menu.progress[i],0)
                self.assertLess(self.menu.progress[i],1)
                self.settle(origin)
                self.assertEqual(self.menu.active,i)
                self.assertEqual(self.menu.progress[i],1)
                self.assertEqual(self.menu.rects[i].center,tuple(map(int,self.menu.focus)))
                self.assertGreater(self.menu.rects[i].height,self.menu.home_rects[i].height)
                self.assertTrue(all(v==0 for j,v in enumerate(self.menu.progress) if j!=i))
                self.menu.update(.05,(-100,-100))
                self.assertGreater(self.menu.progress[i],0)
                self.assertLess(self.menu.progress[i],1)
                self.settle((-100,-100))
                self.assertEqual(self.menu.progress[i],0)
                self.assertLess(abs(self.menu.rects[i].centerx-self.menu.home_rects[i].centerx),2)

    def test_click_persists_and_switches(self):
        self.menu.click(self.menu.rects[0].center,self.app)
        self.settle((-100,-100))
        self.assertEqual(self.menu.pinned,0)
        self.assertEqual(self.menu.progress[0],1)
        self.menu.click(self.menu.rects[3].center,self.app)
        self.settle((-100,-100))
        self.assertEqual(self.menu.progress[3],1)
        self.assertEqual(self.menu.progress[0],0)
        self.menu.click((5,150),self.app)
        self.settle((-100,-100))
        self.assertIsNone(self.menu.pinned)
        self.assertEqual(self.menu.progress,[0]*4)

    def test_buttons_and_settings(self):
        self.menu.click(self.menu.settings.center,self.app)
        self.assertTrue(self.menu.settings_open)
        self.menu.click(self.menu.speed_buttons[2].center,self.app)
        self.assertEqual(self.app.game_speed,3)
        old=self.app.god_mode
        self.menu.click(self.menu.reveal_button.center,self.app)
        self.assertNotEqual(old,self.app.god_mode)
        self.menu.click(self.menu.close_button.center,self.app)
        self.menu.click(self.menu.versus.center,self.app)
        self.assertTrue(self.menu.info_open)
        self.assertEqual(self.app.state,'MENU')
        self.menu.click(self.menu.close_button.center,self.app)
        self.menu.click(self.menu.play.center,self.app)
        self.assertEqual(self.app.state,'GAME')
        self.app.execute_next_step()
        self.app.draw()

    def test_responsive_layers_and_aspect_ratio(self):
        for size in ((1280,800),(1920,1080),(800,600),(390,844),(360,640)):
            with self.subTest(size=size):
                self.surface=pygame.Surface(size)
                self.menu.pinned=None
                self.menu.progress=[0.0]*4
                self.menu.depth=0
                self.menu.draw(self.surface,self.app)
                for i in range(4):
                    self.menu.pinned=i
                    self.settle((-100,-100))
                    rect=self.menu.rects[i]
                    self.assertTrue(self.surface.get_rect().contains(rect))
                    self.assertLessEqual(rect.bottom,size[1]-self.menu.footer_h+1)
                    ratio=self.menu.cards[i][0].get_width()/self.menu.cards[i][0].get_height()
                    self.assertAlmostEqual(rect.width/rect.height,ratio,delta=.01)
                    for button in (self.menu.play,self.menu.versus,self.menu.settings):
                        self.assertFalse(rect.colliderect(button))
                        self.assertTrue(self.surface.get_rect().contains(button))
                self.menu.pinned=None
                self.settle((-100,-100))

    def test_touch_events_without_duplicate_click(self):
        self.app.draw()
        center=self.menu.rects[2].center
        pygame.event.post(pygame.event.Event(pygame.FINGERDOWN,x=center[0]/1280,y=center[1]/800,finger_id=1,touch_id=1))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,pos=center,button=1,touch=True))
        self.app.handle_events()
        self.assertEqual(self.menu.pinned,2)

    def test_grayscale_and_color_sources(self):
        for color,gray in self.menu.cards:
            samples=[(int(color.get_width()*x),int(color.get_height()*y)) for x in (.25,.5,.75) for y in (.25,.5,.75)]
            self.assertTrue(all(gray.get_at(p).r==gray.get_at(p).g==gray.get_at(p).b for p in samples))
            self.assertTrue(any(len(set(color.get_at(p)[:3]))>1 for p in samples))


if __name__=='__main__':
    unittest.main()
