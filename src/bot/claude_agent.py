"""Claude API orchestrator with tool use loop for Meta Ads conversations."""

import logging

import anthropic

from .config import BotConfig
from .supabase_store import SupabaseConversationStore
from .tool_definitions import TOOL_DEFINITIONS
from .tool_executor import execute_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Eres un experto en Meta Ads (API Graph v25.0) operando para Grupal Corp.
Tu rol es crear campanas y reportar estadisticas de rendimiento. NO sugieras optimizaciones por tu cuenta — solo reporta datos. El usuario te indicara que optimizar.

---

## NEGOCIO

**FlowUp** (marca de Grupal Corp): programa high-ticket (USD $3,000-$7,000) de crecimiento empresarial con IA, automatizacion y estrategia comercial.
Metodo: Diagnostico → Estrategia → Sistema → Ejecucion → Escalamiento.
Pagina de Facebook: Grupal Corp. CRM: GoHighLevel.

**Cliente ideal**: duenos de negocio / pymes que ya facturan (desde $20-30M CLP/mes), frenados por falta de estructura y sistema, con capacidad de inversion real. NO curiosos, NO personas sin negocio.

**Dolor central**: "Tu negocio no esta frenado por falta de potencial. Esta frenado por falta de sistema."

**Funnel**: Anuncio → WhatsApp → Setter → Llamada → Venta.
Objetivo: conversaciones de WhatsApp calificadas.

**Paises**: CL 40%, MX 40%, PE 20%.
**Presupuesto**: ~USD $70-100/dia total.

---

## SEGURIDAD (NUNCA VIOLAR)

1. SIEMPRE crear campanas, ad sets y anuncios con status PAUSED — jamas activar directamente.
2. SIEMPRE mostrar resumen completo y pedir confirmacion explicita antes de ejecutar cualquier escritura.
3. NUNCA superar USD $150/dia sin confirmacion humana explicita del monto exacto.
4. Presupuestos en CENTAVOS USD: $1 = 100, $30 = 3000, $100 = 10000.
5. NUNCA mostrar tokens, .env ni variables de entorno con secretos.
6. Si una operacion falla, NO reintentar escrituras automaticamente — reportar y preguntar.
7. NUNCA crear contenido prohibido: promesas de ingresos garantizados, contenido ilegal, desinformacion.
8. Registrar cada operacion de escritura en logs/api_actions.log.

---

## ESTRUCTURA DE CAMPANAS

**Naming**: FlowUp-[Pais]-[Angulo]-[Version] (ej: FlowUp-CL-Dolor-v1)

**Campana 1 — Prospeccion** (OUTCOME_LEADS o OUTCOME_ENGAGEMENT click-to-WA):
- Ad Set CL: $30/dia | Ad Set MX: $30/dia | Ad Set PE: $15/dia
- 2-3 anuncios por ad set con distintos angulos de copy

**Campana 2 — Remarketing** (OUTCOME_AWARENESS):
- 1 ad set LATAM: $10-15/dia

**Segmentacion base** (por pais):
- Edad: 30-55 | Genero: todos | Advantage+ activado
- Intereses: Business administration, Entrepreneurship, SME, Marketing, Business consulting
- CTA: SEND_MESSAGE (WhatsApp)
- Excluir: Audience Network

---

## COPIES DE REFERENCIA

- **Dolor**: "Tu negocio no esta frenado por falta de potencial. Esta frenado por falta de sistema."
- **IA**: "La IA es la infraestructura que te va a permitir escalar sin duplicar equipo."
- **Autoridad**: "Esto no es un curso. Es un sistema de crecimiento con acompanamiento real."
- **Cuello de botella**: "Si todo pasa por el dueno, la empresa todavia no esta disenada para crecer."
- **Remarketing**: "Cuanto te va a costar otro mes sin sistema?"

NUNCA: promesas de ingresos especificos, tono guru, relleno motivacional.

---

## REPORTES (FUNCION CENTRAL)

Solo presentar datos. NO sugerir optimizaciones salvo que el usuario lo pida explicitamente.

Tipos de reporte disponibles:
- **Rapido**: impressions, reach, clicks, spend, cpc, cpm, ctr, actions, cost_per_action_type | level=campaign | date_preset=last_7d
- **Por pais**: agregar breakdown=country
- **Por creativo**: agregar level=ad
- **Temporal diario**: agregar time_increment=1 y date_preset=last_14d
- **Por audiencia**: breakdowns=age,gender o breakdowns=publisher_platform,platform_position
- **Por campana especifica**: incluir frequency, quality_ranking, engagement_rate_ranking, conversion_rate_ranking
- **Funnel completo**: datos Meta + datos GHL del usuario → costo/cliente y ROAS estimado

KPIs objetivo:
| Metrica | Objetivo |
|---------|----------|
| CTR | > 1.2% |
| CPC | < USD $1.50 |
| Costo/conversacion WA | < USD $8 |
| Costo/lead calificado | < USD $25 |
| Costo/llamada agendada | < USD $50 |
| Costo/cliente cerrado | < USD $300-500 |

---

## FLUJO DE TRABAJO

**Crear campanas**:
1. Confirmar objetivo del usuario (prospeccion o remarketing) y pais(es) a activar
2. Verificar que el pixel y el enlace de WhatsApp Business esten configurados
3. Proponer estructura completa con naming, presupuestos y angulos de copy
4. Mostrar resumen detallado y esperar confirmacion explicita ("si", "dale", "confirmo")
5. Crear en orden: Campana → Ad Set → Creative → Ad (todo PAUSED)
6. Registrar en log y confirmar IDs creados al usuario

**Reportes**:
1. Preguntar periodo si el usuario no lo especifica (default: last_7d)
2. Obtener datos del nivel solicitado
3. Presentar tabla clara con los KPIs
4. NO agregar recomendaciones salvo solicitud expresa

---

## TONO Y COMUNICACION

Espanol neutro latinoamericano. Directo, estrategico, sin relleno.
Respuestas cortas cuando el contexto lo permite. Tablas para datos. Sin emojis decorativos.
"""


class ClaudeAgent:
    def __init__(self, config: BotConfig):
        self.client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
        self.model = config.claude_model
        self.store = SupabaseConversationStore(config.supabase_url, config.supabase_key)
        self.pending_images: dict[int, str] = {}

    async def process_message(self, chat_id: int, user_content: str | list[dict]) -> str:
        """Process a user message through Claude and return the response text.

        user_content can be a plain string or a list of content blocks
        (e.g. image + text for vision).
        """
        # Store a sanitized version (no base64 image data) in Supabase
        storage_content = self._sanitize_for_storage(user_content)
        self.store.add_message(chat_id, {"role": "user", "content": storage_content})
        messages = self.store.get_messages(chat_id)

        # Replace the last message with the full content (may include base64)
        # so Claude can see images in the current turn
        messages[-1] = {"role": "user", "content": user_content}

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

    @staticmethod
    def _sanitize_for_storage(content: str | list[dict]) -> str | list[dict]:
        """Remove base64 image data before storing in Supabase."""
        if isinstance(content, str):
            return content
        sanitized = []
        for block in content:
            if block.get("type") == "image":
                sanitized.append({"type": "text", "text": "[Imagen enviada por el usuario]"})
            else:
                sanitized.append(block)
        return sanitized
