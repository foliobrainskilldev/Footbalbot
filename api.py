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
    logger.info("Iniciando requisição AUTOMÁTICA GLOBLAL diária...")
    
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_str = datetime.now(brt_tz).strftime('%Y-%m-%d')
    
    url = "https://v3.football.api-sports.io/fixtures"
    
    # BUSCA GLOBAL: Pede TODOS os jogos do mundo hoje
    # Burlamos o erro de "Season" da API pedindo apenas a data.
    querystring = {
        "date": hoje_str,
        "timezone": "America/Sao_Paulo"
    }
    
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        todos_os_jogos = data.get('response', [])
        
        # FILTRO LOCAL: Separamos APENAS os jogos da Copa do Mundo (ID 1)
        jogos_copa = []
        for jogo in todos_os_jogos:
            if jogo.get('league', {}).get('id') == WORLD_CUP_LEAGUE_ID:
                jogos_copa.append(jogo)
                
        # Atualiza o JSON apenas com os jogos da Copa de hoje
        data['response'] = jogos_copa
        data['results'] = len(jogos_copa)
        
        with open("jogos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Sucesso! Encontrados {len(todos_os_jogos)} jogos no mundo. {data['results']} são da Copa do Mundo para HOJE ({hoje_str}).")
        return True

    except Exception as e:
        logger.error(f"Erro ao buscar: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()