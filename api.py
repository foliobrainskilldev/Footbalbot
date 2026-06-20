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
# Talvez o jogo não esteja na liga 1. Mas vamos buscar na 1 primeiro para ver!
WORLD_CUP_LEAGUE_ID = 1  

def fetch_daily_games():
    logger.info("Iniciando MODO RAIO-X: Lendo tudo o que a API tem...")
    
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_obj = datetime.now(brt_tz)
    hoje_str = hoje_obj.strftime('%Y-%m-%d')
    temporada = hoje_obj.year

    url = "https://v3.football.api-sports.io/fixtures"
    querystring = {
        "league": WORLD_CUP_LEAGUE_ID,
        "season": temporada
    }
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        todos_os_jogos = data.get('response', [])
        logger.info(f"A API devolveu um total de {len(todos_os_jogos)} jogos no banco de dados para esta liga/temporada.")

        # Salva TUDO bruto num arquivo de debug para podermos ler depois
        with open("debug_tabela_completa.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        jogos_de_hoje = []
        
        logger.info(f"Procurando jogos para a data de hoje no Brasil: {hoje_str}")
        
        for jogo in todos_os_jogos:
            fixture = jogo.get('fixture', {})
            timestamp = fixture.get('timestamp')
            home = jogo['teams']['home']['name']
            away = jogo['teams']['away']['name']
            
            if timestamp:
                dt_jogo_brt = datetime.fromtimestamp(timestamp, brt_tz)
                data_do_jogo_brt = dt_jogo_brt.strftime('%Y-%m-%d')
                hora_do_jogo_brt = dt_jogo_brt.strftime('%H:%M')
                
                # Se for um jogo do Brasil, vamos imprimir na tela para ver onde a API enfiou ele!
                if "Brazil" in home or "Brazil" in away or "Haiti" in home or "Haiti" in away:
                    logger.warning(f"🚨 ACHEI O JOGO NA API: {home} x {away} | Cadastrado lá no dia: {data_do_jogo_brt} às {hora_do_jogo_brt} BRT")

                if data_do_jogo_brt == hoje_str:
                    jogos_de_hoje.append(jogo)
                
        data['response'] = jogos_de_hoje
        data['results'] = len(jogos_de_hoje)

        with open("jogos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Filtragem concluída! {data['results']} jogos salvos para hoje.")
        return True

    except Exception as e:
        logger.error(f"Erro ao buscar: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()