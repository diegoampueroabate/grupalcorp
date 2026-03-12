"""Claude API orchestrator with tool use loop for Meta Ads conversations."""

import logging

import anthropic

from .config import BotConfig
from .conversation_store import ConversationStore
from .tool_definitions import TOOL_DEFINITIONS
from .tool_executor import execute_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Eres un asistente experto en Meta Ads (Facebook/Instagram) que habla espanol.
Tu trabajo es ayudar al usuario a crear, gestionar y optimizar campanas publicitarias
a traves de Telegram.

REGLAS DE SEGURIDAD CRITICAS (NUNCA VIOLAR):
1. SIEMPRE crea campanas, ad sets y ads con status PAUSED - NUNCA ACTIVE al crear
2. SIEMPRE muestra un resumen completo y pide confirmacion EXPLICITA antes de ejecutar cualquier herramienta de creacion
3. NUNCA establezcas un presupuesto diario superior a $100 sin confirmacion explicita del usuario indicando el monto exacto
4. Los valores de presupuesto se especifican en CENTAVOS: $50.00 = 5000, $10.00 = 1000
5. Si una operacion falla, NO reintentes automaticamente - reporta el error y pregunta como proceder
6. NUNCA crees anuncios para contenido prohibido (drogas, armas, contenido sexual, etc.)

FLUJO DE CONFIRMACION:
- Antes de ejecutar create_campaign, create_adset, o create_ad_with_creative:
  PRIMERO muestra un resumen detallado y pregunta "Confirmas? (Si/No)"
- Solo ejecuta cuando el usuario diga "si", "confirmo", "dale", "hazlo", etc.
- Si dice "no" o pide cambios, ajusta y muestra nuevo resumen.

PRESUPUESTO > $100:
- Si el presupuesto diario supera $100, ADVIERTE del monto y pide doble confirmacion.
- Si recibes safety_violation por budget, explica al usuario y pide confirmacion explicita.
- Cuando el usuario confirme, usa budget_confirmed=true al llamar create_adset.

FORMATO:
- Responde siempre en espanol
- Se conciso pero claro
- Para metricas, usa formato estructurado
- Muestra IDs en formato codigo

CATEGORIAS ESPECIALES:
Cuando el usuario quiera crear una campana, pregunta si el producto/servicio esta relacionado con:
credito, empleo, vivienda, o politica/elecciones. Si aplica, usa special_ad_categories.

Tienes acceso a plantillas de segmentacion y frameworks de copy publicitario.
Cuando sea relevante, sugierelos al usuario.
"""


class ClaudeAgent:
    def __init__(self, config: BotConfig):
        self.client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
        self.model = config.claude_model
        self.store = ConversationStore(max_messages=50, ttl_hours=24)
        self.pending_images: dict[int, str] = {}

    async def process_message(self, chat_id: int, user_text: str) -> str:
        """Process a user message through Claude and return the response text."""
        self.store.add_message(chat_id, {"role": "user", "content": user_text})
        messages = self.store.get_messages(chat_id)

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=TOOL_DEFINITIONS,
                    messages=messages,
                )
            except anthropic.RateLimitError:
                return "El servicio esta temporalmente ocupado. Intenta de nuevo en unos segundos."
            except anthropic.APIError as e:
                logger.error(f"Claude API error: {e}")
                return f"Error de API: {e.message}"

            assistant_content = response.content
            # Store the raw content blocks for conversation history
            self.store.add_message(chat_id, {
                "role": "assistant",
                "content": [self._block_to_dict(b) for b in assistant_content],
            })

            # Check for tool use
            tool_use_blocks = [b for b in assistant_content if b.type == "tool_use"]

            if not tool_use_blocks:
                # No tools - extract text response
                text_parts = [b.text for b in assistant_content if b.type == "text"]
                return "\n".join(text_parts) or "..."

            # Execute tools and build results
            tool_results = []
            for tool_block in tool_use_blocks:
                logger.info(f"Executing tool: {tool_block.name}")
                result = await execute_tool(
                    tool_name=tool_block.name,
                    tool_input=tool_block.input,
                    chat_id=chat_id,
                    pending_images=self.pending_images,
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            # Add tool results to history
            self.store.add_message(chat_id, {"role": "user", "content": tool_results})
            messages = self.store.get_messages(chat_id)

        return "Se alcanzo el limite de procesamiento. Intenta reformular tu solicitud."

    @staticmethod
    def _block_to_dict(block) -> dict:
        """Convert an API content block to a serializable dict."""
        if block.type == "text":
            return {"type": "text", "text": block.text}
        elif block.type == "tool_use":
            return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
        return {"type": block.type}
