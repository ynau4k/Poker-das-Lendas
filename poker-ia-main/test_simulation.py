import sys
import io
import time
from collections import defaultdict
from poker_engine import PokerEngine, CardUtils
from poker_ai import PokerAI

# Ensure utf-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_automated_test(num_hands: int = 50, simulations_per_decision: int = 400):
    print("=" * 70)
    print(f"🃏 INICIANDO TESTE AUTOMATIZADO ({num_hands} PARTIDAS DE POKER - 4 IAs)")
    print("=" * 70)

    engine = PokerEngine(initial_stack=1000, small_blind=10, big_blind=20)
    ai = PokerAI(simulations=simulations_per_decision)

    stats = {
        p.name: {
            "wins": 0,
            "chips_won": 0,
            "folds": 0,
            "calls": 0,
            "raises": 0,
            "bluffs": 0,
            "personality": p.personality
        }
        for p in engine.players
    }

    start_time = time.time()

    for hand_idx in range(1, num_hands + 1):
        # Start new hand (after first hand)
        if hand_idx > 1:
            engine.start_new_hand(reset_dealer=True)

        action_count_this_hand = 0
        max_safety_actions = 100 # Guard against any infinite loops

        while not engine.hand_ended:
            action_count_this_hand += 1
            if action_count_this_hand > max_safety_actions:
                raise RuntimeError(f"Loop infinito detectado na mão #{hand_idx}!")

            curr_idx = engine.current_player_idx
            curr_player = engine.players[curr_idx]
            
            # Active opponents count
            active_opponents = len([p for p in engine.get_active_players() if p.idx != curr_idx])
            cost_to_call = engine.get_to_call(curr_player)

            # AI Decision
            decision = ai.decide(
                player=curr_player,
                community_cards=engine.community_cards,
                cost_to_call=cost_to_call,
                current_pot=engine.pot,
                num_active_opponents=active_opponents,
                big_blind=engine.big_blind
            )

            action = decision["action"]
            raise_amount = decision["raise_amount"]

            # Record stats
            if action == "fold":
                stats[curr_player.name]["folds"] += 1
            elif action == "call":
                stats[curr_player.name]["calls"] += 1
            elif action in ("raise", "all-in"):
                stats[curr_player.name]["raises"] += 1

            if decision.get("is_bluff"):
                stats[curr_player.name]["bluffs"] += 1

            # Execute action
            engine.player_action(curr_idx, action, raise_amount)

        # Record winners
        for win_info in engine.winners_info:
            w_player = win_info["player"]
            amount = win_info["amount"]
            stats[w_player.name]["wins"] += 1
            stats[w_player.name]["chips_won"] += amount

        if hand_idx % 10 == 0 or hand_idx == num_hands:
            print(f"✅ Mão #{hand_idx:02d} concluída com sucesso! (Estágio: {engine.stage}, Pote: {engine.pot} fichas)")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"📊 RELATÓRIO FINAL DE SIMULAÇÃO ({num_hands} MÃOS EM {elapsed:.2f}s)")
    print("=" * 70)
    print(f"{'JOGADOR / PERFIL':<28} | {'VITÓRIAS':<8} | {'FICHAS GANHAS':<13} | {'STACK FINAL':<11} | {'FOLDS':<6} | {'RAISES':<7} | {'BLEFES':<6}")
    print("-" * 95)

    for p in engine.players:
        s = stats[p.name]
        p_name = f"{p.name} ({s['personality']})"
        print(f"{p_name:<28} | {s['wins']:<8} | {s['chips_won']:<13} | {p.stack:<11} | {s['folds']:<6} | {s['raises']:<7} | {s['bluffs']:<6}")

    print("=" * 70)
    print("🎉 MOTOR VALIDADO COM 100% DE SUCESSO SEM TRAVAMENTOS OU ERROS!")
    print("=" * 70)

if __name__ == "__main__":
    run_automated_test(num_hands=50, simulations_per_decision=300)
