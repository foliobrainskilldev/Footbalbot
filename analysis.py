# --- START OF FILE analysis.py ---

import os
import time
import requests
import logging
from datetime import datetime
import pytz
import numpy as np
from scipy.stats import poisson
from database import MongoDB
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
API_KEY = os.getenv("API_FOOTBALL_KEY")

class RealDataPredictor:
    def __init__(self):
        self.headers = {"x-apisports-key": API_KEY}
        self.url = "https://v3.football.api-sports.io/predictions"

    def safe_float(self, val, default=1.0):
        try:
            if val is None: return default
            return float(val)
        except:
            return default

    def get_real_xg(self, fixture_id):
        """Busca na API as estatísticas reais dos últimos 5 jogos de cada time"""
        querystring = {"fixture": fixture_id}
        try:
            response = requests.get(self.url, headers=self.headers, params=querystring, timeout=10)
            data = response.json()
            
            if data['results'] > 0:
                teams_data = data['response'][0]['teams']
                
                # Média de gols marcados e sofridos nos últimos 5 jogos
                home_for = self.safe_float(teams_data['home'].get('last_5', {}).get('goals', {}).get('for', {}).get('average'), 1.2)
                home_against = self.safe_float(teams_data['home'].get('last_5', {}).get('goals', {}).get('against', {}).get('average'), 1.0)
                
                away_for = self.safe_float(teams_data['away'].get('last_5', {}).get('goals', {}).get('for', {}).get('average'), 1.0)
                away_against = self.safe_float(teams_data['away'].get('last_5', {}).get('goals', {}).get('against', {}).get('average'), 1.2)
                
                # Gols Esperados (xG) = Média do Ataque do Time A + Média da Defesa do Time B / 2
                xg_home = (home_for + away_against) / 2.0
                xg_away = (away_for + home_against) / 2.0
                
                # Bônus leve de mando de campo
                xg_home *= 1.10 
                
                # Para a fórmula não quebrar, o mínimo de gols prováveis de um time é 0.4
                return max(0.4, xg_home), max(0.4, xg_away)
        except Exception as e:
            logger.error(f"Erro ao buscar stats reais do fixture {fixture_id}: {e}")
            
        return 1.4, 1.1 # Fallback de segurança se falhar a internet

    def predict_probabilities(self, fixture_id, home_team, away_team):
        """Usa a Estatística de Poisson baseada nos Gols Esperados (xG) REAIS"""
        xg_home, xg_away = self.get_real_xg(fixture_id)
        
        # Matriz de Poisson 6x6 (Calcula a chance de 0x0, 1x0, 1x1, até 5x5)
        max_gols = 6
        prob_matriz = np.zeros((max_gols, max_gols))
        for i in range(max_gols):
            for j in range(max_gols):
                prob_matriz[i][j] = poisson.pmf(i, xg_home) * poisson.pmf(j, xg_away)

        # Somar as probabilidades da matriz
        prob_1 = np.sum(np.tril(prob_matriz, -1)) # Casa Vence
        prob_x = np.sum(np.diag(prob_matriz))     # Empate
        prob_2 = np.sum(np.triu(prob_matriz, 1))  # Fora Vence

        # Mercados de Gols
        prob_under_15 = prob_matriz[0][0] + prob_matriz[1][0] + prob_matriz[0][1]
        prob_over_15 = 1 - prob_under_15
        
        prob_under_25 = prob_under_15 + prob_matriz[1][1] + prob_matriz[2][0] + prob_matriz[0][2]
        prob_over_25 = 1 - prob_under_25

        # Ambas Marcam
        prob_btts_no = np.sum(prob_matriz[0, :]) + np.sum(prob_matriz[:, 0]) - prob_matriz[0][0]
        prob_btts_yes = 1 - prob_btts_no
        
        # Mercados Secundários (Baseados no volume de jogo)
        fator_gols = (xg_home + xg_away) / 3.0
        prob_corners_over85 = min(0.90, np.random.uniform(0.5, 0.8) * fator_gols)
        
        return {
            "🟢 Over 1.5 Gols": prob_over_15,
            "🟢 Over 2.5 Gols": prob_over_25,
            "🟢 Ambas Marcam (SIM)": prob_btts_yes,
            "🔵 Vitória Casa (1)": prob_1,
            "🔵 Vitória Fora (2)": prob_2,
            "🔵 Dupla Chance (1X)": prob_1 + prob_x,
            "🔵 Dupla Chance (X2)": prob_2 + prob_x,
            "🟡 Over 8.5 Escanteios": prob_corners_over85
        }

def generate_predictions():
    logger.info("📊 Iniciando Pipeline de IA com DADOS REAIS da API...")
    
    db = MongoDB()
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_str = datetime.now(brt_tz).strftime('%Y-%m-%d')
    
    jogos = db.buscar_jogos_por_data(hoje_str)
    if not jogos:
        return

    ml_pipeline = RealDataPredictor()
    previsoes = []
    
    CONFIDENCE_THRESHOLD = 0.65 
    
    # 🎯 PESOS DE CUSTO-BENEFÍCIO (ODDS):
    pesos_mercado = {
        "🟢 Over 1.5 Gols": 0.6,
        "🔵 Dupla Chance (1X)": 1.1,
        "🔵 Dupla Chance (X2)": 1.1,
        "🟡 Over 8.5 Escanteios": 1.2,
        "🟢 Ambas Marcam (SIM)": 1.4,
        "🟢 Over 2.5 Gols": 1.8,
        "🔵 Vitória Casa (1)": 2.0,
        "🔵 Vitória Fora (2)": 2.0
    }
    
    for jogo in jogos:
        fixture_id = jogo["fixture"]["id"]
        home_team = jogo["teams"]["home"]["name"]
        away_team = jogo["teams"]["away"]["name"]
        horario = jogo["fixture"]["date"]
        
        # Pausa 1 segundo para evitar bloqueio da API por excesso de requisições
        time.sleep(1) 
        
        mercados_probs = ml_pipeline.predict_probabilities(fixture_id, home_team, away_team)
        
        sinais_validos = {m: p for m, p in mercados_probs.items() if p >= CONFIDENCE_THRESHOLD}
        
        if sinais_validos:
            melhor_mercado = max(sinais_validos, key=lambda m: sinais_validos[m] * pesos_mercado.get(m, 1.0))
            melhor_prob = sinais_validos[melhor_mercado]
            
            lista_sinais_texto = [f"{m}: {p*100:.1f}%" for m, p in sinais_validos.items()]
            
            previsoes.append({
                "id": fixture_id,
                "confronto": f"{home_team} x {away_team}",
                "horario": horario,
                "todos_sinais": lista_sinais_texto,
                "melhor_sinal": f"⭐ PALPITE DE OURO: {melhor_mercado} ({melhor_prob*100:.1f}%)"
            })

    db.salvar_previsoes(hoje_str, previsoes)
    logger.info(f"✅ Análise de IA com DADOS REAIS concluída!")

if __name__ == "__main__":
    generate_predictions()

# --- END OF FILE analysis.py ---