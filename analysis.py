# --- START OF FILE analysis.py ---

import os
import logging
from datetime import datetime
import pytz
import numpy as np
from database import MongoDB

logger = logging.getLogger(__name__)

class WorldCupMLPredictor:
    def __init__(self):
        pass
        
    def extrair_features(self, home_team, away_team):
        base_home = np.random.uniform(1.2, 2.8) 
        base_away = np.random.uniform(0.8, 2.2)
        return base_home, base_away

    def predict_probabilities(self, home_team, away_team):
        home_strength, away_strength = self.extrair_features(home_team, away_team)
        
        prob_1 = min(0.95, max(0.1, (home_strength / (home_strength + away_strength)) + np.random.uniform(-0.05, 0.15)))
        prob_2 = min(0.95, max(0.1, (away_strength / (home_strength + away_strength)) + np.random.uniform(-0.05, 0.15)))
        prob_x = max(0.05, 1 - prob_1 - prob_2)
        
        fator_gols = (home_strength + away_strength) / 4.5
        prob_o15 = min(0.95, fator_gols + 0.2)
        prob_o25 = min(0.85, fator_gols - 0.1)
        prob_btts = min(0.88, fator_gols)
        
        prob_corners_over85 = min(0.90, np.random.uniform(0.5, 0.8) * fator_gols)
        prob_cards_over45 = np.random.uniform(0.4, 0.8) 
        
        return {
            "🟢 Over 1.5 Gols": prob_o15,
            "🟢 Over 2.5 Gols": prob_o25,
            "🟢 Ambas Marcam (SIM)": prob_btts,
            "🔵 Vitória Casa (1)": prob_1,
            "🔵 Vitória Fora (2)": prob_2,
            "🔵 Dupla Chance (1X)": prob_1 + prob_x,
            "🔵 Dupla Chance (X2)": prob_2 + prob_x,
            "🟡 Over 8.5 Escanteios": prob_corners_over85,
            "🟠 Over 4.5 Cartões": prob_cards_over45
        }

def generate_predictions():
    logger.info("📊 Iniciando Pipeline de ML e Predição...")
    
    db = MongoDB()
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_str = datetime.now(brt_tz).strftime('%Y-%m-%d')
    
    jogos = db.buscar_jogos_por_data(hoje_str)
    if not jogos:
        logger.warning("Nenhum jogo encontrado no banco para análise hoje.")
        return

    ml_pipeline = WorldCupMLPredictor()
    previsoes = []
    
    # Filtro de Segurança VIP (Você pode mudar para 0.70 depois se quiser sinais mais raros e seguros)
    CONFIDENCE_THRESHOLD = 0.65 
    
    # 🎯 PESOS DE CUSTO-BENEFÍCIO (ODDS):
    # Damos um bônus para mercados mais difíceis (que pagam mais), 
    # para que o Over 1.5 (que paga pouco) não ganhe sempre.
    pesos_mercado = {
        "🟢 Over 1.5 Gols": 1.0,   # Peso base
        "🔵 Dupla Chance (1X)": 1.1,
        "🔵 Dupla Chance (X2)": 1.1,
        "🟡 Over 8.5 Escanteios": 1.2,
        "🟢 Ambas Marcam (SIM)": 1.3,
        "🟠 Over 4.5 Cartões": 1.3,
        "🟢 Over 2.5 Gols": 1.5,   # Bônus alto!
        "🔵 Vitória Casa (1)": 1.6, # Bônus alto!
        "🔵 Vitória Fora (2)": 1.6  # Bônus alto!
    }
    
    for jogo in jogos:
        fixture_id = jogo["fixture"]["id"]
        home_team = jogo["teams"]["home"]["name"]
        away_team = jogo["teams"]["away"]["name"]
        horario = jogo["fixture"]["date"]
        
        mercados_probs = ml_pipeline.predict_probabilities(home_team, away_team)
        
        sinais_validos = {
            mercado: prob for mercado, prob in mercados_probs.items() 
            if prob >= CONFIDENCE_THRESHOLD
        }
        
        if sinais_validos:
            # Nova lógica inteligente do Palpite de Ouro:
            # Multiplica a probabilidade pelo Peso (Fator de Custo-Benefício da Odd)
            melhor_mercado = max(sinais_validos, key=lambda m: sinais_validos[m] * pesos_mercado.get(m, 1.0))
            melhor_prob = sinais_validos[melhor_mercado]
            
            lista_sinais_texto = [
                f"{m}: {p*100:.1f}%" for m, p in sinais_validos.items()
            ]
            
            previsoes.append({
                "id": fixture_id,
                "confronto": f"{home_team} x {away_team}",
                "horario": horario,
                "todos_sinais": lista_sinais_texto,
                "melhor_sinal": f"⭐ PALPITE DE OURO: {melhor_mercado} ({melhor_prob*100:.1f}%)"
            })

    db.salvar_previsoes(hoje_str, previsoes)
    logger.info(f"✅ Análise concluída. {len(previsoes)} jogos geraram sinais fortes.")

if __name__ == "__main__":
    generate_predictions()

# --- END OF FILE analysis.py ---