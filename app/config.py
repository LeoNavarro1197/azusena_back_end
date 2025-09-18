from dotenv import load_dotenv
import os
import logging

# Cargar las variables del archivo .env
load_dotenv()

class Config:
    # Selección de local o OpenAI
    USE_LOCAL_MODEL = os.getenv('USE_LOCAL_MODEL', 'False').lower() == 'true'
    
    # API Key de OpenAI desde variable de entorno
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'KEY_NO_DEFINIDA')
    
    # Modelo de OpenAI desde variable de entorno
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini-2024-07-18')

    @classmethod
    def validate_config(cls):
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == "KEY_NO_DEFINIDA":
            logging.error("API Key de OpenAI no configurada")
            raise ValueError("API Key de OpenAI no configurada")
        logging.info("Configuración validada correctamente")
