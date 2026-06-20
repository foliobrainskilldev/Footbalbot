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
    
    # ESTRATÉGIA MESTRA: Pedimos TODOS os jogos da Copa do Mundo (1 única requisição)
    # Isso burla o bug de UTC do servidor da API-Football
    querystring = {
        "league": WORLD_CUP_LEAGUE_ID,
        "season": temporada,
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
        
        # FILTRO LOCAL: O próprio Python separa apenas os jogos de "hoje" no Brasil
        jogos_de_hoje = []
        todos_os_jogos = data.get('response', [])
        
        for jogo in todos_os_jogos:
            # Evita erros caso algum jogo da tabela ainda esteja sem data definida (TBD)
            fixture = jogo.get('fixture', {})
            data_str = fixture.get('date', '')
            
            # Pega os 10 primeiros caracteres do horário BRT (Ex: "2026-06-19")
            if len(data_str) >= 10:
                data_do_jogo_brt = data_str[:10]
                
                if data_do_jogo_brt == hoje_str:
                    jogos_de_hoje.append(jogo)
                
        # Substitui a lista gigante de 104 jogos apenas pelos de hoje
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