import os
import json
import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações da API
API_KEY = os.getenv("API_FOOTBALL_KEY")
WORLD_CUP_LEAGUE_ID = 1  # ID fixo da Copa do Mundo na API-Football

def fetch_daily_games():
    logger.info("Iniciando MODO RAIO-X: Conectando à API-Football...")
    
    if not API_KEY:
        logger.error("Chave de API (API_FOOTBALL_KEY) não encontrada no ambiente!")
        return False

    # Define o fuso horário brasileiro
    brt_tz = pytz.timezone('America/Sao_Paulo')
    hoje_obj = datetime.now(brt_tz)
    
    # Formata a data atual em YYYY-MM-DD
    hoje_str = hoje_obj.strftime('%Y-%m-%d')
    
    # Força a temporada para 2026, ano em que a Copa do Mundo acontece
    temporada = 2026 

    url = "https://api-sports.io"
    
    # Enviando o parâmetro 'date' diretamente para a API otimizar a busca
    querystring = {
        "league": WORLD_CUP_LEAGUE_ID,
        "season": temporada,
        "date": hoje_str
    }
    
    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        logger.info(f"Buscando jogos da Copa do Mundo programados para hoje ({hoje_str}) no fuso do Brasil...")
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Verifica se a API retornou erros internos de validação ou de chave
        if data.get('errors'):
            logger.error(f"A API retornou um erro: {data['errors']}")
            return False

        todos_os_jogos = data.get('response', [])
        logger.info(f"A API retornou {len(todos_os_jogos)} jogos para a data de hoje.")

        # Salva o arquivo bruto de depuração com o resultado exato obtido
        with open("debug_tabela_completa.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        jogos_filtrados = []
        
        for jogo in todos_os_jogos:
            fixture = jogo.get('fixture', {})
            timestamp = fixture.get('timestamp')
            home = jogo.get('teams', {}).get('home', {}).get('name', 'Desconhecido')
            away = jogo.get('teams', {}).get('away', {}).get('name', 'Desconhecido')
            
            if timestamp:
                # Converte o timestamp UTC do jogo para o horário de Brasília
                dt_jogo_brt = datetime.fromtimestamp(timestamp, brt_tz)
                hora_do_jogo_brt = dt_jogo_brt.strftime('%H:%M')
                
                # Alerta visual no terminal caso encontre jogos de seleções específicas para testes
                if any(pais in [home, away] for pais in ["Brazil", "Haiti", "Argentina", "France"]):
                    logger.warning(f"🚨 JOGO EM DESTAQUE ENCONTRADO: {home} x {away} às {hora_do_jogo_brt} BRT")
                
                jogos_filtrados.append(jogo)
                
        # Atualiza o dicionário final para salvar apenas os confrontos validados
        data['response'] = jogos_filtrados
        data['results'] = len(jogos_filtrados)

        # Salva o resultado final pronto para ser consumido pela sua aplicação
        with open("jogos.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Processo concluído! {data['results']} jogos salvos em 'jogos.json'.")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição HTTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado durante o processamento: {e}")
        return False

if __name__ == "__main__":
    fetch_daily_games()
