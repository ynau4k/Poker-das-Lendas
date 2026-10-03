"""Responsive Pygame menu. Filters and perspective never modify source assets."""
import math
import os
import pygame

GOLD = (229, 194, 122)
IVORY = (249, 242, 224)


def ease(value):
    return value * value * (3 - 2 * value)


class MenuScreen:
    names = ('Ronaldo', 'Messi', 'Neymar', 'Mbappé')

    def __init__(self):
        root = os.path.join(os.path.dirname(__file__), 'assets', 'menu')
        self.background_source = pygame.image.load(os.path.join(root, 'background.png')).convert()
        self.cards = []
        for name in ('ronaldo', 'messi', 'neymar', 'mbappe'):
            image = pygame.image.load(os.path.join(root, name + '.png')).convert_alpha()
            # Cache working textures; keep the original files and their aspect ratios intact.
            image = pygame.transform.smoothscale(image, (int(720 * image.get_width() / image.get_height()), 720))
            self.cards.append((image, pygame.transform.grayscale(image)))
        self.progress = [0.0] * 4
        self.depth = 0.0
        self.active = None
        self.pinned = None
        self.settings_open = False
        self.info_open = False
        self.size = None
        self.clock_time = 0.0
        self.button_progress = [0.0] * 3
        self.font_cache = {}
        self.rects = [pygame.Rect(0, 0, 0, 0) for _ in range(4)]
        self.layout((1280, 800))

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.font_cache:
            self.font_cache[key] = pygame.font.SysFont('Arial', size, bold=bold)
        return self.font_cache[key]

    def text(self, surface, text, size, color, center, bold=False):
        rendered = self.font(size, bold).render(text, True, color)
        surface.blit(rendered, rendered.get_rect(center=center))

    def layout(self, size):
        if size == self.size:
            return
        self.size = size
        w, h = size
        self.portrait = w < h * .95
        self.header_h = min(142, int(h * .18))
        self.footer_h = 168 if self.portrait else 126
        self.area = pygame.Rect(16, self.header_h, w - 32, max(100, h - self.header_h - self.footer_h))
        if self.portrait:
            self.base_height = min(self.area.height * .43, w * .52)
            self.homes = [(w * x, self.area.y + self.area.height * y) for x, y in ((.28,.25),(.72,.25),(.28,.75),(.72,.75))]
            button_w = (w - 44) // 2
            self.play = pygame.Rect(22, h-153, w-44, 55)
            self.versus = pygame.Rect(22, h-85, button_w-6, 48)
            self.settings = pygame.Rect(w//2+6, h-85, button_w-6, 48)
        else:
            self.base_height = min(self.area.height * .84, (w-160) / 4 * 1.34)
            self.homes = [(w * (.17 + i*.22), self.area.centery) for i in range(4)]
            button_w = min(310, (w-100)//3)
            self.versus = pygame.Rect(w//2-button_w*3//2-16, h-97, button_w, 61)
            self.play = pygame.Rect(w//2-button_w//2, h-97, button_w, 61)
            self.settings = pygame.Rect(w//2+button_w//2+16, h-97, button_w, 61)
        self.focus_height = min(self.area.height * .97, w * (.75 if self.portrait else .40))
        self.focus = (w/2, self.area.centery)
        self.home_rects = [self.card_rect(i, xy, self.base_height) for i,xy in enumerate(self.homes)]
        scale = max(w/self.background_source.get_width(), h/self.background_source.get_height())
        bg = pygame.transform.smoothscale(self.background_source, (math.ceil(self.background_source.get_width()*scale), math.ceil(self.background_source.get_height()*scale)))
        self.background = pygame.Surface(size)
        self.background.blit(bg, bg.get_rect(center=(w//2,h//2)))
        shade = pygame.Surface(size, pygame.SRCALPHA)
        shade.fill((0,0,0,112))
        self.background.blit(shade,(0,0))
        mw = min(570, w-32)
        mh = min(340, h-40)
        self.modal = pygame.Rect((w-mw)//2,(h-mh)//2,mw,mh)
        self.speed_buttons = [pygame.Rect(self.modal.x+24+i*(mw-48)//3,self.modal.y+110,(mw-60)//3,43) for i in range(3)]
        self.reveal_button = pygame.Rect(self.modal.x+24,self.modal.y+178,mw-48,43)
        self.close_button = pygame.Rect(self.modal.x+24,self.modal.bottom-65,mw-48,42)

    def card_rect(self, idx, center, height):
        ratio = self.cards[idx][0].get_width()/self.cards[idx][0].get_height()
        rect = pygame.Rect(0,0,max(1,int(height*ratio)),max(1,int(height)))
        rect.center = (round(center[0]), round(center[1]))
        return rect

    def hit(self, position, retain_home=False):
        # The visually highest card gets the hit first. No invisible cards steal input.
        # Retain the initial hover while the card travels away from the pointer.
        # Otherwise a background card crossing that point can cause oscillation.
        if retain_home and self.active is not None:
            if self.rects[self.active].collidepoint(position) or self.home_rects[self.active].collidepoint(position):
                return self.active
        order = sorted(range(4), key=lambda i:self.progress[i], reverse=True)
        for i in order:
            if self.rects[i].collidepoint(position):
                return i
        if self.depth < .05:
            for i,rect in enumerate(self.home_rects):
                if rect.collidepoint(position):
                    return i
        return None

    def update(self, dt, pointer=None):
        self.clock_time += dt
        if pointer is None:
            pointer = pygame.mouse.get_pos()
        target = self.pinned if self.pinned is not None else self.hit(pointer, retain_home=True)
        if self.settings_open or self.info_open:
            target = None
        self.active = target
        # Exponential damping is frame-rate independent and reverses without a jump.
        blend = 1-math.exp(-5.5*min(dt,.1))
        for i in range(4):
            self.progress[i] += ((1.0 if target == i else 0.0)-self.progress[i])*blend
            if self.progress[i] < .0005:
                self.progress[i] = 0.0
            elif self.progress[i] > .9995:
                self.progress[i] = 1.0
        self.depth += ((1 if target is not None else 0)-self.depth)*blend
        if self.depth < .0005:
            self.depth = 0.0
        elif self.depth > .9995:
            self.depth = 1.0
        for i,rect in enumerate((self.versus,self.play,self.settings)):
            self.button_progress[i] += (int(rect.collidepoint(pointer))-self.button_progress[i])*blend

    @staticmethod
    def perspective(texture, angle):
        """Project vertical strips as a rotating plane, with foreshortening and depth."""
        if abs(angle) < .01:
            return texture
        width,height = texture.get_size()
        sine,cosine = math.sin(angle),math.cos(angle)
        focal = width*2.8
        bounds = []
        for x in (0,width):
            local = x-width/2
            z = local*sine
            factor = focal/(focal+z)
            bounds.append((local*cosine*factor, height*factor))
        out_w = max(2, math.ceil(bounds[1][0]-bounds[0][0])+2)
        out_h = math.ceil(max(v[1] for v in bounds))
        out = pygame.Surface((out_w,out_h),pygame.SRCALPHA)
        left = bounds[0][0]
        step = 3
        for x in range(0,width,step):
            end = min(width,x+step)
            local,other = x-width/2,end-width/2
            factor = focal/(focal+local*sine)
            x1 = int(local*cosine*factor-left)
            x2 = math.ceil(other*cosine*focal/(focal+other*sine)-left)
            sh = max(1,int(height*factor))
            strip = pygame.transform.smoothscale(texture.subsurface((x,0,end-x,height)),(max(1,x2-x1+1),sh))
            out.blit(strip,(x1,(out_h-sh)//2))
        return out

    def pose(self, i):
        amount = ease(self.progress[i])
        d = ease(self.depth)
        x,y = self.homes[i]
        # Inactive cards step back and leave a corridor for the hero card.
        side_x = self.size[0]*(.14 if i%2==0 else .86)
        side_y = self.area.y+self.area.height*(.30 if i<2 else .72)
        if not self.portrait:
            side_x = self.size[0]*(.13 if i<2 else .87)
            side_y = self.area.y+self.area.height*(.27 if i%2==0 else .73)
        x += (side_x-x)*d*(1-amount)
        y += (side_y-y)*d*(1-amount)
        x += (self.focus[0]-x)*amount
        y += (self.focus[1]-y)*amount
        height = self.base_height*(1-.42*d)*(1-amount)+self.focus_height*amount
        y += math.sin(self.clock_time*.9+i)*2*(1-amount)
        # A cinematic turn while travelling; frontal again at either endpoint.
        angle = math.sin(math.pi*self.progress[i])*1.05*(-1 if i<2 else 1)
        return (x,y),height,angle,amount

    def draw_card(self, surface, i):
        center,height,angle,amount = self.pose(i)
        color,gray = self.cards[i]
        rect = self.card_rect(i,center,height)
        texture = pygame.Surface(rect.size, pygame.SRCALPHA)
        texture.fill((0, 0, 0, 255))
        texture.blit(pygame.transform.smoothscale(gray,rect.size),(0,0))
        if amount > 0:
            layer = pygame.transform.smoothscale(color,rect.size)
            layer.set_alpha(round(255*amount))
            texture.blit(layer,(0,0))
        texture = self.perspective(texture,angle)
        rect = texture.get_rect(center=(round(center[0]),round(center[1])))
        self.rects[i] = rect
        shadow = pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        for padding,alpha in ((24,5),(16,9),(8,18)):
            pygame.draw.rect(shadow,(0,0,0,alpha+int(18*amount)),rect.move(8,12).inflate(padding,padding),border_radius=15)
        if amount > .01:
            for padding,alpha in ((28,5),(16,9),(8,15)):
                pygame.draw.rect(shadow,(*GOLD,int(alpha*amount)),rect.inflate(padding,padding),width=padding//2,border_radius=18)
        surface.blit(shadow,(0,0))
        texture.set_alpha(round(255*(1-.43*ease(self.depth)*(1-amount))))
        surface.blit(texture,rect)

    def button(self,surface,rect,label,hover=0,primary=False,size=18):
        overlay=pygame.Surface(rect.size,pygame.SRCALPHA)
        overlay.fill((8+int(18*hover),8+int(14*hover),9+int(7*hover),235))
        surface.blit(overlay,rect)
        pygame.draw.rect(surface,GOLD if primary else (145+int(45*hover),125+int(36*hover),87+int(28*hover)),rect,2 if primary else 1,border_radius=8)
        self.text(surface,label,size,IVORY if primary else GOLD,rect.center,True)

    def draw(self,surface,app):
        self.layout(surface.get_size())
        w,h=self.size
        surface.blit(self.background,(0,0))
        # Background -> dim cards -> foreground card -> persistent interface -> modal.
        for i in sorted(range(4),key=lambda idx:self.progress[idx]):
            self.draw_card(surface,i)
        header=pygame.Surface((w,self.header_h),pygame.SRCALPHA)
        header.fill((0,0,0,120))
        surface.blit(header,(0,0))
        self.text(surface,'POKER ROYALE',max(24,min(52,w//16)),GOLD,(w//2,self.header_h*.40),True)
        subtitle='QUATRO LENDAS. UMA MESA.'
        self.text(surface,subtitle,max(10,min(13,w//32)),(195,182,155),(w//2,self.header_h*.73))
        footer=pygame.Surface((w,self.footer_h),pygame.SRCALPHA)
        footer.fill((0,0,0,220))
        surface.blit(footer,(0,h-self.footer_h))
        labels=('IA VS HUMANO','JOGAR','CONFIGURAÇÕES')
        for j,rect in enumerate((self.versus,self.play,self.settings)):
            self.button(surface,rect,labels[j],self.button_progress[j],j==1,size=max(10,min(19,int(rect.width/10))))
        hint='Passe o mouse ou toque em uma carta'
        self.text(surface,hint,11,(183,174,156),(w//2,h-17))
        if self.settings_open or self.info_open:
            overlay=pygame.Surface(self.size,pygame.SRCALPHA)
            overlay.fill((0,0,0,205))
            surface.blit(overlay,(0,0))
            pygame.draw.rect(surface,(13,13,16),self.modal,border_radius=14)
            pygame.draw.rect(surface,GOLD,self.modal,1,border_radius=14)
            self.text(surface,'CONFIGURAÇÕES' if self.settings_open else 'IA VS HUMANO',23,GOLD,(w//2,self.modal.y+39),True)
            if self.settings_open:
                self.text(surface,'Velocidade da simulação',15,IVORY,(w//2,self.modal.y+84))
                for i,rect in enumerate(self.speed_buttons):
                    self.button(surface,rect,f'{i+1}×',int(app.game_speed==i+1),app.game_speed==i+1)
                self.button(surface,self.reveal_button,'Cartas reveladas: '+('SIM' if app.god_mode else 'NÃO'),primary=app.god_mode,size=15)
            else:
                for j,line in enumerate(('Modo em desenvolvimento.', 'O motor atual simula quatro IAs.', 'Use JOGAR para assistir à partida.')):
                    self.text(surface,line,14,IVORY,(w//2,self.modal.y+115+j*30))
            self.button(surface,self.close_button,'VOLTAR',primary=True,size=15)

    def click(self,position,app):
        if self.settings_open or self.info_open:
            if self.close_button.collidepoint(position):
                self.settings_open=self.info_open=False
            elif self.settings_open:
                for i,rect in enumerate(self.speed_buttons):
                    if rect.collidepoint(position):
                        app.set_game_speed(i+1)
                if self.reveal_button.collidepoint(position):
                    app.god_mode=not app.god_mode
            return
        if self.play.collidepoint(position):
            app.start_play()
        elif self.settings.collidepoint(position):
            self.settings_open=True
        elif self.versus.collidepoint(position):
            self.info_open=True
        else:
            idx=self.hit(position,retain_home=True)
            self.pinned=idx if idx != self.pinned else None
            self.active=self.pinned
