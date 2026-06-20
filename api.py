import os
import json
import requests
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (API KEY)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
WORLD_CUP_LEAGUE_ID = 1  

def fetch_daily_games():
    logger.info("Iniciando requisição à API-Football com busca inteligente...")
    
    # Define o fuso horário do Brasil
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_obj = datetime.now(brt_tz)
    
    hoje_str = hoje_obj.strftime('%Y-%m-%d')
    amanha_str = (hoje_obj + timedelta(days=1)).strftime('%Y-%m-%d')
    temporada = hoje_obj.year

    url = "https://v3.football.api-sports.io/fixtures"
    
    # BUSCA INTELIGENTE: Pede 2 dias para não perder os jogos da madrugada no servidor deles
    querystring = {
        "league": WORLD_CUP_LEAGUE_ID,
        "season": temporada,
        "from": hoje_str,
        "to": amanha_str,
        "timezone": "America/Sao_Paulo"
    }

    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        if not API_KEY:
            logger.error("A CHAVE DA API ESTÁ VAZIA!")
            return False

        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # FILTRO INTELIGENTE: Pega os 2 dias da API, mas salva SÓ os que caem "hoje" no horário BRT
        jogos_de_hoje = []
        for jogo in data.get('response', []):
            # A API devolve algo como "2026-06-19T21:30:00-03:00". Pegamos só os 10 primeiros caracteres (A data)
            data_do_jogo_brt = jogo['fixture']['date'][:10]
            
            if data_do_jogo_brt == hoje_str:
                jogos_de_hoje.append(jogo)
                
        # Substitui os resultados da API apenas pela lista filtrada de hoje
        data['response'] = jogos_de_hoje
        data['results'] = len(jogos_de_hoje)

        with open("jogos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Sucesso! {data['results']} jogo(s) filtrado(s) perfeitamente para HOJE e salvos.")
        return True

    except Exception as e:
        logger.error(f"Erro ao buscar jogos da API: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()