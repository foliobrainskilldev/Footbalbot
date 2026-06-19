import os
import asyncio
import logging
from dotenv import load_dotenv
import pytz
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from api import fetch_daily_games
from analysis import generate_predictions
from bot_logic import start_command, jogos_command, analise_command, send_daily_signals

# Inicialização e Configuração
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # ID do seu Grupo/Canal

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def daily_routine(app: Application):
    """A rotina mestre que roda apenas 1 vez por dia."""
    logger.info("=== INICIANDO ROTINA DIÁRIA 00:00 BRT ===")
    
    # 1. Busca os jogos do dia (Gasta exatamente 1 requisição)
    sucesso_api = fetch_daily_games()
    
    # 2. Processamento e Machine Learning offline
    if sucesso_api or os.path.exists("jogos.json"):
        generate_predictions()
        
    # 3. Disparo Automático para o Telegram
    if TELEGRAM_CHAT_ID:
        await send_daily_signals(app, TELEGRAM_CHAT_ID)
        
    logger.info("=== ROTINA DIÁRIA CONCLUÍDA ===")

def main():
    if not TELEGRAM_TOKEN:
        logger.error("Defina TELEGRAM_TOKEN no arquivo .env")
        return

    # Inicializa o Bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("jogos", jogos_command))
    application.add_handler(CommandHandler("analise", analise_command))

    # Configura Scheduler (Agendamento Automático)
    timezone_brt = pytz.timezone('America/Sao_Paulo')
    scheduler = AsyncIOScheduler(timezone=timezone_brt)
    
    # Programa a execução diária exata às 00:00 do fuso horário de Brasília
    scheduler.add_job(
        daily_routine, 
        trigger='cron', 
        hour=0, 
        minute=0, 
        args=[application]
    )
    scheduler.start()

    logger.info("Bot Iniciado e Scheduler configurado (Aguardando 00:00 BRT).")
    
    # Inicia Polling (Para escutar os comandos /start, /jogos, etc)
    application.run_polling()

if __name__ == "__main__":
    main()