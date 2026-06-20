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

API_KEY = os.getenv("API_FOOTBALL_KEY")
WORLD_CUP_LEAGUE_ID = 1  

def fetch_daily_games():
    logger.info("Iniciando requisição suprema à API-Football (Tabela Completa)...")
    
    # Define o fuso horário do Brasil
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_obj = datetime.now(brt_tz)
    hoje_str = hoje_obj.strftime('%Y-%m-%d')
    temporada = hoje_obj.year

    url = "https://v3.football.api-sports.io/fixtures"
    
    querystring = {
        "league": WORLD_CUP_LEAGUE_ID,
        "season": temporada
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
        
        jogos_de_hoje = []
        todos_os_jogos = data.get('response', [])
        
        for jogo in todos_os_jogos:
            fixture = jogo.get('fixture', {})
            # PEGANDO O RELÓGIO UNIVERSAL (TIMESTAMP) EM VEZ DO TEXTO
            timestamp = fixture.get('timestamp')
            
            if timestamp:
                # CONVERSÃO ABSOLUTA: Converte os segundos para o horário/data real do Brasil
                dt_jogo_brt = datetime.fromtimestamp(timestamp, brt_tz)
                data_do_jogo_brt = dt_jogo_brt.strftime('%Y-%m-%d')
                
                # Agora sim, se a data convertida for dia 19, ele vai salvar!
                if data_do_jogo_brt == hoje_str:
                    jogos_de_hoje.append(jogo)
                
        data['response'] = jogos_de_hoje
        data['results'] = len(jogos_de_hoje)

        with open("jogos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Sucesso absoluto! {data['results']} jogo(s) filtrado(s) perfeitamente para HOJE e salvos.")
        return True

    except Exception as e:
        logger.error(f"Erro ao buscar jogos da API: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()