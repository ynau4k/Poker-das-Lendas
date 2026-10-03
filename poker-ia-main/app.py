import streamlit as st
import time
from poker_engine import PokerEngine, CardUtils
from poker_ai import PokerAI

# Set page configuration
st.set_page_config(
    page_title="Texas Hold'em Poker AI - Dashboard Telemétrico",
    page_icon="♠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stApp {
        background: radial-gradient(circle at 50% 30%, #1e293b 0%, #0f172a 100%);
    }
    .poker-table {
        background: radial-gradient(circle, #065f46 0%, #047857 70%, #022c22 100%);
        border: 12px solid #b45309;
        border-radius: 40px;
        padding: 24px;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.7), 0 20px 25px -5px rgba(0,0,0,0.5);
        text-align: center;
        margin-bottom: 20px;
    }
    .card-container {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-wrap: wrap;
    }
    .metric-card {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .pot-badge {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #ffffff;
        font-size: 24px;
        font-weight: 800;
        padding: 8px 24px;
        border-radius: 20px;
        display: inline-block;
        box-shadow: 0 4px 10px rgba(217, 119, 6, 0.4);
        margin: 10px 0;
    }
    .ai-mind-box {
        background-color: #1e1b4b;
        border: 2px solid #6366f1;
        border-radius: 12px;
        padding: 18px;
        font-family: 'Courier New', Courier, monospace;
        color: #e0e7ff;
    }
    .stProgress > div > div > div > div {
        background-color: #6366f1;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'game' not in st.session_state:
    st.session_state.game = PokerEngine(initial_stack=1000, small_blind=10, big_blind=20)

if 'simulations' not in st.session_state:
    st.session_state.simulations = 2000

if 'ai' not in st.session_state:
    st.session_state.ai = PokerAI(simulations=st.session_state.simulations)

if 'telemetry' not in st.session_state:
    st.session_state.telemetry = None

if 'show_ai_cards' not in st.session_state:
    st.session_state.show_ai_cards = True

game: PokerEngine = st.session_state.game
ai: PokerAI = st.session_state.ai

# Sidebar Controls & Settings
st.sidebar.title("⚙️ Configurações da IA")
st.sidebar.markdown("---")

num_sims = st.sidebar.slider(
    "Simulações de Monte Carlo",
    min_value=500,
    max_value=5000,
    value=st.session_state.simulations,
    step=500,
    help="Número de iterações de Monte Carlo para calcular a Equity da IA."
)
if num_sims != st.session_state.simulations:
    st.session_state.simulations = num_sims
    st.session_state.ai = PokerAI(simulations=num_sims)
    st.sidebar.success(f"Simulações atualizadas para {num_sims}!")

st.session_state.show_ai_cards = st.sidebar.checkbox(
    "👁️ Revelar Mão da IA (Modo Aula/Apresentação)",
    value=st.session_state.show_ai_cards
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reiniciar Partida Inteira (Stack R$1.000)"):
    st.session_state.game = PokerEngine(initial_stack=1000, small_blind=10, big_blind=20)
    st.session_state.telemetry = None
    st.rerun()

st.sidebar.markdown("""
### 📚 Sobre o Projeto
**Poker AI Engine v1.0**
- **Algoritmo:** Simulação Monte Carlo + Pot Odds.
- **Biblioteca Evaluator:** `treys`
- **Foco:** Decisão Matemática em Tempo Real para Demonstração Universitária.
""")

# Automatic AI Turn Handler
def trigger_ai_turn():
    if not game.hand_ended and game.current_turn == 'ai':
        cost_to_call = game.get_to_call('ai')
        telemetry = ai.decide_action(
            ai_hand=game.ai_hand,
            community_cards=game.community_cards,
            cost_to_call=cost_to_call,
            current_pot=game.pot,
            ai_stack=game.ai_stack,
            human_stack=game.human_stack,
            min_raise=game.big_blind
        )
        st.session_state.telemetry = telemetry

        # Execute decision in game engine
        action = telemetry['action']
        raise_amount = telemetry['raise_amount']
        game.player_action('ai', action, raise_amount)

# Check if AI needs to move initially
if not game.hand_ended and game.current_turn == 'ai':
    trigger_ai_turn()

# HEADER
st.title("♠️ Texas Hold'em AI — Agente Inteligente & Telemetria")
st.caption("Demonstração de Inteligência Artificial para Poker baseada em Monte Carlo e Teoria dos Jogos")

# MAIN LAYOUT: 2 Columns (Mesa de Jogo vs Mente da IA)
col_table, col_mind = st.columns([1.3, 1], gap="large")

# ==================== COLUMN 1: MESA DE JOGO ====================
with col_table:
    st.subheader("🏟️ Mesa de Jogo")
    
    # Poker Table Visual Container
    st.markdown('<div class="poker-table">', unsafe_allow_html=True)
    
    # 1. AI PLAYER AREA (Top of Table)
    st.markdown("#### 🤖 Agente de IA")
    c_ai1, c_ai2, c_ai3 = st.columns([1, 2, 1])
    with c_ai2:
        ai_cards_html = "".join([
            CardUtils.card_to_html(c, face_down=(not st.session_state.show_ai_cards and not game.hand_ended))
            for c in game.ai_hand
        ])
        st.markdown(f'<div class="card-container">{ai_cards_html}</div>', unsafe_allow_html=True)
        st.markdown(f"**Stack IA:** `{game.ai_stack}` fichas | **Aposta Rodada:** `{game.ai_bet_stage}`")
        if game.current_turn == 'ai' and not game.hand_ended:
            st.info("🤔 IA está pensando...")

    st.markdown("<hr style='border-color: #059669; margin: 15px 0;'>", unsafe_allow_html=True)

    # 2. COMMUNITY CARDS & POT (Center of Table)
    st.markdown("#### 🎰 Cartas Comunitárias (Mesa)")
    if len(game.community_cards) == 0:
        comm_cards_html = CardUtils.card_to_html(None, face_down=True) * 5
    else:
        comm_cards_html = "".join([CardUtils.card_to_html(c) for c in game.community_cards])
        # Fill remaining slots with back cards if river not reached
        remaining_slots = 5 - len(game.community_cards)
        if remaining_slots > 0:
            comm_cards_html += CardUtils.card_to_html(None, face_down=True) * remaining_slots

    st.markdown(f'<div class="card-container">{comm_cards_html}</div>', unsafe_allow_html=True)
    
    # POT BADGE
    st.markdown(f'<div class="pot-badge">POTE ATUAL: {game.pot} FICHAS</div>', unsafe_allow_html=True)
    st.markdown(f"**Estágio Atual:** `{game.stage}`")

    st.markdown("<hr style='border-color: #059669; margin: 15px 0;'>", unsafe_allow_html=True)

    # 3. HUMAN PLAYER AREA (Bottom of Table)
    st.markdown("#### 👤 Você (Jogador Humano)")
    c_h1, c_h2, c_h3 = st.columns([1, 2, 1])
    with c_h2:
        human_cards_html = "".join([CardUtils.card_to_html(c) for c in game.human_hand])
        st.markdown(f'<div class="card-container">{human_cards_html}</div>', unsafe_allow_html=True)
        st.markdown(f"**Seu Stack:** `{game.human_stack}` fichas | **Sua Aposta Rodada:** `{game.human_bet_stage}`")

    st.markdown('</div>', unsafe_allow_html=True) # End poker-table div

    # SHOWDOWN / WINNER ANNOUNCEMENT
    if game.hand_ended:
        st.markdown("---")
        if game.winner == 'human':
            st.balloons()
            st.success(f"🎉 **VOCÊ VENCEU!** {game.win_reason}")
        elif game.winner == 'ai':
            st.error(f"🤖 **A IA VENCEU!** {game.win_reason}")
        else:
            st.warning(f"🤝 **EMPATE!** {game.win_reason}")
            
        if st.button("🃏 Jogar Próxima Mão", type="primary", use_container_width=True):
            game.reset_hand()
            st.session_state.telemetry = None
            st.rerun()

    # PLAYER CONTROLS (Active if it's Human Turn)
    st.subheader("🎮 Controles do Jogador")
    if not game.hand_ended and game.current_turn == 'human':
        to_call = game.get_to_call('human')
        
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

        # CHECK
        with btn_col1:
            check_disabled = to_call > 0
            if st.button("✋ Checar (Check)", disabled=check_disabled, use_container_width=True):
                game.player_action('human', 'check')
                trigger_ai_turn()
                st.rerun()

        # CALL
        with btn_col2:
            call_disabled = to_call == 0 or game.human_stack == 0
            call_label = f"💰 Pagar {to_call}" if to_call > 0 else "💰 Pagar"
            if st.button(call_label, disabled=call_disabled, type="secondary" if not call_disabled else "default", use_container_width=True):
                game.player_action('human', 'call')
                trigger_ai_turn()
                st.rerun()

        # FOLD
        with btn_col3:
            if st.button("❌ Desistir (Fold)", use_container_width=True):
                game.player_action('human', 'fold')
                st.rerun()

        # RAISE
        with btn_col4:
            min_r = max(game.big_blind, to_call + game.big_blind)
            max_r = game.human_stack - to_call
            if max_r > 0:
                raise_val = st.number_input(
                    "Valor do Aumento (+fichas):",
                    min_value=min_r,
                    max_value=max_r,
                    value=min_r,
                    step=game.big_blind,
                    label_visibility="collapsed"
                )
                if st.button(f"🚀 Aumentar (+{raise_val})", type="primary", use_container_width=True):
                    game.player_action('human', 'raise', raise_amount=raise_val)
                    trigger_ai_turn()
                    st.rerun()
            else:
                st.button("🚀 All-In", disabled=True, use_container_width=True)
    elif not game.hand_ended and game.current_turn == 'ai':
        st.warning("⏳ Aguardando decisão da IA...")

# ==================== COLUMN 2: MENTE DA IA (TELEMETRY DASHBOARD) ====================
with col_mind:
    st.subheader("🧠 Telemetria Mental da IA")
    st.caption("Visualização das métricas probabilísticas em tempo real")

    telemetry = st.session_state.telemetry

    if telemetry is None and not game.hand_ended:
        # Pre-calculate telemetry preview for display if AI hasn't acted yet in this hand
        cost_to_call = game.get_to_call('ai')
        telemetry = ai.decide_action(
            ai_hand=game.ai_hand,
            community_cards=game.community_cards,
            cost_to_call=cost_to_call,
            current_pot=game.pot,
            ai_stack=game.ai_stack,
            human_stack=game.human_stack,
            min_raise=game.big_blind
        )

    if telemetry:
        eq = telemetry['equity']
        po = telemetry['pot_odds']
        blockers = telemetry['blockers_count']

        # EQUITY GAUGE / PROGRESS BAR
        st.markdown(f"#### 📊 Equity (Taxa de Vitória Simulada): `{eq:.2f}%`")
        st.progress(min(1.0, max(0.0, eq / 100.0)))
        
        # Color indicator based on strength
        if eq > 75:
            st.success("🟢 Mão Fortíssima (> 75% Equity)")
        elif eq > 50:
            st.info("🔵 Mão Moderada / Favorecida (> 50% Equity)")
        elif eq >= po:
            st.warning("🟡 Mão Marginal / Viável (Equity >= Pot Odds)")
        else:
            st.error("🔴 Mão Fraca (Equity < Pot Odds)")

        # METRICS CARDS
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric(label="🎯 Pot Odds Necesárias", value=f"{po:.1f}%")
        with m_col2:
            st.metric(label="🃏 Blockers Removidos", value=f"{blockers} cartas")

        st.markdown("---")

        # NATURAL LANGUAGE REASONING LOG
        st.markdown("### 📜 Log de Raciocínio Lógico")
        st.markdown(f'<div class="ai-mind-box">{telemetry["reasoning_log"]}</div>', unsafe_allow_html=True)
    else:
        st.info("Aguardando início das simulações...")

    # GAME HISTORY LOG
    st.markdown("---")
    st.markdown("### 📋 Histórico da Rodada")
    log_box = "\n".join(game.log_history[-10:])
    st.text_area("Log de Ações", value=log_box, height=180, disabled=True)
