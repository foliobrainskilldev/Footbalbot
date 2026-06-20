import os
import json
import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
WORLD_CUP_LEAGUE_ID = 1  

def fetch_daily_games():
    logger.info("Iniciando requisição AUTOMÁTICA diária para a API-Football...")
    
    # Fuso horário do Brasil
    brt_tz = pytz.timezone('America/Sao_Paulo')
    
    # MODO AUTOMÁTICO: Pega sempre a data exata do momento em que rodar
    hoje_str = datetime.now(brt_tz).strftime('%Y-%m-%d')
    temporada = datetime.now(brt_tz).year
    
    url = "https://v3.football.api-sports.io/fixtures"
    
    querystring = {
        "date": hoje_str,
        "timezone": "America/Sao_Paulo",
        "league": WORLD_CUP_LEAGUE_ID,
        "season": temporada
    }
    
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Salva o resultado (mesmo que seja 0, para apagar os jogos do dia anterior)
        with open("jogos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Sucesso! {data.get('results', 0)} jogos salvos no jogos.json para o dia {hoje_str}.")
        return True

    except Exception as e:
        logger.error(f"Erro ao buscar: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()