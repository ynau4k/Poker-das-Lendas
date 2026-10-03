"""Presentation and animation layer. Poker state remains owned by PokerEngine."""
import math
import os
from dataclasses import dataclass
import pygame

GOLD=(210,174,107)
WHITE=(244,237,220)


@dataclass
class CardFlight:
    index: int
    card: int
    origin: tuple
    destination: tuple
    delay: float
    duration: float
    elapsed: float = 0.0

    @property
    def progress(self):
        return max(0.0,min(1.0,(self.elapsed-self.delay)/self.duration))

    @property
    def done(self):
        return self.elapsed >= self.delay+self.duration


class GameView:
    names=('Ronaldo','Mbappé','Messi','Neymar Jr.')
    personalities=('Calculista','Agressivo','Cauteloso','Blefador')
    profile_centers=((640,88),(1110,367),(640,635),(170,367))
    hand_centers=((640,232),(957,390),(640,555),(323,390))
    angles=(180,-90,0,90)

    def __init__(self,renderer):
        self.renderer=renderer
        root=os.path.join(os.path.dirname(__file__),'assets','game')
        image=pygame.image.load(os.path.join(root,'table.png')).convert()
        scale=min(1280/image.get_width(),690/image.get_height())
        self.table=pygame.transform.smoothscale(image,(round(image.get_width()*scale),round(image.get_height()*scale)))
        self.table_rect=self.table.get_rect(center=(640,385))
        self.avatars=[]
        for key in ('ronaldo','mbappe','messi','neymar'):
            image=pygame.image.load(os.path.join(root,key+'.jpg')).convert()
            width,height=image.get_size()
            # Frame the faces near the top of the original portrait, without stretching.
            side=round(width*(.60 if key=='messi' else .70))
            left=round(width*(.27 if key=='messi' else .20))
            region=pygame.Rect(min(left,width-side),round(height*.02),side,side)
            avatar=pygame.transform.smoothscale(image.subsurface(region),(64,64)).convert_alpha()
            mask=pygame.Surface((64,64),pygame.SRCALPHA)
            pygame.draw.circle(mask,(255,255,255),(32,32),31)
            avatar.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            self.avatars.append(avatar)
        self.fonts={n:pygame.font.SysFont('Arial',n,bold=n>=17) for n in (11,12,14,17,20,28)}
        self.flights=[]
        self.board_count=0
        self.hand_key=None
        self.hit_regions=[]
        self.selected=None
        self.on_card_click=None
        self.last_card_event=None
        self.pending_highlight=False
        self.deal_age=0.0

    @property
    def busy(self):
        return bool(self.flights) or self.deal_age < .8

    def sync(self,engine):
        key=(id(engine),engine.hand_count)
        if key!=self.hand_key:
            self.hand_key=key
            self.board_count=0
            self.flights=[]
            self.selected=None
            self.last_card_event=None
            self.pending_highlight=False
            self.deal_age=0.0
            for i,p in enumerate(engine.players):
                p.name=self.names[i]

    def board_destination(self,index):
        return (476+82*index,391)

    def queue_board(self,engine,player_idx,speed):
        self.sync(engine)
        queued={f.index for f in self.flights}
        duration=max(.65,1.15/speed)
        next_delay=0.0
        for index in range(self.board_count,len(engine.community_cards)):
            if index in queued:
                continue
            self.flights.append(CardFlight(index,engine.community_cards[index],self.hand_centers[player_idx],self.board_destination(index),next_delay,duration))
            next_delay+=duration*.55

    def update(self,dt,engine):
        self.sync(engine)
        self.deal_age+=dt
        for flight in self.flights:
            flight.elapsed+=dt
            if flight.done:
                self.board_count=max(self.board_count,flight.index+1)
        self.flights=[flight for flight in self.flights if not flight.done]

    def text(self,surface,message,size,center,color=WHITE):
        image=self.fonts[size].render(message,True,color)
        surface.blit(image,image.get_rect(center=center))

    def paint_card(self,surface,card,center,hidden,angle=0,scale=1,flip=1,identity=None):
        art=self.renderer.get_card_back() if hidden or flip<0 else self.renderer.get_card_front(card)
        art=pygame.transform.smoothscale(art,(max(2,round(68*scale*abs(flip))),round(98*scale)))
        if angle:
            art=pygame.transform.rotate(art,angle)
        rect=art.get_rect(center=tuple(map(round,center)))
        shadow=pygame.Surface(rect.inflate(12,12).size,pygame.SRCALPHA)
        pygame.draw.rect(shadow,(0,0,0,105),shadow.get_rect(),border_radius=8)
        surface.blit(shadow,(rect.x-2,rect.y+2))
        surface.blit(art,rect)
        if identity is not None:
            self.hit_regions.append((rect,identity,card,hidden))
            if self.selected==identity:
                pygame.draw.rect(surface,GOLD,rect.inflate(6,6),2,border_radius=6)

    def draw(self,surface,app):
        engine=app.engine
        self.sync(engine)
        self.hit_regions=[]
        surface.fill((8,9,9))
        surface.blit(self.table,self.table_rect)
        for i,p in enumerate(engine.players):
            x,y=self.profile_centers[i]
            active=not engine.hand_ended and engine.current_player_idx==i
            panel=pygame.Rect(x-96,y-42,192,143)
            pygame.draw.rect(surface,(12,14,14),panel,border_radius=18)
            pygame.draw.rect(surface,GOLD if active else (79,72,56),panel,2 if active else 1,border_radius=18)
            surface.blit(self.avatars[i],(x-32,y-32))
            pygame.draw.circle(surface,GOLD if active else (92,82,64),(x,y),33,2)
            self.text(surface,self.names[i],17,(x,y+45))
            self.text(surface,self.personalities[i],12,(x,y+65),(182,167,137))
            self.text(surface,f'{p.stack:,} fichas',14,(x,y+85),GOLD)
            hx,hy=self.hand_centers[i]
            for j,card in enumerate(p.hand):
                offset=(j-.5)*45
                center=(hx+offset,hy) if i in (0,2) else (hx,hy+offset)
                age=max(0,min(1,(self.deal_age-j*.12-i*.08)/.5))
                t=age*age*(3-2*age)
                center=(640+(center[0]-640)*t,391+(center[1]-391)*t)
                self.paint_card(surface,card,center,not(app.god_mode or engine.hand_ended),self.angles[i],.86,identity=('hand',i,j))
            label=p.last_action or ('ANALISANDO' if active else '')
            action_center=(hx+150,hy) if i in (0,2) else (hx,hy+80)
            self.text(surface,label[:28],11,action_center,(192,182,158))
        pot_box=pygame.Rect(487,278,306,49)
        pygame.draw.rect(surface,(8,25,19),pot_box,border_radius=12)
        pygame.draw.rect(surface,GOLD,pot_box,1,border_radius=12)
        self.text(surface,f'POTE  {engine.pot:,}',28,pot_box.center,GOLD)
        self.text(surface,engine.stage,12,(640,342),(198,185,157))
        flying_indices={f.index for f in self.flights}
        for j in range(5):
            center=self.board_destination(j)
            if j<len(engine.community_cards) and j<self.board_count and j not in flying_indices:
                self.paint_card(surface,engine.community_cards[j],center,False,identity=('board',j))
            else:
                pygame.draw.rect(surface,(49,83,61),pygame.Rect(center[0]-34,center[1]-49,68,98),1,border_radius=8)
        for flight in self.flights:
            if flight.elapsed<flight.delay:
                continue
            t=flight.progress
            eased=t*t*(3-2*t)
            ox,oy=flight.origin
            dx,dy=flight.destination
            center=(ox+(dx-ox)*eased,oy+(dy-oy)*eased-math.sin(math.pi*t)*65)
            flip=-math.cos(math.pi*t) # back first, edge halfway, face at the destination
            self.paint_card(surface,flight.card,center,False,angle=math.sin(math.pi*t)*18,scale=1+.15*math.sin(math.pi*t),flip=flip)
        text='Clique em uma carta para selecioná-la'
        if engine.hand_ended:
            text='Mão encerrada · '+', '.join(w['player'].name for w in engine.winners_info)
        elif app.auto_play:
            text=self.names[engine.current_player_idx]+' · aguardando o próximo turno'
        self.text(surface,text,14,(640,468),(218,207,184))
        if self.last_card_event is not None:
            event=self.last_card_event
            value='Carta oculta' if event['hidden'] else app.card_label(event['card'])
            self.text(surface,'Selecionada: '+value,12,(640,490),GOLD)
        elif engine.players[engine.current_player_idx].last_telemetry:
            t=engine.players[engine.current_player_idx].last_telemetry
            self.text(surface,f"Equity {t['equity']:.0f}% · Pot odds {t['pot_odds']:.0f}%",12,(640,490),GOLD)

    def click(self,position):
        for rect,identity,card,hidden in reversed(self.hit_regions):
            if rect.collidepoint(position):
                self.selected=identity
                self.last_card_event={'identity':identity,'card':card,'hidden':hidden}
                if self.on_card_click:
                    self.on_card_click(dict(self.last_card_event))
                return True
        return False
