"""Telegram bot handlers with auth guard."""

import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from .config import BotConfig
from .claude_agent import ClaudeAgent
from .formatters import chunk_message
from .media_handler import (
    download_telegram_photo,
    download_telegram_voice,
    encode_image_to_base64,
    transcribe_audio,
)

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.agent = ClaudeAgent(config)
        self.app = Application.builder().token(config.telegram_bot_token).build()
        self._register_handlers()

    def _is_authorized(self, update: Update) -> bool:
        return update.effective_chat.id == self.config.telegram_owner_id

    async def _unauthorized(self, update: Update) -> None:
        await update.message.reply_text("No autorizado. Este bot es privado.")
        logger.warning(f"Unauthorized access from chat_id={update.effective_chat.id}")

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("reset", self._cmd_reset))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        self.app.add_handler(MessageHandler(filters.VOICE, self._handle_voice))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return await self._unauthorized(update)
        await update.message.reply_text(
            "Hola! Soy tu asistente de Meta Ads.\n\n"
            "Puedes hablarme naturalmente. Por ejemplo:\n"
            "- 'Como van mis campanas esta semana?'\n"
            "- 'Quiero crear una campana de trafico'\n"
            "- 'Dame el rendimiento de los ultimos 30 dias'\n"
            "- 'Lista mis campanas activas'\n\n"
            "Comandos:\n"
            "/reset - Borrar historial de conversacion\n"
            "/help - Ver ayuda\n\n"
            "Todas las campanas se crean en PAUSED por seguridad."
        )

    async def _cmd_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return await self._unauthorized(update)
        self.agent.store.clear(update.effective_chat.id)
        await update.message.reply_text("Historial borrado. Empezamos de nuevo!")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return await self._unauthorized(update)
        await update.message.reply_text(
            "Soy un asistente de Meta Ads con IA.\n\n"
            "Puedo:\n"
            "- Crear campanas, ad sets y anuncios\n"
            "- Consultar metricas de rendimiento\n"
            "- Dar recomendaciones de optimizacion\n"
            "- Sugerir segmentacion y copy\n"
            "- Verificar el estado del token\n\n"
            "Envia una foto para usarla como imagen del anuncio.\n"
            "Todo se crea en PAUSED - te pido confirmacion antes de ejecutar."
        )

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return await self._unauthorized(update)

        chat_id = update.effective_chat.id
        photo = update.message.photo[-1]  # Highest resolution
        temp_path = await download_telegram_photo(photo, context.bot)

        # Keep for ad creation
        self.agent.pending_images[chat_id] = temp_path

        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Build multimodal content blocks so Claude can SEE the image
        image_b64, media_type = encode_image_to_base64(temp_path)
        caption = update.message.caption or ""
        text = (
            f'El usuario envio una imagen con este mensaje: "{caption}". '
            "La imagen tambien se guardo para usar como creativo de anuncio si es necesario. "
            "Analiza la imagen y responde al usuario considerando su mensaje."
            if caption
            else "El usuario envio una imagen. "
            "Esta imagen tambien se guardo para usar como creativo de anuncio si es necesario. "
            "Describe brevemente lo que ves y responde al usuario."
        )

        content_blocks = [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
            {"type": "text", "text": text},
        ]

        try:
            response = await self.agent.process_message(chat_id, content_blocks)
            for chunk in chunk_message(response):
                await update.message.reply_text(chunk)
        except Exception as e:
            logger.exception(f"Error processing photo for chat_id={chat_id}")
            await update.message.reply_text(
                "Imagen recibida y guardada para anuncios, pero no pude analizarla. "
                f"Error: {type(e).__name__}"
            )

    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return await self._unauthorized(update)

        chat_id = update.effective_chat.id
        voice = update.message.voice

        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        temp_path = None
        try:
            temp_path = await download_telegram_voice(voice, context.bot)
            transcription = await transcribe_audio(temp_path, self.config.openai_api_key)

            if not transcription.strip():
                await update.message.reply_text(
                    "No pude entender el audio. Intenta de nuevo o escribe tu mensaje."
                )
                return

            response = await self.agent.process_message(
                chat_id, f"[Mensaje de voz transcrito]: {transcription}"
            )
            for chunk in chunk_message(response):
                await update.message.reply_text(chunk)
        except Exception as e:
            logger.exception(f"Error processing voice for chat_id={chat_id}")
            await update.message.reply_text(
                f"No pude procesar el mensaje de voz. Error: {type(e).__name__}. "
                "Intenta de nuevo o escribe tu mensaje."
            )
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return await self._unauthorized(update)

        chat_id = update.effective_chat.id
        user_text = update.message.text

        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        try:
            response = await self.agent.process_message(chat_id, user_text)
            for chunk in chunk_message(response):
                await update.message.reply_text(chunk)
        except Exception as e:
            logger.exception(f"Error processing message for chat_id={chat_id}")
            await update.message.reply_text(
                f"Error interno: {type(e).__name__}. "
                "Intenta de nuevo o usa /reset para reiniciar."
            )

    def run(self):
        """Start the bot with polling."""
        logger.info("Starting Meta Ads Telegram bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
