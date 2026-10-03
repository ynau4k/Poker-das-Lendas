"""Reference artwork with programmatically generated rank and suit combinations."""
import os
import pygame

SIZE = (340, 490)


class AntiqueDeck:
    """52 rank/suit combinations rendered from the supplied suit artwork."""
    def __init__(self):
        root = os.path.join(os.path.dirname(__file__), 'assets', 'game')
        reference = pygame.image.load(os.path.join(root, 'faces.png')).convert()
        self.templates = {}
        for kind, x in zip('hdcs', (88, 447, 793, 1149)):
            for court, y, height in ((False,16,448),(True,495,462)):
                tile = reference.subsurface(pygame.Rect(x,y,308,height))
                self.templates[kind,court] = pygame.transform.smoothscale(tile,SIZE).convert_alpha()
        image = pygame.image.load(os.path.join(root,'back.png')).convert()
        self.back = pygame.transform.smoothscale(image.subsurface((442,38,652,930)),SIZE).convert_alpha()
        self.font=pygame.font.SysFont('Times New Roman',63,bold=True)
        self.cache={}
        self.mask=pygame.Surface(SIZE,pygame.SRCALPHA)
        pygame.draw.rect(self.mask,(255,255,255),self.mask.get_rect(),border_radius=21)
        self.back.blit(self.mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)

    def front(self,rank,kind):
        key=(rank,kind)
        if key in self.cache:
            return self.cache[key]
        surface=self.templates[kind,rank in ('J','Q','K')].copy()
        color=(156,32,38) if kind in ('h','d') else (184,148,95)
        # Replace only the rank panels; all four suit motifs come from the reference.
        panel=pygame.Surface((64,77))
        panel.fill((9,9,7))
        text=self.font.render(rank,True,color)
        if text.get_width()>60:
            text=pygame.transform.smoothscale(text,(60,text.get_height()))
        panel.blit(text,text.get_rect(center=(32,36)))
        surface.blit(panel,(17,13))
        surface.blit(pygame.transform.rotate(panel,180),(340-81,490-90))
        surface.blit(self.mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        self.cache[key]=surface
        return surface
