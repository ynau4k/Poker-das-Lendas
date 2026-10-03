import random
from typing import List, Tuple, Dict, Any, Optional
from treys import Card, Evaluator, Deck
from poker_engine import CardUtils, Player

class PokerAI:
    def __init__(self, simulations: int = 1000):
        self.simulations = simulations
        self.evaluator = Evaluator()
        self.full_deck = Deck().cards

    def calculate_multiway_equity(
        self,
        ai_hand: List[int],
        community_cards: List[int],
        num_active_opponents: int = 3
    ) -> Tuple[float, int]:
        """
        Calculates multiway equity via Monte Carlo simulation against N active opponents.
        Removes known blockers (AI hand + community cards).
        """
        known_cards = set(ai_hand + community_cards)
        blockers_count = len(known_cards)
        available_deck = [c for c in self.full_deck if c not in known_cards]

        num_active_opponents = max(1, num_active_opponents)
        cards_needed_opps = num_active_opponents * 2
        cards_needed_board = 5 - len(community_cards)
        total_sample_needed = cards_needed_opps + cards_needed_board

        wins = 0.0

        for _ in range(self.simulations):
            sampled = random.sample(available_deck, total_sample_needed)
            
            # Extract opponents hands
            opp_hands = [
                sampled[i * 2 : (i + 1) * 2]
                for i in range(num_active_opponents)
            ]
            
            # Complete the 5-card board
            board_runout = community_cards + sampled[cards_needed_opps:]

            # Score AI hand
            ai_score = self.evaluator.evaluate(board_runout, ai_hand)
            
            # Score Opponent hands
            best_opp_score = min(
                self.evaluator.evaluate(board_runout, opp_h)
                for opp_h in opp_hands
            )

            if ai_score < best_opp_score:
                wins += 1.0 # AI wins outright
            elif ai_score == best_opp_score:
                # Count ties
                ties_count = sum(1 for opp_h in opp_hands if self.evaluator.evaluate(board_runout, opp_h) == ai_score)
                wins += 1.0 / (1.0 + ties_count)

        equity = (wins / self.simulations) * 100.0
        return round(equity, 2), blockers_count

    def calculate_pot_odds(self, cost_to_call: int, current_pot: int) -> float:
        """Calculates Pot Odds as cost_to_call / (current_pot + cost_to_call)."""
        if cost_to_call <= 0:
            return 0.0
        total_pot = current_pot + cost_to_call
        pot_odds = (cost_to_call / total_pot) * 100.0
        return round(pot_odds, 2)

    def decide(
        self,
        player: Player,
        community_cards: List[int],
        cost_to_call: int,
        current_pot: int,
        num_active_opponents: int,
        big_blind: int = 20
    ) -> Dict[str, Any]:
        """
        Computes Equity, Pot Odds and applies personality-specific behavioral bias:
        - equilibrado: Equity >= Pot Odds
        - agressivo: -15% equity threshold, high raise frequency
        - conservador: +15% equity safety margin required
        - blefador: 20% bluff chance on weak hands
        """
        equity, blockers_count = self.calculate_multiway_equity(
            player.hand, community_cards, num_active_opponents
        )
        pot_odds = self.calculate_pot_odds(cost_to_call, current_pot)

        # Hand class description if community cards present
        hand_class_str = "Pré-Flop"
        if len(community_cards) >= 3:
            rank_score = self.evaluator.evaluate(community_cards, player.hand)
            rank_class = self.evaluator.get_rank_class(rank_score)
            hand_class_str = self.evaluator.class_to_string(rank_class)

        personality = player.personality
        action = "check" if cost_to_call == 0 else "call"
        raise_amount = 0
        is_bluff = False
        justification = ""

        # -------------------------------------------------------------
        # 1. PERFIL: EQUILIBRADO (Racional)
        # -------------------------------------------------------------
        if personality == "equilibrado":
            if cost_to_call == 0:
                if equity > 65.0:
                    action = "raise"
                    raise_amount = max(big_blind * 2, current_pot // 2)
                    justification = "Aumentou por valor (Mão muito forte)"
                elif equity > 45.0:
                    action = "raise"
                    raise_amount = big_blind
                    justification = "Apostou para valorizar o pote"
                else:
                    action = "check"
                    justification = "Passou a vez (Mão razoável)"
            else:
                if equity > 70.0:
                    action = "raise"
                    raise_amount = max(cost_to_call * 2, big_blind * 2)
                    justification = "Re-aumentou forte (Mão dominante)"
                elif equity > (pot_odds + 10.0):
                    action = "raise"
                    raise_amount = max(cost_to_call, big_blind)
                    justification = "Aumentou a aposta (Boa vantagem)"
                elif equity >= pot_odds:
                    action = "call"
                    justification = "Pagou a aposta (Preço favorável)"
                else:
                    action = "fold"
                    justification = "Desistiu da rodada (Risco alto)"

        # -------------------------------------------------------------
        # 2. PERFIL: AGRESSIVO (Ousado) - Reduz threshold em 15%
        # -------------------------------------------------------------
        elif personality == "agressivo":
            aggro_threshold = max(0.0, pot_odds - 15.0)

            if cost_to_call == 0:
                if equity > 45.0:
                    action = "raise"
                    raise_amount = max(big_blind * 3, current_pot // 2)
                    justification = "Aumentou pesado para pressionar a mesa"
                elif equity > 25.0:
                    action = "raise"
                    raise_amount = big_blind
                    justification = "Aposta de sondagem (Agressão)"
                else:
                    action = "check"
                    justification = "Passou a vez (Aguardando oportunidade)"
            else:
                if equity > 55.0:
                    action = "raise"
                    raise_amount = max(cost_to_call * 3, current_pot // 2, big_blind * 2)
                    justification = "Re-aumento agressivo (Ataque total)"
                elif equity >= aggro_threshold:
                    if equity >= pot_odds:
                        action = "raise"
                        raise_amount = max(cost_to_call, big_blind)
                        justification = "Aumentou a aposta com confiança"
                    else:
                        action = "call"
                        justification = "Pagou para ver a próxima carta"
                else:
                    action = "fold"
                    justification = "Desistiu (Mão sem perspectiva)"

        # -------------------------------------------------------------
        # 3. PERFIL: CONSERVADOR (Cauteloso) - Exige +15% de margem
        # -------------------------------------------------------------
        elif personality == "conservador":
            safe_threshold = pot_odds + 15.0

            if cost_to_call == 0:
                if equity > 75.0:
                    action = "raise"
                    raise_amount = max(big_blind * 2, current_pot // 3)
                    justification = "Aumentou seguro (Mão premium)"
                else:
                    action = "check"
                    justification = "Passou a vez (Controle de risco)"
            else:
                if equity > 80.0:
                    action = "raise"
                    raise_amount = max(cost_to_call * 2, big_blind * 2)
                    justification = "Re-aumento seguro (Quase certeza de vitória)"
                elif equity >= safe_threshold:
                    action = "call"
                    justification = "Pagou com margem de segurança"
                else:
                    action = "fold"
                    justification = "Desistiu (Protegendo as fichas)"

        # -------------------------------------------------------------
        # 4. PERFIL: BLEFADOR (Wildcard) - 20% de chance de blefe
        # -------------------------------------------------------------
        elif personality == "blefador":
            weak_hand = (equity < pot_odds or equity < 35.0)
            roll_bluff = random.random() < 0.20

            if weak_hand and roll_bluff:
                is_bluff = True
                action = "raise"
                bluff_size = max(cost_to_call * 3, current_pot, big_blind * 3)
                raise_amount = min(bluff_size, player.stack)
                justification = "BLEFOU ALTO! Tentando assustar a mesa"
            else:
                if cost_to_call == 0:
                    if equity > 60.0:
                        action = "raise"
                        raise_amount = max(big_blind * 2, current_pot // 2)
                        justification = "Aumentou por valor (Mão forte)"
                    else:
                        action = "check"
                        justification = "Passou a vez (Mão simples)"
                else:
                    if equity > 70.0:
                        action = "raise"
                        raise_amount = max(cost_to_call * 2, big_blind * 2)
                        justification = "Re-aumentou com mão forte"
                    elif equity >= pot_odds:
                        action = "call"
                        justification = "Pagou a aposta com chance real"
                    else:
                        action = "fold"
                        justification = "Desistiu (Não vale arriscar)"

        # Cap raise by available stack
        if action == "raise":
            available_for_raise = player.stack - cost_to_call
            if available_for_raise <= 0:
                action = "call"
                raise_amount = 0
            else:
                raise_amount = min(raise_amount, available_for_raise)
                if raise_amount == available_for_raise:
                    action = "all-in"

        telemetry = {
            "player_name": player.name,
            "personality": personality,
            "equity": equity,
            "pot_odds": pot_odds,
            "blockers_count": blockers_count,
            "hand_class_str": hand_class_str,
            "action": action,
            "raise_amount": raise_amount,
            "is_bluff": is_bluff,
            "justification": justification,
            "simulations": self.simulations
        }
        player.last_telemetry = telemetry
        return telemetry
