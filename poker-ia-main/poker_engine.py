import random
from typing import List, Tuple, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from treys import Card, Evaluator, Deck

# Suit symbols & colors for GUI rendering
SUIT_SYMBOLS = {
    's': '♠',
    'h': '♥',
    'd': '♦',
    'c': '♣'
}

SUIT_COLORS = {
    's': (30, 41, 59),      # Slate black
    'h': (220, 38, 38),     # Bright Red
    'd': (37, 99, 235),     # Blue / Diamond Red
    'c': (22, 101, 52)      # Green / Club
}

PERSONALITY_CONFIG = {
    "equilibrado": {
        "title": "Equilibrado (Racional)",
        "badge": "♠",
        "color": (59, 130, 246), # Blue
        "desc": "Decisões estritamente por Equity >= Pot Odds"
    },
    "agressivo": {
        "title": "Agressivo (Ousado)",
        "badge": "♥",
        "color": (239, 68, 68),  # Red
        "desc": "Assume mais riscos (-15% de exigência de Equity)"
    },
    "conservador": {
        "title": "Conservador (Cauteloso)",
        "badge": "♦",
        "color": (16, 185, 129), # Emerald
        "desc": "Exige +15% de margem de segurança"
    },
    "blefador": {
        "title": "Blefador (Wildcard)",
        "badge": "♣",
        "color": (139, 92, 246), # Purple
        "desc": "20% de chance de blefar com mãos fracas"
    }
}

HAND_RANKS_PT = {
    "High Card": "Carta Alta",
    "Pair": "Um Par",
    "Two Pair": "Dois Pares",
    "Three of a Kind": "Trinca",
    "Straight": "Sequência",
    "Flush": "Flush (Mesmo Naipe)",
    "Full House": "Full House (Trinca + Par)",
    "Four of a Kind": "Quadra",
    "Straight Flush": "Straight Flush",
    "Royal Flush": "Royal Flush (Sequência Máxima)"
}

class CardUtils:
    @staticmethod
    def card_to_str(card_int: int) -> str:
        """Converts a treys card int to a readable string like 'A♠' or '10♥'."""
        if card_int is None:
            return "??"
        t_str = Card.int_to_str(card_int)
        rank = t_str[0].upper()
        if rank == 'T':
            rank = '10'
        suit_char = t_str[1].lower()
        suit_symbol = SUIT_SYMBOLS.get(suit_char, suit_char)
        return f"{rank}{suit_symbol}"

    @staticmethod
    def card_rank_suit(card_int: int) -> Tuple[str, str, str]:
        """Returns (rank, suit_symbol, suit_char) e.g. ('A', '♠', 's')."""
        if card_int is None:
            return ("?", "?", "s")
        t_str = Card.int_to_str(card_int)
        rank = t_str[0].upper()
        if rank == 'T':
            rank = '10'
        suit_char = t_str[1].lower()
        suit_symbol = SUIT_SYMBOLS.get(suit_char, suit_char)
        return (rank, suit_symbol, suit_char)

    @staticmethod
    def translate_hand_class(class_str: str) -> str:
        """Translates Treys hand class string to friendly Portuguese."""
        return HAND_RANKS_PT.get(class_str, class_str)


@dataclass
class Player:
    idx: int
    name: str
    personality: str # "equilibrado", "agressivo", "conservador", "blefador"
    stack: int = 1000
    hand: List[int] = field(default_factory=list)
    current_bet: int = 0
    total_bet_this_hand: int = 0
    is_active: bool = True
    is_all_in: bool = False
    last_action: str = ""
    last_telemetry: Optional[Dict] = None
    hands_won: int = 0

    def reset_for_hand(self):
        self.hand = []
        self.current_bet = 0
        self.total_bet_this_hand = 0
        self.is_active = (self.stack > 0)
        self.is_all_in = False
        self.last_action = ""
        self.last_telemetry = None


class PokerEngine:
    def __init__(self, initial_stack: int = 1000, small_blind: int = 10, big_blind: int = 20):
        self.initial_stack = initial_stack
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.evaluator = Evaluator()

        # Initialize 4 AI players with their assigned positions and personalities
        self.players: List[Player] = [
            Player(0, "IA Racional", "equilibrado", initial_stack),
            Player(1, "IA Ousada", "agressivo", initial_stack),
            Player(2, "IA Cautelosa", "conservador", initial_stack),
            Player(3, "IA Blefadora", "blefador", initial_stack)
        ]

        self.dealer_idx = 0
        self.history_log: List[str] = []
        self.hand_count = 0
        self.start_new_hand(reset_dealer=False)

    def log(self, msg: str):
        self.history_log.append(msg)

    def get_active_players(self) -> List[Player]:
        return [p for p in self.players if p.is_active]

    def get_active_non_allin_players(self) -> List[Player]:
        return [p for p in self.players if p.is_active and not p.is_all_in]

    def start_new_hand(self, reset_dealer: bool = True):
        """Starts a fresh Texas Hold'em hand."""
        self.hand_count += 1
        if reset_dealer:
            self.dealer_idx = (self.dealer_idx + 1) % 4

        # Reload broke players so game can continue indefinitely in presentation
        for p in self.players:
            if p.stack <= 0:
                p.stack = self.initial_stack
                self.log(f"🔄 {p.name} teve o stack recarregado para {self.initial_stack} fichas.")
            p.reset_for_hand()

        self.deck = Deck()
        # Deal 2 cards to each player
        for p in self.players:
            p.hand = self.deck.draw(2)

        self.community_cards: List[int] = []
        self.pot = 0
        self.stage = "PREFLOP" # PREFLOP, FLOP, TURN, RIVER, SHOWDOWN, ENDED
        self.hand_ended = False
        self.winners_info: List[Dict] = []
        self.acted_this_round: Set[int] = set()
        self.current_high_bet = self.big_blind
        self.raises_this_round = 0
        self.max_raises = 3

        # Post Blinds
        sb_idx = (self.dealer_idx + 1) % 4
        bb_idx = (self.dealer_idx + 2) % 4

        sb_player = self.players[sb_idx]
        bb_player = self.players[bb_idx]

        sb_amount = self._deduct_chips(sb_player, self.small_blind)
        bb_amount = self._deduct_chips(bb_player, self.big_blind)

        sb_player.last_action = f"SB ({sb_amount})"
        bb_player.last_action = f"BB ({bb_amount})"

        self.log(f"--- MÃO #{self.hand_count} INICIADA ---")
        self.log(f"Dealer: {self.players[self.dealer_idx].name} | SB: {sb_player.name} ({sb_amount}) | BB: {bb_player.name} ({bb_amount})")

        # In 4-player game preflop, action starts on UTG (Player after BB)
        self.current_player_idx = (self.dealer_idx + 3) % 4

    def _deduct_chips(self, player: Player, amount: int) -> int:
        actual = min(player.stack, amount)
        player.stack -= actual
        player.current_bet += actual
        player.total_bet_this_hand += actual
        self.pot += actual
        if player.stack == 0:
            player.is_all_in = True
        return actual

    def get_to_call(self, player: Player) -> int:
        return max(0, self.current_high_bet - player.current_bet)

    def _next_player(self, from_idx: int) -> int:
        """Finds next active non-allin player clockwise."""
        for step in range(1, 4):
            candidate_idx = (from_idx + step) % 4
            candidate = self.players[candidate_idx]
            if candidate.is_active and not candidate.is_all_in:
                return candidate_idx
        # If no non-all-in player is found, return current
        return from_idx

    def is_betting_round_complete(self) -> bool:
        """Checks if current stage's betting round is complete."""
        active = self.get_active_players()
        if len(active) <= 1:
            return True

        active_non_allin = self.get_active_non_allin_players()
        if len(active_non_allin) <= 1:
            # If at most 1 player can still bet, check if all active non-allin have matched high bet
            if not active_non_allin or (active_non_allin[0].idx in self.acted_this_round and active_non_allin[0].current_bet == self.current_high_bet):
                return True

        # All active non-allin players must have acted and matched current high bet
        for p in active_non_allin:
            if p.idx not in self.acted_this_round:
                return False
            if p.current_bet != self.current_high_bet:
                return False

        return True

    def player_action(self, player_idx: int, action: str, raise_amount: int = 0) -> str:
        """
        Executes action for player: 'fold', 'check', 'call', 'raise', 'all-in'
        """
        if self.hand_ended or player_idx != self.current_player_idx:
            return "Ação fora de turno ou mão encerrada."

        player = self.players[player_idx]
        to_call = self.get_to_call(player)

        if action == "fold":
            player.is_active = False
            player.last_action = "FOLD"
            self.log(f"{player.name} desistiu (Fold).")

            # Check if only 1 player remains
            active = self.get_active_players()
            if len(active) == 1:
                self._settle_single_survivor(active[0])
                return "fold_win"

        elif action == "check":
            if to_call > 0:
                # If there's an amount to call, player can't check; treat as call or fold
                return self.player_action(player_idx, "call")
            player.last_action = "CHECK"
            self.acted_this_round.add(player_idx)
            self.log(f"{player.name} checou (Check).")

        elif action == "call":
            paid = self._deduct_chips(player, to_call)
            player.last_action = f"CALL ({paid})" if not player.is_all_in else "CALL (ALL-IN)"
            self.acted_this_round.add(player_idx)
            self.log(f"{player.name} pagou {paid} fichas (Call).")

        elif action in ("raise", "all-in"):
            # Check raise cap (unless it's an all-in call / bet)
            is_all_in_attempt = (raise_amount >= player.stack - to_call)
            if not is_all_in_attempt and self.raises_this_round >= self.max_raises:
                # Cap reached: convert to call
                return self.player_action(player_idx, "call")

            self.raises_this_round += 1
            # Ensure minimum raise
            actual_raise = max(self.big_blind, raise_amount)
            total_needed = to_call + actual_raise
            paid = self._deduct_chips(player, total_needed)

            self.current_high_bet = player.current_bet
            if player.is_all_in:
                player.last_action = f"ALL-IN ({player.current_bet})"
                self.log(f"💥 {player.name} foi ALL-IN ({player.current_bet} fichas)!")
            else:
                player.last_action = f"RAISE (+{paid})"
                self.log(f"🚀 {player.name} aumentou para {self.current_high_bet} (+{paid} fichas).")

            # Re-open betting for other active players
            self.acted_this_round = {player_idx}

        # Check if betting round has concluded
        if self.is_betting_round_complete():
            self.advance_stage()
        else:
            self.current_player_idx = self._next_player(player_idx)

        return "ok"

    def advance_stage(self):
        """Advances game state to next round: FLOP -> TURN -> RIVER -> SHOWDOWN."""
        # Reset current round bets
        for p in self.players:
            p.current_bet = 0
        self.current_high_bet = 0
        self.acted_this_round = set()
        self.raises_this_round = 0

        # Check active count
        active = self.get_active_players()
        if len(active) <= 1:
            if active:
                self._settle_single_survivor(active[0])
            return

        # Starting player post-flop is first active player clockwise from dealer
        self.current_player_idx = self._next_player(self.dealer_idx)

        if self.stage == "PREFLOP":
            self.stage = "FLOP"
            self.community_cards.extend(self.deck.draw(3))
            cards_str = [CardUtils.card_to_str(c) for c in self.community_cards]
            self.log(f"--- FLOP ({', '.join(cards_str)}) --- Pote: {self.pot}")
        elif self.stage == "FLOP":
            self.stage = "TURN"
            self.community_cards.extend(self.deck.draw(1))
            cards_str = [CardUtils.card_to_str(c) for c in self.community_cards]
            self.log(f"--- TURN ({', '.join(cards_str)}) --- Pote: {self.pot}")
        elif self.stage == "TURN":
            self.stage = "RIVER"
            self.community_cards.extend(self.deck.draw(1))
            cards_str = [CardUtils.card_to_str(c) for c in self.community_cards]
            self.log(f"--- RIVER ({', '.join(cards_str)}) --- Pote: {self.pot}")
        elif self.stage == "RIVER":
            self.stage = "SHOWDOWN"
            self.evaluate_showdown()

        # If 0 or 1 active non-allin player left, auto-run out remaining board cards to SHOWDOWN
        if not self.hand_ended and self.stage != "SHOWDOWN":
            active_non_allin = self.get_active_non_allin_players()
            if len(active_non_allin) <= 1:
                self.advance_stage()

    def _settle_single_survivor(self, winner: Player):
        """Awards entire pot to single remaining player when everyone else folds."""
        self.hand_ended = True
        self.stage = "ENDED"
        winner.stack += self.pot
        winner.hands_won += 1
        self.winners_info = [{
            "player": winner,
            "amount": self.pot,
            "hand_class": "Todos os oponentes desistiram (Fold)",
            "hand_cards": winner.hand
        }]
        self.log(f"🏆 {winner.name} venceu {self.pot} fichas (todos desistiram)!")

    def evaluate_showdown(self):
        """Evaluates hands at Showdown using Treys Evaluator with accurate side-pot resolution."""
        self.stage = "SHOWDOWN"
        self.hand_ended = True

        active_players = self.get_active_players()
        if not active_players:
            return

        # Score hands with Treys (lower score = better hand)
        scored_players = []
        for p in active_players:
            score = self.evaluator.evaluate(self.community_cards, p.hand)
            rank_class = self.evaluator.get_rank_class(score)
            raw_class_str = self.evaluator.class_to_string(rank_class)
            class_str = CardUtils.translate_hand_class(raw_class_str)
            scored_players.append({
                "player": p,
                "score": score,
                "class_str": class_str,
                "total_bet": p.total_bet_this_hand
            })

        # Multi-tiered side-pot resolution algorithm
        all_bets = sorted(list(set(p.total_bet_this_hand for p in self.players if p.total_bet_this_hand > 0)))
        payouts: Dict[int, int] = {p.idx: 0 for p in self.players}
        prev_level = 0

        for bet_level in all_bets:
            contribution_per_player = bet_level - prev_level
            tier_pot = sum(
                min(contribution_per_player, max(0, p.total_bet_this_hand - prev_level))
                for p in self.players
            )
            
            if tier_pot <= 0:
                continue

            eligible = [sp for sp in scored_players if sp["total_bet"] >= bet_level]
            if not eligible:
                eligible = scored_players

            best_score = min(sp["score"] for sp in eligible)
            tier_winners = [sp for sp in eligible if sp["score"] == best_score]

            split_share = tier_pot // len(tier_winners)
            remainder = tier_pot % len(tier_winners)

            for w in tier_winners:
                payouts[w["player"].idx] += split_share
            if remainder > 0 and tier_winners:
                payouts[tier_winners[0]["player"].idx] += remainder

            prev_level = bet_level

        # Apply payouts to stacks and build summary
        self.winners_info = []
        for sp in scored_players:
            p_idx = sp["player"].idx
            won = payouts[p_idx]
            if won > 0:
                sp["player"].stack += won
                sp["player"].hands_won += 1
                self.winners_info.append({
                    "player": sp["player"],
                    "amount": won,
                    "hand_class": sp["class_str"],
                    "hand_cards": sp["player"].hand
                })
                cards_readable = [CardUtils.card_to_str(c) for c in sp["player"].hand]
                self.log(f"🏆 {sp['player'].name} venceu {won} fichas com {sp['class_str']} ({', '.join(cards_readable)})!")


class RoundAnalyzer:
    """Analyzes tactical highlights at the end of each round (bluffs, fold mistakes, value wins)."""

    @staticmethod
    def analyze_round(engine: PokerEngine) -> Dict[str, Any]:
        if not engine.hand_ended or not engine.winners_info:
            return {
                "tag": "EM_ANDAMENTO",
                "title": "Partida em Andamento",
                "headline": "Aguardando",
                "desc": "Aguardando conclusão da rodada...",
                "narrative_lines": ["Partida em andamento."],
                "color": (148, 163, 184)
            }

        evaluator = engine.evaluator
        actual_winner = engine.winners_info[0]["player"]
        
        # Build complete 5-card board if hand ended prematurely (preflop/flop fold)
        full_board = list(engine.community_cards)
        if len(full_board) < 5:
            known_cards = set(full_board)
            for p in engine.players:
                known_cards.update(p.hand)
            available = [c for c in Deck().cards if c not in known_cards]
            needed = 5 - len(full_board)
            full_board.extend(available[:needed])

        # Score all 4 players' hands against the full board
        scores = {}
        for p in engine.players:
            s = evaluator.evaluate(full_board, p.hand)
            cls_rank = evaluator.get_rank_class(s)
            raw_cls_name = evaluator.class_to_string(cls_rank)
            cls_name = CardUtils.translate_hand_class(raw_cls_name)
            scores[p.idx] = {
                "player": p,
                "score": s,
                "hand_class": cls_name
            }

        best_score = min(info["score"] for info in scores.values())
        best_players = [info["player"] for info in scores.values() if info["score"] == best_score]
        best_p = best_players[0]
        best_class = scores[best_p.idx]["hand_class"]

        winner_was_best = actual_winner.idx in [p.idx for p in best_players]

        # Check if there was an all-in
        has_all_in = any(p.is_all_in for p in engine.players)

        # Case 1: Best theoretical player folded to a bluff/aggression
        if not winner_was_best:
            folded_best = [p for p in best_players if not p.is_active]
            if folded_best:
                f_player = folded_best[0]
                f_class = scores[f_player.idx]["hand_class"]
                return {
                    "tag": "CAIU_NO_BLEFE",
                    "title": "🚨 DESTAQUE DA RODADA",
                    "headline": "CAIU NO BLEFE!",
                    "desc": f"{f_player.name} ({f_class}) desistiu da melhor mão sob a pressão de {actual_winner.name}!",
                    "narrative_lines": [
                        f"A {actual_winner.name} venceu o pote de ${engine.pot:,} sem ter a melhor mão!",
                        f"Baseado puramente nas cartas, a {f_player.name} teria ganho com {f_class}.",
                        "No entanto, ela desistiu (Fold) devido à pressão da aposta alta."
                    ],
                    "color": (239, 68, 68), # Red
                    "winner": actual_winner,
                    "best_player": f_player,
                    "winner_cards": actual_winner.hand,
                    "best_cards": f_player.hand,
                    "is_major_event": True
                }
            else:
                w_class = scores[actual_winner.idx]["hand_class"]
                return {
                    "tag": "BLEFE_SUCESSO",
                    "title": "🎭 O QUE ACONTECEU AQUI?",
                    "headline": "BLEFE DE SUCESSO!",
                    "desc": f"{actual_winner.name} levou o pote de ${engine.pot:,} com um blefe oportuno!",
                    "narrative_lines": [
                        f"A {actual_winner.name} conquistou o pote de ${engine.pot:,} com um blefe bem-sucedido!",
                        f"Mesmo com um jogo modesto ({w_class}), forçou os rivais a recuarem.",
                        "A agressividade no momento certo superou a probabilidade das cartas."
                    ],
                    "color": (139, 92, 246), # Purple
                    "winner": actual_winner,
                    "best_player": best_p,
                    "winner_cards": actual_winner.hand,
                    "best_cards": best_p.hand,
                    "is_major_event": True
                }
        else:
            # Case 2: Winner had the best hand
            headline_str = "VITÓRIA HISTÓRICA NO ALL-IN!" if has_all_in else "VITÓRIA JUSTA!"
            return {
                "tag": "VITORIA_JUSTA",
                "title": "🏆 DESTAQUE DA RODADA",
                "headline": headline_str,
                "desc": f"{actual_winner.name} confirmou o favoritismo e venceu com {best_class}.",
                "narrative_lines": [
                    f"A {actual_winner.name} confirmou o favoritismo e venceu o pote de ${engine.pot:,}!",
                    f"Segurando {best_class}, suas decisões foram 100% embasadas na probabilidade real.",
                    "O jogo disciplinado e a expectativa matemática geraram o resultado esperado."
                ],
                "color": (34, 197, 94), # Emerald green
                "winner": actual_winner,
                "best_player": actual_winner,
                "winner_cards": actual_winner.hand,
                "best_cards": actual_winner.hand,
                "is_major_event": has_all_in or engine.pot >= 400
            }
