import os
import logging
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import MongoDB

logger = logging.getLogger(__name__)

def get_hoje_str():
    brt_tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(brt_tz).strftime('%Y-%m-%d')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 *Bot Analista Avançado - Copa do Mundo*\n\n"
        "Comandos disponíveis:\n"
        "/jogos - Ver jogos diários salvos no banco de dados\n"
        "/analise - Ver as predições de IA de hoje"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def jogos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = MongoDB()
    hoje_str = get_hoje_str()
    jogos = db.buscar_jogos_por_data(hoje_str)
        
    if not jogos:
        await update.message.reply_text("Hoje não temos jogos da Copa do Mundo registrados no banco.")
        return
        
    res = f"📅 *Jogos de Hoje - Copa do Mundo ({hoje_str}):*\n\n"
    for j in jogos:
        home = j["teams"]["home"]["name"]
        away = j["teams"]["away"]["name"]
        hora = j["fixture"]["date"][11:16]
        res += f"⚽ {home} x {away} ⏰ {hora}\n"
        
    await update.message.reply_text(res, parse_mode="Markdown")

async def analise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = MongoDB()
    hoje_str = get_hoje_str()
    previsoes = db.buscar_previsoes_por_data(hoje_str)
        
    if not previsoes:
        await update.message.reply_text("Nenhuma oportunidade com confiança acima de 65% para hoje.")
        return
        
    for p in previsoes:
        msg = f"🏆 *{p['confronto']}*\n"
        msg += f"⏰ {p['horario'][11:16]}\n\n"
        
        msg += "*🔥 Sinais Encontrados (> 65%):*\n"
        for sinal in p['todos_sinais']:
            msg += f"👉 {sinal}\n"
            
        msg += f"\n{p['melhor_sinal']}\n"
            
        # Botão afiliado
        keyboard = [[InlineKeyboardButton("🎮 Fazer Entrada (Link Seguro)", url="https://lkmn.cc/2024cb")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def send_daily_signals(app, chat_id):
    """Envia sinais automaticamente para o grupo/canal."""
    logger.info("Enviando sinais diários automatizados para o Telegram.")
    
    db = MongoDB()
    hoje_str = get_hoje_str()
    previsoes = db.buscar_previsoes_por_data(hoje_str)
        
    if not previsoes:
        await app.bot.send_message(chat_id=chat_id, text="⚠️ A IA não encontrou padrões seguros (> 65%) nos jogos de hoje.")
        return

    for p in previsoes:
        msg = f"🏆 *SINAL VIP IA - COPA DO MUNDO*\n\n"
        msg += f"⚽ *{p['confronto']}*\n\n"
        
        msg += "*Mercados Aprovados:*\n"
        for sinal in p['todos_sinais']:
            msg += f"✅ {sinal}\n"
            
        msg += f"\n🎯 *MELHOR OPÇÃO:*\n{p['melhor_sinal']}\n"
            
        keyboard = [[InlineKeyboardButton("💰 Fazer essa Entrada Agora!", url="https://lkmn.cc/2024cb")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=reply_markup)