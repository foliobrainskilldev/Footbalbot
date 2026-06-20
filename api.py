import os
import json
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")

def fetch_daily_games():
    logger.info("Iniciando BUSCA GLOBAL: Procurando o jogo do Brasil no mundo todo...")

    url = "https://v3.football.api-sports.io/fixtures"
    
    # Busca pela data exata com o fuso do Brasil, ignorando a Liga!
    querystring = {
        "date": "2026-06-19",
        "timezone": "America/Sao_Paulo"
    }
    
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        todos_os_jogos = data.get('response', [])
        logger.info(f"A API encontrou {len(todos_os_jogos)} jogos no mundo todo para esta data.")

        achei = False
        for jogo in todos_os_jogos:
            home = jogo['teams']['home']['name']
            away = jogo['teams']['away']['name']
            liga_nome = jogo['league']['name']
            liga_id = jogo['league']['id']
            
            # Se tiver Brasil ou Haiti, ele apita!
            if "Brazil" in home or "Brazil" in away or "Haiti" in home or "Haiti" in away:
                logger.warning(f"🚨 ACHEI O JOGO!!! 🚨")
                logger.warning(f"⚽ {home} x {away}")
                logger.warning(f"🏆 NOME DA LIGA: {liga_nome}")
                logger.warning(f"👉 ID DA LIGA: {liga_id}  <--- É ESSE NÚMERO QUE PRECISAMOS!")
                achei = True
                
        if not achei:
            logger.error("O jogo não foi encontrado em NENHUMA liga da API nesta data.")
            logger.error("Verifique se o jogo não é dia 20 ou se a API-Football cobre esse campeonato.")
            
        return True

    except Exception as e:
        logger.error(f"Erro ao buscar: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()