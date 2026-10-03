"""
poker_highlights.py - Sistema Avançado de Detecção de Melhores Momentos,
Curiosidades Contrafactuais ("E SE?") e Registro Histórico de Recordes da Partida.
"""

import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from treys import Evaluator, Deck, Card
from poker_engine import CardUtils, Player, HAND_RANKS_PT


@dataclass
class HandHighlight:
    """Estrutura rica de um Momento Marcante identificado na rodada."""
    category: str                   # "HAND_RANK", "TACTICAL", "COUNTERFACTUAL", "RECORD"
    event_type: str                 # "VIRADA_RIVER", "BLEFE_PERFEITO", "FULL_HOUSE", etc.
    title: str                      # Título grande para a interface (ex: "★ VIRADA NO RIVER ★")
    headline: str                   # Manchete (ex: "Messi buscou a vitória na última carta!")
    subtitle: str                   # Subtítulo explicativo
    narrative_lines: List[str]      # 2 a 3 linhas narrativas humanas
    player_name: str                # Jogador principal em destaque
    player_idx: int                 # Índice do jogador
    pot_amount: int                 # Valor do pote conquistado
    primary_cards: List[int]        # Cartas do jogador
    board_cards: List[int]          # Cartas da mesa
    color: Tuple[int, int, int]     # Cor temática do destaque
    intensity: int                  # 1: Normal, 2: Destaque, 3: Grande Evento, 4: Épico
    is_major_event: bool = True     # Pausa auto-play se for evento relevante
    
    # Seção Contrafactual "E SE?"
    has_counterfactual: bool = False
    counterfactual_title: str = ""
    counterfactual_desc: str = ""
    counterfactual_player: str = ""
    counterfactual_cards: List[int] = field(default_factory=list)
    counterfactual_hand_class: str = ""
    counterfactual_disclaimer: str = "RESULTADO SIMULADO — a mão foi encerrada após o fold."


class MatchTracker:
    """Rastreia recordes, maiores jogadas e estatísticas globais da sessão."""
    def __init__(self):
        self.total_hands: int = 0
        self.highest_pot: Dict[str, Any] = {"amount": 0, "winner": "Nenhum", "hand_num": 0, "class_name": ""}
        self.highest_bet: Dict[str, Any] = {"amount": 0, "player": "Nenhum", "hand_num": 0}
        self.best_bluff: Optional[Dict[str, Any]] = None
        self.best_comeback: Optional[Dict[str, Any]] = None
        self.strongest_hand: Dict[str, Any] = {"class_name": "Nenhuma", "player": "Nenhum", "cards": [], "hand_num": 0, "score": 99999}
        self.notable_folds: List[Dict[str, Any]] = []
        self.recent_highlights: List[HandHighlight] = []
        
        # Histórico de ações da mão corrente para alimentar os analisadores
        self.current_hand_actions: List[Dict[str, Any]] = []
        self.current_hand_max_bet: int = 0
        self.stage_leaders: Dict[str, Dict[str, Any]] = {}

    def start_new_hand(self, hand_num: int):
        self.total_hands = hand_num
        self.current_hand_actions.clear()
        self.current_hand_max_bet = 0
        self.stage_leaders.clear()

    def record_action(self, stage: str, player_idx: int, player_name: str, action: str, amount: int, is_bluff: bool, equity: float):
        self.current_hand_actions.append({
            "stage": stage,
            "player_idx": player_idx,
            "player_name": player_name,
            "action": action,
            "amount": amount,
            "is_bluff": is_bluff,
            "equity": equity
        })
        if amount > self.current_hand_max_bet:
            self.current_hand_max_bet = amount
        if amount > self.highest_bet["amount"]:
            self.highest_bet = {
                "amount": amount,
                "player": player_name,
                "hand_num": self.total_hands
            }

    def record_hand_end(self, highlight: HandHighlight, pot: int, winner_name: str, rank_score: int, hand_class: str, winner_cards: List[int]):
        # Atualiza Maior Pote
        if pot > self.highest_pot["amount"]:
            self.highest_pot = {
                "amount": pot,
                "winner": winner_name,
                "hand_num": self.total_hands,
                "class_name": hand_class
            }
        
        # Atualiza Mão Mais Forte (Treys: menor score = mão mais forte)
        if rank_score < self.strongest_hand["score"] and rank_score > 0:
            self.strongest_hand = {
                "class_name": hand_class,
                "player": winner_name,
                "cards": winner_cards,
                "hand_num": self.total_hands,
                "score": rank_score
            }

        # Registra Blefe Marcante
        if highlight.event_type == "BLEFE_PERFEITO":
            if not self.best_bluff or pot > self.best_bluff.get("pot", 0):
                self.best_bluff = {
                    "player": winner_name,
                    "pot": pot,
                    "hand_num": self.total_hands,
                    "desc": highlight.headline
                }

        # Registra Virada Marcante
        if highlight.event_type in ("VIRADA_RIVER", "BAD_BEAT"):
            if not self.best_comeback or pot > self.best_comeback.get("pot", 0):
                self.best_comeback = {
                    "player": winner_name,
                    "pot": pot,
                    "hand_num": self.total_hands,
                    "desc": highlight.headline
                }

        # Registra Fold Curioso Marcante
        if highlight.has_counterfactual:
            self.notable_folds.append({
                "player": highlight.counterfactual_player,
                "hand_class": highlight.counterfactual_hand_class,
                "pot": pot,
                "hand_num": self.total_hands,
                "cards": highlight.counterfactual_cards
            })

        self.recent_highlights.insert(0, highlight)
        if len(self.recent_highlights) > 15:
            self.recent_highlights.pop()


class CuriosityDetector:
    """Detecta oportunidades contrafactuais ('E SE?') analisando decisões dos jogadores que deram fold."""
    @staticmethod
    def detect_counterfactual(engine, actual_winner: Player, full_board: List[int], scores: Dict[int, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        evaluator = engine.evaluator
        actual_winner_score = scores[actual_winner.idx]["score"]
        
        # Jogadores que desistiram (fold)
        folded_players = [p for p in engine.players if not p.is_active and len(p.hand) >= 2]
        if not folded_players:
            return None

        candidates = []
        for p in folded_players:
            p_score = scores[p.idx]["score"]
            p_class = scores[p.idx]["hand_class"]
            # Se a mão do jogador que foldou superaria o vencedor real
            if p_score < actual_winner_score:
                candidates.append({
                    "player": p,
                    "score": p_score,
                    "hand_class": p_class,
                    "cards": p.hand
                })

        if not candidates:
            return None

        # Pega a melhor mão entre os que desistiram
        best_candidate = min(candidates, key=lambda c: c["score"])
        cand_p = best_candidate["player"]
        cand_class = best_candidate["hand_class"]

        return {
            "title": "⚠ E SE? FOLD CURIOSO DETECTADO",
            "desc": f"Se {cand_p.name} não tivesse desistido, teria vencido o pote com {cand_class}!",
            "player_name": cand_p.name,
            "cards": cand_p.hand,
            "hand_class": cand_class
        }


class HighlightDetector:
    """Analisa a mão concluída e seleciona o Melhor Momento mais relevante e emocionante."""

    @staticmethod
    def analyze_round(engine, tracker: MatchTracker) -> HandHighlight:
        if not engine.hand_ended or not engine.winners_info:
            return HandHighlight(
                category="GENERIC",
                event_type="EM_ANDAMENTO",
                title="★ PARTIDA EM ANDAMENTO ★",
                headline="Aguardando Conclusão",
                subtitle="A simulação está em curso.",
                narrative_lines=["Os jogadores estão disputando as fichas."],
                player_name="Mesa",
                player_idx=0,
                pot_amount=engine.pot,
                primary_cards=[],
                board_cards=engine.community_cards,
                color=(140, 150, 175),
                intensity=1,
                is_major_event=False
            )

        evaluator = engine.evaluator
        actual_winner_info = engine.winners_info[0]
        actual_winner = actual_winner_info["player"]
        actual_hand_class = actual_winner_info.get("hand_class", "")
        actual_winner_cards = actual_winner.hand

        # Completa o board de 5 cartas se a mão acabou antes do River
        full_board = list(engine.community_cards)
        if len(full_board) < 5:
            known_cards = set(full_board)
            for p in engine.players:
                known_cards.update(p.hand)
            available = [c for c in Deck().cards if c not in known_cards]
            needed = 5 - len(full_board)
            full_board.extend(available[:needed])

        # Calcula o score de todos os 4 jogadores contra o board completo
        scores = {}
        for p in engine.players:
            s = evaluator.evaluate(full_board, p.hand)
            cls_rank = evaluator.get_rank_class(s)
            raw_cls_name = evaluator.class_to_string(cls_rank)
            cls_name = CardUtils.translate_hand_class(raw_cls_name)
            scores[p.idx] = {
                "player": p,
                "score": s,
                "cls_rank": cls_rank,
                "hand_class": cls_name
            }

        winner_score = scores[actual_winner.idx]["score"]
        winner_cls_rank = scores[actual_winner.idx]["cls_rank"]
        best_score = min(info["score"] for info in scores.values())
        best_players = [info["player"] for info in scores.values() if info["score"] == best_score]
        winner_was_best = (actual_winner.idx in [p.idx for p in best_players])

        # Verifica detecção contrafactual ("E SE?")
        counterfactual = CuriosityDetector.detect_counterfactual(engine, actual_winner, full_board, scores)

        # Histórico de ações na mão atual
        hand_actions = tracker.current_hand_actions
        bluff_actions = [a for a in hand_actions if a.get("is_bluff")]
        has_all_in = any(p.is_all_in for p in engine.players) or any(a.get("action") == "all-in" for a in hand_actions)
        is_pot_record = engine.pot >= 800 or (tracker.highest_pot["amount"] > 0 and engine.pot >= tracker.highest_pot["amount"])

        # Avaliação de virada no River (Turn Leader vs River Winner)
        turn_comeback = False
        turn_loser_was_winner = False
        if len(engine.community_cards) >= 5:
            turn_board = engine.community_cards[:4]
            active_at_turn = [p for p in engine.players if p.is_active]
            if len(active_at_turn) >= 2:
                turn_scores = {p.idx: evaluator.evaluate(turn_board, p.hand) for p in active_at_turn}
                turn_leader_idx = min(turn_scores, key=turn_scores.get)
                if turn_leader_idx != actual_winner.idx and turn_scores[turn_leader_idx] < turn_scores[actual_winner.idx]:
                    turn_comeback = True

        # =====================================================================
        # HIERARQUIA DE CANDIDATOS A MELHOR MOMENTO
        # =====================================================================
        candidates: List[Tuple[int, HandHighlight]] = []

        # ---------------------------------------------------------------------
        # 1. MÃOS RARAS & MONSTROS (Royal Flush, Quadra, Full House, Straight Flush)
        # ---------------------------------------------------------------------
        if winner_cls_rank == 1: # Straight Flush ou Royal Flush
            is_royal = (winner_score == 1)
            title = "★ ROYAL FLUSH LENDÁRIO! ★" if is_royal else "★ STRAIGHT FLUSH ÉPICO! ★"
            headline = f"{actual_winner.name} fez a mão mais rara do poker!"
            candidates.append((100 if is_royal else 95, HandHighlight(
                category="HAND_RANK",
                event_type="ROYAL_FLUSH" if is_royal else "STRAIGHT_FLUSH",
                title=title,
                headline=headline,
                subtitle=f"Probabilidade astronômica concretizada com {actual_hand_class}!",
                narrative_lines=[
                    f"{actual_winner.name} formou a combinação suprema ({actual_hand_class})!",
                    "Uma jogada histórica que dominou completamente a mesa.",
                    f"Pote conquistado: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(255, 215, 0),
                intensity=4,
                is_major_event=True
            )))

        elif winner_cls_rank == 2: # Quadra (Four of a Kind)
            candidates.append((92, HandHighlight(
                category="HAND_RANK",
                event_type="QUADRA",
                title="★ QUADRA IMPARÁVEL! ★",
                headline=f"{actual_winner.name} acertou uma Quadra!",
                subtitle="Quatro cartas idênticas formaram uma fortaleza insuperável.",
                narrative_lines=[
                    f"Com {actual_hand_class}, {actual_winner.name} não deu chances aos adversários.",
                    "As apostas foram correspondidas até a vitória esmagadora.",
                    f"Total arrecadado no pote: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(255, 140, 40),
                intensity=4,
                is_major_event=True
            )))

        elif winner_cls_rank == 3: # Full House
            candidates.append((82, HandHighlight(
                category="HAND_RANK",
                event_type="FULL_HOUSE",
                title="★ FULL HOUSE MONSTRO! ★",
                headline=f"{actual_winner.name} montou um Full House!",
                subtitle="Trinca combinada a um par formou um jogo de altíssimo valor.",
                narrative_lines=[
                    f"Com {actual_hand_class}, {actual_winner.name} maximizou seus ganhos.",
                    "A leitura matemática e a agressividade no momento certo garantiram o pote.",
                    f"Premiação da rodada: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(50, 185, 255),
                intensity=3,
                is_major_event=True
            )))

        # ---------------------------------------------------------------------
        # 2. VIRADA NO RIVER (RIVER COMEBACK)
        # ---------------------------------------------------------------------
        if turn_comeback:
            candidates.append((88, HandHighlight(
                category="TACTICAL",
                event_type="VIRADA_RIVER",
                title="★ VIRADA NO RIVER! ★",
                headline=f"{actual_winner.name} virou o jogo na última carta!",
                subtitle="Estava em desvantagem no Turn e acertou a mão no River.",
                narrative_lines=[
                    f"{actual_winner.name} estava atrás até o Turn, mas a 5ª carta mudou a história!",
                    f"O River completou sua combinação vitoriosa: {actual_hand_class}.",
                    f"Conquistou o expressivo pote de ${engine.pot:,} no apagar das luzes."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(255, 65, 120),
                intensity=3,
                is_major_event=True
            )))

        # ---------------------------------------------------------------------
        # 3. BLEFE BEM-SUCEDIDO (BLEFE PERFEITO)
        # ---------------------------------------------------------------------
        winner_bluffed = any(a.get("player_idx") == actual_winner.idx and a.get("is_bluff") for a in hand_actions)
        if not winner_was_best or winner_bluffed or (engine.stage == "ENDED" and winner_cls_rank >= 7):
            candidates.append((85, HandHighlight(
                category="TACTICAL",
                event_type="BLEFE_PERFEITO",
                title="★ BLEFE PERFEITO! ★",
                headline=f"{actual_winner.name} enganou a mesa com maestria!",
                subtitle="Venceu sem ter a melhor mão ao forçar a desistência dos rivais.",
                narrative_lines=[
                    f"{actual_winner.name} exerceu forte pressão e fez os adversários foldarem.",
                    "Apostou alto com uma mão vulnerável e levou tudo sem ir a showdown.",
                    f"Lucro espetacular de ${engine.pot:,} fichas na base da pura coragem."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(185, 80, 255),
                intensity=3,
                is_major_event=True
            )))

        # ---------------------------------------------------------------------
        # 4. BLEFE FALHOU / DESCOBERTO
        # ---------------------------------------------------------------------
        failed_bluffs = [a for a in bluff_actions if a.get("player_idx") != actual_winner.idx]
        if failed_bluffs and engine.stage == "SHOWDOWN":
            bluffer_name = failed_bluffs[0]["player_name"]
            candidates.append((78, HandHighlight(
                category="TACTICAL",
                event_type="BLEFE_FALHOU",
                title="★ BLEFE DESCOBERTO! ★",
                headline=f"{actual_winner.name} desmascarou o blefe de {bluffer_name}!",
                subtitle="Oponente tentou assustar a mesa, mas tomou o call da vitória.",
                narrative_lines=[
                    f"{bluffer_name} aumentou alto tentando roubar o pote com blefe.",
                    f"{actual_winner.name} manteve a frieza, pagou a aposta e venceu no showdown.",
                    f"Pote de ${engine.pot:,} garantido pela leitura precisa."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(255, 100, 50),
                intensity=2,
                is_major_event=True
            )))

        # ---------------------------------------------------------------------
        # 5. ALL-IN DRAMÁTICO
        # ---------------------------------------------------------------------
        if has_all_in:
            candidates.append((80, HandHighlight(
                category="TACTICAL",
                event_type="ALL_IN_DECISIVO",
                title="★ TUDO OU NADA NO ALL-IN! ★",
                headline=f"{actual_winner.name} arriscou todo o stack e saiu vitorioso!",
                subtitle="Momento de tensão máxima com todas as fichas no centro da mesa.",
                narrative_lines=[
                    "A rodada atingiu o clímax com a aposta máxima de All-in.",
                    f"{actual_winner.name} segurou a pressão e venceu com {actual_hand_class}.",
                    f"Pote gigante de ${engine.pot:,} fichas conquistado."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(255, 50, 75),
                intensity=3,
                is_major_event=True
            )))

        # ---------------------------------------------------------------------
        # 6. RECORDE DE POTE
        # ---------------------------------------------------------------------
        if is_pot_record and engine.pot >= 600:
            candidates.append((76, HandHighlight(
                category="RECORD",
                event_type="MAIOR_POTE",
                title="★ POTE GIGANTE DA PARTIDA! ★",
                headline=f"Pote acumulou ${engine.pot:,} fichas!",
                subtitle="Uma das maiores disputas financeiras da sessão.",
                narrative_lines=[
                    "Múltiplos aumentos inflaram o pote a valores recordes.",
                    f"{actual_winner.name} prevaleceu com {actual_hand_class}.",
                    f"Adicionou impressionantes ${engine.pot:,} fichas ao seu montante."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(255, 215, 0),
                intensity=3,
                is_major_event=True
            )))

        # ---------------------------------------------------------------------
        # 7. MÃOS INTERMEDIÁRIAS (Flush, Sequência, Trinca, Pares Altos)
        # ---------------------------------------------------------------------
        if winner_cls_rank == 4: # Flush
            candidates.append((70, HandHighlight(
                category="HAND_RANK",
                event_type="FLUSH",
                title="★ FLUSH CONQUISTADO! ★",
                headline=f"{actual_winner.name} completou um Flush!",
                subtitle="Cinco cartas do mesmo naipe asseguraram o triunfo.",
                narrative_lines=[
                    f"Com {actual_hand_class}, dominou as probabilidades pós-flop.",
                    "Uma mão sólida que garantiu a dianteira do início ao fim.",
                    f"Pote: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(46, 204, 113),
                intensity=2,
                is_major_event=engine.pot >= 300
            )))

        elif winner_cls_rank == 5: # Sequência (Straight)
            candidates.append((68, HandHighlight(
                category="HAND_RANK",
                event_type="SEQUENCIA",
                title="★ SEQUÊNCIA PERFEITA! ★",
                headline=f"{actual_winner.name} formou uma Sequência!",
                subtitle="Cinco cartas em ordem numérica conectaram o jogo perfeito.",
                narrative_lines=[
                    f"A combinação de {actual_hand_class} superou a concorrência na mesa.",
                    "Aposta calculada que encontrou o desfecho desejado no showdown.",
                    f"Pote: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(46, 204, 113),
                intensity=2,
                is_major_event=engine.pot >= 300
            )))

        elif winner_cls_rank == 6: # Trinca (Three of a Kind)
            candidates.append((62, HandHighlight(
                category="HAND_RANK",
                event_type="TRINCA",
                title="★ TRINCA DOMINANTE! ★",
                headline=f"{actual_winner.name} venceu com Trinca!",
                subtitle="Três cartas de mesmo valor garantiram o controle do pote.",
                narrative_lines=[
                    f"Com {actual_hand_class}, {actual_winner.name} manteve a vantagem estatística.",
                    "Extraiu fichas dos oponentes com tranquilidade.",
                    f"Pote: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(52, 152, 219),
                intensity=2,
                is_major_event=engine.pot >= 300
            )))

        elif winner_cls_rank == 7: # Dois Pares
            candidates.append((52, HandHighlight(
                category="HAND_RANK",
                event_type="DOIS_PARES",
                title="★ DOIS PARES VENCEDORES! ★",
                headline=f"{actual_winner.name} faturou o pote com Dois Pares.",
                subtitle="Combinação sólida que prevaleceu no confronto final.",
                narrative_lines=[
                    f"Segurando {actual_hand_class}, tomou decisões favoráveis de pot odds.",
                    "Confirmou a vitória no showdown.",
                    f"Pote: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(52, 152, 219),
                intensity=1,
                is_major_event=engine.pot >= 350
            )))

        elif winner_cls_rank == 8: # Par
            # Verifica se é par alto de mão (AA, KK, QQ, JJ)
            is_pocket_aces = False
            if len(actual_winner_cards) >= 2:
                r1, _, _ = CardUtils.card_rank_suit(actual_winner_cards[0])
                r2, _, _ = CardUtils.card_rank_suit(actual_winner_cards[1])
                if r1 == r2 and r1 in ('A', 'K', 'Q'):
                    is_pocket_aces = True
            
            p_title = "★ PAR DE ASES NO SHOWDOWN! ★" if is_pocket_aces else "★ PAR DECISIVO! ★"
            candidates.append((50 if is_pocket_aces else 40, HandHighlight(
                category="HAND_RANK",
                event_type="PAR",
                title=p_title,
                headline=f"{actual_winner.name} garantiu a vitória com Par.",
                subtitle="Foi suficiente para bater as mãos adversárias no showdown.",
                narrative_lines=[
                    f"Com {actual_hand_class}, manteve o stack protegido e saiu na frente.",
                    "Frieza na rodada final para recolher as fichas da mesa.",
                    f"Pote: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(100, 180, 240),
                intensity=1,
                is_major_event=engine.pot >= 350
            )))

        # Fallback genérico caso todos tenham foldado cedo
        if not candidates:
            candidates.append((30, HandHighlight(
                category="GENERIC",
                event_type="VITORIA_PADRAO",
                title="★ VITÓRIA DA RODADA ★",
                headline=f"{actual_winner.name} recolheu o pote da mão #{tracker.total_hands}.",
                subtitle="Os adversários desistiram diante da aposta.",
                narrative_lines=[
                    f"{actual_winner.name} manteve a pressão e levou as fichas sem resistência.",
                    "Jogo eficiente e stack protegido.",
                    f"Pote: ${engine.pot:,} fichas."
                ],
                player_name=actual_winner.name,
                player_idx=actual_winner.idx,
                pot_amount=engine.pot,
                primary_cards=actual_winner_cards,
                board_cards=engine.community_cards,
                color=(46, 204, 113),
                intensity=1,
                is_major_event=has_all_in or engine.pot >= 400
            )))

        # Escolhe o destaque de maior peso/importância
        best_candidate = max(candidates, key=lambda c: c[0])[1]

        # Se houver curiosidade contrafactual ("E SE?"), anexa ao destaque!
        if counterfactual:
            best_candidate.has_counterfactual = True
            best_candidate.counterfactual_title = counterfactual["title"]
            best_candidate.counterfactual_desc = counterfactual["desc"]
            best_candidate.counterfactual_player = counterfactual["player_name"]
            best_candidate.counterfactual_cards = counterfactual["cards"]
            best_candidate.counterfactual_hand_class = counterfactual["hand_class"]

        return best_candidate
