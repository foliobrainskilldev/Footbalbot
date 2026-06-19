import json
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 *Bot Analista Copa do Mundo*\n\n"
        "Comandos disponíveis:\n"
        "/jogos - Ver jogos guardados para hoje\n"
        "/analise - Ver as predições de hoje"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def jogos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists("jogos.json"):
        await update.message.reply_text("Nenhum jogo no banco de dados hoje.")
        return
        
    with open("jogos.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    jogos = data.get("response", [])
    if not jogos:
        await update.message.reply_text("Hoje não temos jogos da Copa do Mundo registrados.")
        return
        
    res = "📅 *Jogos de Hoje (Copa do Mundo):*\n\n"
    for j in jogos:
        home = j["teams"]["home"]["name"]
        away = j["teams"]["away"]["name"]
        hora = j["fixture"]["date"][11:16]
        res += f"⚽ {home} x {away} ⏰ {hora}\n"
        
    await update.message.reply_text(res, parse_mode="Markdown")

async def analise_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists("previsoes.json"):
        await update.message.reply_text("A análise de hoje ainda não foi processada.")
        return
        
    with open("previsoes.json", "r", encoding="utf-8") as f:
        previsoes = json.load(f)
        
    if not previsoes:
        await update.message.reply_text("Nenhum sinal com mais de 70% de confiança para hoje.")
        return
        
    for p in previsoes:
        msg = f"🏆 *{p['confronto']}*\n"
        msg += f"⏰ {p['horario'][11:16]}\n\n"
        msg += "*🔥 SINAIS GERADOS:*\n"
        for sinal in p['sinais']:
            msg += f"{sinal}\n"
            
        # Botão afiliado
        keyboard = [[InlineKeyboardButton("🎮 Onde eu jogo (Link Seguro)", url="https://lkmn.cc/2024cb")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def send_daily_signals(app, chat_id):
    """Envia sinais automaticamente para o grupo/canal."""
    logger.info("Enviando sinais diários automatizados para o Telegram.")
    
    if not os.path.exists("previsoes.json"):
        return
        
    with open("previsoes.json", "r", encoding="utf-8") as f:
        previsoes = json.load(f)
        
    if not previsoes:
        await app.bot.send_message(chat_id=chat_id, text="⚠️ Sem padrões claros (>70%) nos jogos de hoje.")
        return

    for p in previsoes:
        msg = f"🏆 *SINAL VIP COPA DO MUNDO*\n\n"
        msg += f"⚽ *{p['confronto']}*\n\n"
        msg += "*Recomendações:*\n"
        for sinal in p['sinais']:
            msg += f"👉 {sinal}\n"
            
        # Botão afiliado obrigatório
        keyboard = [[InlineKeyboardButton("💰 Onde eu jogo e faço as entradas", url="https://lkmn.cc/2024cb")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=reply_markup)