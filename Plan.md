# Plan: Bot de Telegram - Asistente Conversacional de Meta Ads

## Contexto
El usuario quiere poder hablar con un bot de Telegram como su asistente de Meta Ads. No un bot de botones/menus, sino uno conversacional con IA que entienda lenguaje natural en espanol.

**Arquitectura**: Telegram -> Claude API (con tool use) -> Funciones Python existentes -> Meta API

El bot reutiliza TODA la logica de negocio existente (validators, safety, logger, create_*, get_insights) sin modificar ningun archivo actual.

---

## Archivos Nuevos (10 archivos en `src/bot/`)

| Archivo | Responsabilidad |
|---------|----------------|
| `src/bot/__init__.py` | Package marker |
| `src/bot/config.py` | Carga env vars del bot (TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_ID, ANTHROPIC_API_KEY) |
| `src/bot/main.py` | Entry point: `python -m src.bot.main` |
| `src/bot/telegram_handler.py` | Handlers de Telegram: /start, /reset, /help, mensajes, fotos. Auth guard (solo owner) |
| `src/bot/claude_agent.py` | Orquestador Claude API: system prompt, historial, loop de tool_use |
| `src/bot/tool_definitions.py` | 7 tool schemas JSON para Claude (create_campaign, create_adset, create_ad, get_insights, targeting presets, ad copy templates, check token) |
| `src/bot/tool_executor.py` | Dispatch: mapea tool_use de Claude a funciones Python existentes. Atrapa SafetyViolation/ValidationError |
| `src/bot/conversation_store.py` | Historial in-memory con TTL (24h) y limite de mensajes (50) |
| `src/bot/formatters.py` | Chunking de mensajes (4096 chars Telegram) y escape Markdown |
| `src/bot/media_handler.py` | Descarga fotos de Telegram a temp files para upload_image() |

---

## Flujo de Conversacion

```
Usuario (Telegram): "Quiero crear una campana de trafico para US con $50/dia"
    |
    v
telegram_handler.py: verifica auth (chat_id == OWNER_ID) -> pasa texto a claude_agent
    |
    v
claude_agent.py: envia a Claude API con system prompt + tools + historial
    |
    v
Claude responde (texto): "Te preparo la campana:
  - Objetivo: OUTCOME_TRAFFIC
  - Presupuesto: $50/dia (5000 centavos)
  - Pais: US
  Confirmas que proceda?"
    |
    v
Usuario: "Si, dale"
    |
    v
Claude llama tool_use: create_campaign(name=..., objective=OUTCOME_TRAFFIC, ...)
    |
    v
tool_executor.py: llama create_campaign() existente -> safety checks -> Meta API -> log
    |
    v
Claude recibe resultado, responde: "Campana creada! ID: 123456, Estado: PAUSED"
```

---

## Seguridad (4 capas)

1. **Telegram Auth**: Solo `TELEGRAM_OWNER_ID` puede interactuar
2. **Claude System Prompt**: 10 reglas de seguridad embebidas, confirmacion obligatoria antes de writes
3. **safety.py existente**: PAUSED forzado, budget >$100 requiere confirmacion, validaciones
4. **tool_executor**: Atrapa TODAS las excepciones, retorna JSON a Claude para que explique al usuario

---

## Dependencias Nuevas

```
python-telegram-bot>=20.7    # Framework async de Telegram
anthropic>=0.40.0            # Claude API SDK
```

## Variables de Entorno Nuevas (.env)

```
TELEGRAM_BOT_TOKEN=token_de_botfather
TELEGRAM_OWNER_ID=tu_chat_id_numerico
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
```

---

## Orden de Implementacion

1. `config.py` + actualizar `.env.example` + `requirements.txt`
2. `conversation_store.py` + `formatters.py` (utilidades independientes)
3. `tool_definitions.py` (7 schemas de tools)
4. `tool_executor.py` (dispatch a funciones existentes)
5. `claude_agent.py` (orquestador con AsyncAnthropic + loop tool_use)
6. `media_handler.py` (descarga de fotos)
7. `telegram_handler.py` (handlers + auth guard)
8. `main.py` (entry point)
9. Tests: `test_conversation_store.py`, `test_formatters.py`, `test_tool_executor.py`

---

## Archivos Existentes a Reutilizar (NO modificar)

- `src/create_campaign.py` -> `create_campaign()`
- `src/create_adset.py` -> `create_adset()`
- `src/create_ad.py` -> `upload_image()`, `create_creative()`, `create_ad()`
- `src/get_insights.py` -> `get_insights()`, `format_insights_table()`, `calculate_recommendations()`
- `src/utils/api_client.py` -> `init_api()`, `get_account()`
- `src/utils/validators.py` -> todas las funciones de validacion
- `src/utils/safety.py` -> todos los safety checks
- `src/utils/logger.py` -> audit logging
- `templates/targeting-presets.json` + `templates/ad-copy-templates.json`

---

## Manejo de Budget > $100

1. Claude muestra resumen y pide confirmacion (system prompt lo obliga)
2. Si safety.py lanza SafetyViolation, tool_executor la retorna como JSON
3. Claude le explica al usuario y pide doble confirmacion
4. En el segundo intento con `budget_confirmed: true`, tool_executor bypasea el check de budget pero mantiene todas las demas validaciones

---

## Verificacion

1. `pip install python-telegram-bot anthropic` - Instalar dependencias
2. Crear bot en BotFather, obtener token
3. Obtener tu chat_id (enviar mensaje a @userinfobot)
4. Configurar .env con las 4 nuevas variables
5. `python -m src.bot.main` - Iniciar bot
6. Enviar `/start` desde Telegram - debe responder bienvenida
7. Enviar "como van mis campanas?" - debe mostrar insights
8. Enviar "crea una campana de trafico" - debe pedir detalles y confirmacion
9. Tests: `python -m pytest tests/ -v`
