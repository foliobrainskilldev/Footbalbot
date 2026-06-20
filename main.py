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
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def daily_routine(app: Application):
    """Pipeline mestre diário: API -> MongoDB -> ML -> Telegram."""
    logger.info("=== INICIANDO PIPELINE DIÁRIO 00:00 BRT ===")
    
    # 1. Coleta, limpa os dados da API e salva no MongoDB
    sucesso_api = fetch_daily_games()
    
    # 2. IA lê do banco, gera predições de vários mercados e salva os sinais
    generate_predictions()
        
    # 3. Disparo Automático para o Telegram
    if TELEGRAM_CHAT_ID:
        await send_daily_signals(app, TELEGRAM_CHAT_ID)
        
    logger.info("=== PIPELINE DIÁRIO CONCLUÍDO ===")

def main():
    if not TELEGRAM_TOKEN:
        logger.error("Defina TELEGRAM_TOKEN no arquivo .env")
        return

    # Inicializa o Bot do Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("jogos", jogos_command))
    application.add_handler(CommandHandler("analise", analise_command))

    # Configura Scheduler (Agendamento Automático de Cron Job)
    timezone_brt = pytz.timezone('America/Sao_Paulo')
    scheduler = AsyncIOScheduler(timezone=timezone_brt)
    
    scheduler.add_job(
        daily_routine, 
        trigger='cron', 
        hour=0, 
        minute=0, 
        args=[application]
    )
    scheduler.start()

    logger.info("Bot Iniciado! Aguardando comandos ou rotina da 00:00 BRT.")
    application.run_polling()

if __name__ == "__main__":
    main()