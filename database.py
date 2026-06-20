import os
import logging
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("A variável de ambiente MONGO_URI não foi definida no arquivo .env")
        
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client["copa_bot_db"]
            self.jogos_col = self.db["jogos"]
            self.previsoes_col = self.db["previsoes"]
            logger.info("✅ Conexão com MongoDB Atlas estabelecida com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar no MongoDB Atlas: {e}")
            raise

    def salvar_jogos(self, data_hoje, jogos_limpos):
        """Salva os jogos limpos no banco usando UPSERT (evita duplicatas)."""
        if not jogos_limpos:
            logger.warning("Nenhum jogo para salvar no banco de dados hoje.")
            return 0

        operacoes = []
        for jogo in jogos_limpos:
            # Usamos o fixture.id como identificador único
            operacoes.append(
                UpdateOne(
                    {"fixture_id": jogo["fixture"]["id"]}, 
                    {"$set": {"data_ref": data_hoje, "detalhes": jogo}}, 
                    upsert=True
                )
            )
            
        if operacoes:
            resultado = self.jogos_col.bulk_write(operacoes)
            logger.info(f"💾 {resultado.upserted_count} novos jogos inseridos e {resultado.modified_count} atualizados no MongoDB.")
            return len(operacoes)
        return 0

    def buscar_jogos_por_data(self, data_hoje):
        """Busca os jogos salvos para uma data específica."""
        jogos = list(self.jogos_col.find({"data_ref": data_hoje}))
        return [j["detalhes"] for j in jogos]

    def salvar_previsoes(self, data_hoje, previsoes):
        """Salva as predições geradas pelo modelo de ML."""
        if not previsoes:
            return
            
        operacoes = []
        for prev in previsoes:
            operacoes.append(
                UpdateOne(
                    {"fixture_id": prev["id"]}, 
                    {"$set": {"data_ref": data_hoje, **prev}}, 
                    upsert=True
                )
            )
            
        if operacoes:
            self.previsoes_col.bulk_write(operacoes)
            logger.info("📊 Previsões salvas com sucesso no MongoDB!")

    def buscar_previsoes_por_data(self, data_hoje):
        """Busca previsões geradas para a data."""
        return list(self.previsoes_col.find({"data_ref": data_hoje}, {"_id": 0}))