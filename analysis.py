import os
import logging
from datetime import datetime
import pytz
import numpy as np
from database import MongoDB

logger = logging.getLogger(__name__)

class WorldCupMLPredictor:
    """
    Classe que representa o Pipeline de Machine Learning.
    Em um cenário real, carregaríamos modelos joblib (Scikit-Learn / XGBoost) aqui.
    """
    def __init__(self):
        # Aqui você carregaria seus modelos (.pkl) treinados com dados históricos
        # self.modelo_gols = joblib.load('models/xgb_gols_v1.pkl')
        # self.modelo_cantos = joblib.load('models/rf_corners_v1.pkl')
        pass
        
    def extrair_features(self, home_team, away_team):
        """Transforma dados brutos do jogo em features numéricas para o Modelo."""
        # Simulação de geração de features estatísticas de força das seleções
        base_home = np.random.uniform(1.2, 2.5) 
        base_away = np.random.uniform(0.8, 2.0)
        return base_home, base_away

    def predict_probabilities(self, home_team, away_team):
        """🤖 Roda as features pelos modelos e retorna % de múltiplos mercados."""
        home_strength, away_strength = self.extrair_features(home_team, away_team)
        
        # Simulação de saídas do predict_proba() dos algoritmos de ML
        # Mercados 1X2 e Dupla Chance
        prob_1 = min(0.95, max(0.1, (home_strength / (home_strength + away_strength)) + np.random.uniform(-0.1, 0.1)))
        prob_2 = min(0.95, max(0.1, (away_strength / (home_strength + away_strength)) + np.random.uniform(-0.1, 0.1)))
        prob_x = max(0.05, 1 - prob_1 - prob_2)
        
        # Mercados de Gols (Over 1.5, Over 2.5, BTTS)
        fator_gols = (home_strength + away_strength) / 4.5
        prob_o15 = min(0.92, fator_gols + 0.2)
        prob_o25 = min(0.85, fator_gols - 0.15)
        prob_btts = min(0.88, fator_gols - 0.05)
        
        # Mercados Secundários (Escanteios e Cartões)
        # Jogos com seleções fortes costumam ter mais ataques (Cantos) e mais intensidade (Cartões)
        prob_corners_over85 = min(0.90, np.random.uniform(0.4, 0.8) * fator_gols)
        prob_cards_over45 = np.random.uniform(0.3, 0.75) 
        
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
    
    # 📩 Limite Dinâmico de Confiança (Sinais apenas acima de 65% a 70%)
    CONFIDENCE_THRESHOLD = 0.65 
    
    for jogo in jogos:
        fixture_id = jogo["fixture"]["id"]
        home_team = jogo["teams"]["home"]["name"]
        away_team = jogo["teams"]["away"]["name"]
        horario = jogo["fixture"]["date"]
        
        # Passa pelo modelo
        mercados_probs = ml_pipeline.predict_probabilities(home_team, away_team)
        
        # Filtra os que passaram na régua dinâmica
        sinais_validos = {
            mercado: prob for mercado, prob in mercados_probs.items() 
            if prob >= CONFIDENCE_THRESHOLD
        }
        
        if sinais_validos:
            # 🎯 Lógica para ESCOLHER O MELHOR palpite (Maior probabilidade)
            melhor_mercado = max(sinais_validos, key=sinais_validos.get)
            melhor_prob = sinais_validos[melhor_mercado]
            
            # Formata lista de todos os palpites aprovados pelo ML para enviar no relatório
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

    # Salva predições finais no MongoDB
    db.salvar_previsoes(hoje_str, previsoes)
    logger.info(f"✅ Análise concluída. {len(previsoes)} jogos geraram sinais fortes.")

if __name__ == "__main__":
    generate_predictions()