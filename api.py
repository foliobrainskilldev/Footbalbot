import os
import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
from database import MongoDB

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
WORLD_CUP_LEAGUE_ID = 1  # ID Restrito apenas para a Copa do Mundo

def clean_fixture_data(jogos_raw):
    """🧹 Pipeline de Limpeza de Dados: Remove jogos cancelados, adiados ou com dados inconsistentes."""
    jogos_limpos = []
    
    for jogo in jogos_raw:
        try:
            # Verifica integridade dos dados básicos
            fixture = jogo.get("fixture", {})
            teams = jogo.get("teams", {})
            
            if not fixture.get("id") or not fixture.get("date"):
                continue
                
            if not teams.get("home", {}).get("name") or not teams.get("away", {}).get("name"):
                continue
                
            # Ignora jogos com status de Cancelado (CANC), Adiado (PST) ou Abandonado (ABD)
            status_short = fixture.get("status", {}).get("short")
            if status_short in ["CANC", "PST", "ABD"]:
                continue
                
            jogos_limpos.append(jogo)
            
        except Exception as e:
            logger.warning(f"Erro ao limpar dados de um jogo, ignorando... {e}")
            continue
            
    return jogos_limpos

def fetch_daily_games():
    """📡 Pipeline de Coleta: Baixa da API, filtra, limpa e envia pro BD."""
    logger.info("Iniciando Pipeline de Dados Diário...")
    
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_str = datetime.now(brt_tz).strftime('%Y-%m-%d')
    
    url = "https://v3.football.api-sports.io/fixtures"
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
        
        # Filtro Local: APENAS Copa do Mundo
        jogos_copa = [j for j in todos_os_jogos if j.get('league', {}).get('id') == WORLD_CUP_LEAGUE_ID]
        
        logger.info(f"Encontrados {len(jogos_copa)} jogos brutos da Copa do Mundo.")
        
        # Limpeza de Dados
        jogos_limpos = clean_fixture_data(jogos_copa)
        logger.info(f"Restaram {len(jogos_limpos)} jogos após limpeza de inconsistências.")
        
        # Salva no Banco de Dados MongoDB
        db = MongoDB()
        db.salvar_jogos(hoje_str, jogos_limpos)
        
        return True

    except Exception as e:
        logger.error(f"Erro no pipeline de coleta: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()