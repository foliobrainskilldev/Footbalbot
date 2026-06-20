import json
import logging
import os
import joblib
import numpy as np
from scipy.stats import poisson

logger = logging.getLogger(__name__)

def prever_poisson(lambda_home, lambda_away):
    """Calcula as probabilidades usando a Distribuição de Poisson"""
    max_gols = 6
    prob_matriz = np.zeros((max_gols, max_gols))
    
    for i in range(max_gols):
        for j in range(max_gols):
            prob_matriz[i][j] = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
            
    prob_home_win = np.sum(np.tril(prob_matriz, -1))
    prob_draw = np.sum(np.diag(prob_matriz))
    prob_away_win = np.sum(np.triu(prob_matriz, 1))
    
    prob_under_25 = prob_matriz[0][0] + prob_matriz[0][1] + prob_matriz[1][0] + prob_matriz[1][1] + prob_matriz[2][0] + prob_matriz[0][2]
    prob_over_25 = 1 - prob_under_25
    
    prob_btts_no = np.sum(prob_matriz[0, :]) + np.sum(prob_matriz[:, 0]) - prob_matriz[0, 0]
    prob_btts_yes = 1 - prob_btts_no
    
    return prob_home_win, prob_draw, prob_away_win, prob_over_25, prob_btts_yes

def generate_predictions():
    logger.info("Iniciando pipeline de processamento e predição...")
    
    if not os.path.exists("jogos.json"):
        logger.error("Arquivo jogos.json não encontrado.")
        return

    with open("jogos.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    jogos = data.get("response", [])
    previsoes = []
    
    for jogo in jogos:
        fixture_id = jogo["fixture"]["id"]
        home_team = jogo["teams"]["home"]["name"]
        away_team = jogo["teams"]["away"]["name"]
        
        # Simulando uma equipe forte jogando em casa e equipe variada fora
        lambda_home = np.random.uniform(1.5, 2.8) 
        lambda_away = np.random.uniform(0.8, 1.9)
        
        p_home, p_draw, p_away, p_over25, p_btts = prever_poisson(lambda_home, lambda_away)

        # BAIXAMOS A RÉGUA PARA 50% (> 0.50) PARA VOCÊ VER OS SINAIS!
        sinais = []
        if p_over25 > 0.50:
            sinais.append(f"✅ OVER 2.5 Gols ({p_over25*100:.1f}%)")
        if p_btts > 0.50:
            sinais.append(f"✅ Ambas Marcam - SIM ({p_btts*100:.1f}%)")
        if p_home > 0.50:
            sinais.append(f"✅ Vitória {home_team} ({p_home*100:.1f}%)")
        elif p_away > 0.50:
            sinais.append(f"✅ Vitória {away_team} ({p_away*100:.1f}%)")

        if sinais:
            previsoes.append({
                "id": fixture_id,
                "confronto": f"{home_team} x {away_team}",
                "horario": jogo["fixture"]["date"],
                "sinais": sinais
            })

    with open("previsoes.json", "w", encoding="utf-8") as f:
        json.dump(previsoes, f, ensure_ascii=False, indent=4)
        
    logger.info(f"Análise concluída. {len(previsoes)} jogos geraram sinais acima de 50%.")

if __name__ == "__main__":
    generate_predictions()