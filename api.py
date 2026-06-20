import os
import json
import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (API KEY)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações API
API_KEY = os.getenv("API_FOOTBALL_KEY")
# ID 1 geralmente é a Copa do Mundo na API-Football
WORLD_CUP_LEAGUE_ID = 1  

def fetch_daily_games():
    """Busca os jogos do dia atual com exatidão de 1 requisição"""
    logger.info("Iniciando requisição única diária para a API-Football...")
    
    # Horário BRT para buscar o dia correto do Brasil
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(brt_tz).strftime('%Y-%m-%d')
    temporada = datetime.now(brt_tz).year

    url = "https://v3.football.api-sports.io/fixtures"
    querystring = {
        "date": hoje,
        "league": WORLD_CUP_LEAGUE_ID,
        "season": temporada,
        "timezone": "America/Sao_Paulo"
    }

    # CABEÇALHO CORRIGIDO: Enviando apenas a chave oficial direta, sem conflitos!
    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        if not API_KEY:
            logger.error("A CHAVE DA API ESTÁ VAZIA! Verifique seu arquivo .env")
            return False

        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status() # Isso aqui verifica se deu erro 403, 404, etc
        data = response.json()
        
        # Otimização: Salvar bruto apenas para backup em memória local
        with open("jogos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Requisição bem-sucedida. {data.get('results', 0)} jogos encontrados e salvos em jogos.json.")
        return True

    except Exception as e:
        logger.error(f"Erro ao buscar jogos da API: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()