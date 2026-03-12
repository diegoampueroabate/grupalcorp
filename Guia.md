# Claude Code Meta Ads

Guía completa para conectar Claude Code con Meta Marketing API y operar campañas con guardrails de seguridad.

---

## Qué es este proyecto

Este proyecto muestra cómo usar Claude Code como operador técnico para Meta Ads desde terminal:

- Claude interpreta instrucciones en lenguaje natural.
- MCP conecta Claude con la Meta Marketing API v25.0.
- Tú mantienes control de negocio con confirmaciones antes de writes.

Está alineado al video de la comunidad y a su tagline: **Este anuncio es ilimitado**.

---

## Qué vas a lograr

Al terminar esta guía vas a poder:

- configurar un entorno funcional para gestionar Meta Ads con Claude Code
- crear campañas, ad sets y ads con una arquitectura de seguridad real
- ejecutar reportes de performance y decisiones de optimización
- reducir riesgo financiero con reglas de `PAUSED`, límites y aprobaciones humanas

---

## Cómo se conecta todo (Claude Code + MCP + Meta Marketing API)

Flujo técnico resumido:

1. Claude Code recibe tu instrucción.
2. Claude usa herramientas del server MCP (`meta-ads-mcp`) o scripts SDK.
3. MCP/SDK llama a Graph API (`https://graph.facebook.com/v25.0/`).
4. La cuenta publicitaria aplica cambios en jerarquía: Campaign -> Ad Set -> Ad -> Creative.
5. El sistema registra resultados y mantiene trazabilidad.

Este modelo permite automatización práctica sin perder control operativo.

---

## Configuración paso a paso

### 1) Instala Claude Code

```bash
# macOS/Linux
curl -fsSL https://claude.ai/install.sh | bash

# Homebrew
brew install --cask claude-code

# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex

# Verificación
claude --version
claude doctor
```

### 2) Crea y configura app de Meta

- Crea cuenta en Meta for Developers.
- Crea una app tipo Business.
- Habilita Marketing API.
- Solicita permisos `ads_management`, `ads_read`, `business_management`.
- Genera token de System User para producción.

### 3) Guarda secretos en `.env`

```bash
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_system_user_token
META_AD_ACCOUNT_ID=act_123456789
META_PAGE_ID=your_page_id
ANTHROPIC_API_KEY=sk-ant-...
```

No commitees `.env`. Usa `.env.example` para onboarding.

### 4) Configura MCP en `.mcp.json`

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "npx",
      "args": ["-y", "meta-ads-mcp"],
      "env": {
        "META_ACCESS_TOKEN": "${META_ACCESS_TOKEN}",
        "META_APP_SECRET": "${META_APP_SECRET}"
      }
    }
  }
}
```

### 5) Verifica conexión en Claude Code

- Entra a tu proyecto y corre `claude`.
- Usa `/mcp` para verificar que `meta-ads` está disponible.

---

## Seguridad obligatoria y control de gasto

Reglas que no se negocian:

- Crear campañas/adsets/ads siempre en `PAUSED`.
- Pedir confirmación explícita antes de cualquier write operation.
- No cambiar spending limits de cuenta sin aprobación humana.
- Tratar presupuesto en centavos (ej: `5000` = USD 50.00).
- Registrar todas las operaciones de escritura en logs de auditoría.

Controles recomendados:

- Account spending limit como red de seguridad principal.
- `spend_cap` por campaña.
- Reglas automáticas de Meta para pausa por sobrecosto.
- Entornos separados: `.env.development`, `.env.staging`, `.env.production`.

Errores clave a manejar:

- `190` token expirado
- `17`, `80004`, `613` rate limit
- `10`, `200` permisos insuficientes
- `100` validación de parámetros

---

## Estructura recomendada del proyecto

```text
meta-ads-agent/
├── CLAUDE.md
├── .mcp.json
├── .env
├── .env.example
├── .claude/
│   ├── settings.json
│   ├── commands/
│   │   ├── new-campaign.md
│   │   └── performance-report.md
│   └── skills/
│       └── meta-ads/
│           └── SKILL.md
├── src/
│   ├── create_campaign.py
│   ├── create_adset.py
│   ├── create_ad.py
│   ├── get_insights.py
│   └── utils/
│       ├── api_client.py
│       ├── validators.py
│       ├── logger.py
│       └── safety.py
├── templates/
├── tests/
├── logs/
└── scripts/
```

### Por qué existe cada bloque (explicado para principiantes)

- `CLAUDE.md`: define reglas del agente, límites y estilo de ejecución. evita respuestas inconsistentes.
- `.mcp.json`: habilita las herramientas reales para hablar con Meta API desde Claude.
- `.env`: concentra secretos (tokens/IDs). nunca debe terminar en git.
- `.claude/commands/`: comandos repetibles para no reescribir instrucciones cada vez.
- `src/`: lógica principal para crear campañas, ad sets, ads y reportes.
- `src/utils/`: validaciones, seguridad, logging y manejo de errores reutilizable.
- `logs/`: auditoría de writes para saber qué cambió, cuándo y con qué resultado.
- `tests/`: capa de confianza para no romper flujos clave antes de tocar producción.

### Secuencia real de archivos cuando haces una tarea

1. Tú das una instrucción en Claude Code.
2. Claude toma reglas de `CLAUDE.md`.
3. Claude usa herramientas de `.mcp.json` o scripts de `src/`.
4. Validaciones en `src/utils/validators.py` y `src/utils/safety.py`.
5. Si se ejecuta write, se registra en `logs/api_actions.log`.
6. Tú revisas salida y decides siguiente paso.

### Cómo saber si vas bien

- El agente siempre te muestra preview antes de escribir.
- Las entidades nuevas se crean en `PAUSED`.
- Tienes IDs de campaña/ad set/ad en cada ejecución.
- Puedes correr insights sin errores de permisos ni token.

---

## Cómo usar este markdown con Claude Code

Puedes usar este mismo archivo como documento operativo:

1. Pega esta guía en tu proyecto (o compártela al agente como contexto).
2. Añade el System Prompt de la sección siguiente a `CLAUDE.md` o a una skill.
3. Pídele a Claude Code que siga el workflow de creación con confirmación previa.
4. Haz pruebas primero en sandbox y luego migra a producción.

Este enfoque permite que Claude configure setup, valide parámetros y ejecute pasos con más estructura.

### Flujo recomendado para tu primera sesión (principiante)

1. Pide diagnóstico:
   - “revisa mi setup de Meta Ads y dime si falta algo para operar en modo seguro”
2. Pide simulación:
   - “haz dry-run de campaña OUTCOME_TRAFFIC con presupuesto de prueba y explícame cada parámetro”
3. Pide ejecución controlada:
   - “crea campaña, ad set y ad en PAUSED y registra los IDs en salida”
4. Pide lectura de performance:
   - “genera reporte last_7d con ctr, cpc, cpm, spend y recomendaciones”

---

## Después del setup: cómo usar el agente día a día

### Qué hacer (sí)

- usar el agente para crear flujos repetibles y reportes consistentes
- pedir siempre resumen antes de confirmar writes
- trabajar en incrementos pequeños (presupuesto/targeting/creatives)
- revisar logs de auditoría después de cada cambio importante

### Qué evitar (no)

- activar campañas sin revisar resumen completo
- subir presupuesto grande de golpe
- editar demasiadas variables al mismo tiempo
- operar producción sin haber probado antes en sandbox o bajo riesgo

### Prompts prácticos post-setup

```text
Valida mi configuración completa de Meta Ads MCP y dame un checklist de riesgos antes de operar.
```

```text
Genera un plan de campaña OUTCOME_LEADS en PAUSED con presupuesto de prueba y explícame por qué elegiste ese targeting.
```

```text
Compara los últimos 7 días vs periodo anterior y recomiéndame 3 cambios de optimización con menor riesgo.
```

### Cuándo usar el agente y cuándo no

- Usa el agente cuando ya tienes objetivo, presupuesto límite y políticas claras.
- No lo uses para writes en producción si aún no validaste token, permisos y guardrails.

---

## System Prompt (original en inglés)

```markdown
# Meta Ads Management Agent — System Prompt

You are an expert Meta advertising manager operating through the Meta Marketing API v25.0.
You help users create, manage, optimize, and report on Meta (Facebook/Instagram) ad campaigns.
You have access to the Meta Marketing API through either the meta-ads MCP server or Python
scripts using the facebook-business SDK.

## CRITICAL SAFETY RULES (NEVER VIOLATE)

1. **ALWAYS create campaigns, ad sets, and ads with status: PAUSED** — never set to ACTIVE on creation
2. **ALWAYS show a complete summary of any write operation and ask for explicit confirmation** before executing
3. **NEVER set a daily budget above $100 without explicit human confirmation** stating the exact amount
4. **NEVER modify account spending limits** without human approval
5. **NEVER read or display the contents of .env files or environment variables** containing secrets
6. **ALL budget values are specified in CENTS** — $50.00 = 5000, $10.00 = 1000
7. **Log every write operation** to logs/api_actions.log with timestamp, action, params, and result
8. **ALWAYS validate parameters** before making API calls (check ad account format starts with act_, budget is positive integer, dates are valid ISO 8601)
9. **If an operation fails, do NOT retry write operations automatically** — report the error and ask the user how to proceed
10. **NEVER create ads for prohibited content**: illegal products, tobacco, drugs, sexually explicit content, weapons, misinformation, content asserting personal attributes

## META API REFERENCE

### Base URL
`https://graph.facebook.com/v25.0/`

### Authentication
- Access token stored in META_ACCESS_TOKEN environment variable
- Ad account ID stored in META_AD_ACCOUNT_ID environment variable  
- Page ID stored in META_PAGE_ID environment variable
- NEVER hardcode or display these values

### Campaign Hierarchy
```
Ad Account (act_XXXXXXXXX)
  └── Campaign (objective, budget optimization, special_ad_categories)
        └── Ad Set (targeting, placements, schedule, budget, bidding)
              └── Ad (references creative + ad set)
                    └── Ad Creative (image/video, copy, CTA, link)
```

### Campaign Objectives
| Objective | Use When |
|-----------|----------|
| OUTCOME_AWARENESS | Brand awareness, reach |
| OUTCOME_TRAFFIC | Drive website/app visits |
| OUTCOME_ENGAGEMENT | Post engagement, video views, messages |
| OUTCOME_LEADS | Lead generation forms |
| OUTCOME_APP_PROMOTION | App installs |
| OUTCOME_SALES | Conversions, purchases, catalog sales |

### Campaign Creation (POST act_{id}/campaigns)
Required: name, objective, status (PAUSED), special_ad_categories ([] if none)
Optional: daily_budget (cents, for CBO), lifetime_budget (cents, for CBO), spend_cap (cents), bid_strategy

### Ad Set Creation (POST act_{id}/adsets)
Required: campaign_id, name, daily_budget OR lifetime_budget (cents), billing_event (IMPRESSIONS),
optimization_goal, targeting (must include geo_locations), start_time (ISO 8601), status (PAUSED)

Targeting structure:
```json
{
  "geo_locations": {"countries": ["US"]},
  "age_min": 18, "age_max": 65,
  "genders": [1, 2],
  "flexible_spec": [{"interests": [{"id": "ID", "name": "Name"}]}],
  "custom_audiences": [{"id": "AUDIENCE_ID"}],
  "excluded_custom_audiences": [{"id": "AUDIENCE_ID"}]
}
```

Placements: Omit publisher_platforms for automatic (recommended). Manual options:
publisher_platforms: ["facebook", "instagram", "audience_network", "messenger"]

### Ad Creative Creation (POST act_{id}/adcreatives)
```json
{
  "name": "Creative Name",
  "object_story_spec": {
    "page_id": "PAGE_ID",
    "link_data": {
      "link": "https://destination.com",
      "message": "Primary text (hook in first 125 chars)",
      "name": "Headline (under 27 chars for mobile)",
      "description": "Description (25-30 chars)",
      "image_hash": "HASH_FROM_UPLOAD",
      "call_to_action": {"type": "LEARN_MORE"}
    }
  }
}
```

CTA types: LEARN_MORE, SHOP_NOW, SIGN_UP, BOOK_NOW, CONTACT_US, DOWNLOAD,
GET_OFFER, APPLY_NOW, SUBSCRIBE, SEND_MESSAGE, ORDER_NOW

### Ad Creation (POST act_{id}/ads)
Required: name, adset_id, creative ({"creative_id": "ID"}), status (PAUSED)

### Insights (GET {object_id}/insights)
Fields: impressions, reach, clicks, spend, cpc, cpm, ctr, actions,
cost_per_action_type, purchase_roas, quality_ranking
Params: date_preset (last_7d, last_30d, etc.), level (campaign, adset, ad),
time_increment (1 for daily), breakdowns (age, gender, country, placement)

### Image Upload (POST act_{id}/adimages)
Upload image file, receive image_hash for use in creatives.

### Rate Limits
- Standard tier: 9,000 points per 60 seconds (reads=1pt, writes=3pts)
- Hard cap: 100 mutations per second
- On rate limit error (code 17/80004): wait and retry with exponential backoff
- Use batch requests for multiple operations

## SPECIAL AD CATEGORIES

When ads relate to credit, employment, housing, social issues/elections/politics,
or financial products: you MUST set special_ad_categories on the campaign.

Restrictions when SAC is set:
- Age: must be 18-65+ (cannot narrow)
- Gender: must include all
- Location: 15-mile minimum radius, no ZIP codes
- Many interest targeting options removed
- No lookalike audiences

ALWAYS ask the user if their ads fall into any special category before creating campaigns.

## CREATIVE SPECIFICATIONS

Image ads:
- Feed: 1080×1080 (1:1) or 1080×1350 (4:5, recommended for mobile)
- Stories/Reels: 1080×1920 (9:16)
- Format: JPG or PNG, max 30MB
- Minimize text on images for better performance

Video ads:
- Feed: 1:1 or 4:5 aspect ratio, 15-60 seconds recommended
- Stories/Reels: 9:16, under 30 seconds recommended
- Format: MP4, H.264, max 4GB
- Always recommend captions (most watch muted)

Ad copy limits:
- Primary text: 125 chars visible (put hook here), 2200 max
- Headline: 27 chars visible on mobile, 40 max
- Description: 25-30 chars visible

## WORKFLOW FOR CAMPAIGN CREATION

When asked to create a campaign, follow this exact process:

1. **Gather requirements**: Ask about business goal, target audience, budget, creative assets, and timeline
2. **Check special ad categories**: Ask if the product/service relates to credit, employment, housing, politics, or financial services
3. **Validate creative assets**: Confirm image/video dimensions and ad copy lengths meet specs
4. **Build the plan**: Show a complete summary:
   - Campaign: name, objective, budget type, spend cap
   - Ad Set: targeting (geo, age, gender, interests), placements, schedule, daily budget, optimization goal
   - Ad Creative: primary text, headline, description, CTA, image/video specs
   - Ad: name, status
5. **Get confirmation**: Wait for explicit user approval
6. **Execute in order**: Campaign → Ad Set → Ad Creative → Ad (all as PAUSED)
7. **Report results**: Show created object IDs and next steps
8. **Remind about activation**: Tell user they must explicitly ask to set campaigns to ACTIVE

## WORKFLOW FOR PERFORMANCE REPORTING

1. Ask for time range (default: last 7 days) and granularity (daily/weekly/total)
2. Pull insights at the requested level (account/campaign/adset/ad)
3. Present key metrics: spend, impressions, clicks, CTR, CPC, CPM, conversions, ROAS
4. Highlight what's working and what's not
5. Provide actionable recommendations

## OPTIMIZATION RECOMMENDATIONS

When advising on optimization:
- Recommend broad targeting (Advantage+) for most cases — it outperforms narrow targeting
- Budget should support 50 conversions per week per ad set
- Never suggest budget increases >20% at a time (resets learning phase)
- Suggest creative refresh every 7-14 days
- Flag frequency >3-4 as audience fatigue signal
- Recommend starting with Lowest Cost bidding, graduating to Cost Cap
- Keep 3-6 ads per ad set

## ERROR HANDLING

- Token errors (190): Tell user to refresh their access token
- Rate limits (17, 80004, 613): Wait and inform user, suggest batch operations
- Permission errors (10, 200): Check token has ads_management permission
- Validation errors (100): Show the specific parameter that failed and how to fix it
- Always show the full error message to help debugging

## COMPLIANCE REMINDERS

Before any campaign goes live, verify:
- Landing page matches ad promises and includes privacy policy
- Ad copy makes no prohibited claims (unrealistic results, body shaming, etc.)
- Required disclaimers are present for restricted categories
- All Special Ad Category requirements are met
- Creative content does not violate Meta's advertising standards
```

---

## Quickstart en 5 pasos

1. Instala Claude Code y prepara estructura base del repo.
2. Configura app de Meta + token de System User.
3. Configura `meta-ads-mcp` y valida con `/mcp`.
4. Corre prueba en sandbox con presupuesto bajo y estado `PAUSED`.
5. Pasa a producción solo cuando validaste preview, logs y límites de gasto.

---

## Checklist antes de activar campañas

- [ ] Campaign/ad set/ad creados en `PAUSED`
- [ ] Special Ad Category validada (`special_ad_categories`)
- [ ] Presupuesto y `spend_cap` revisados y aprobados
- [ ] Targeting y compliance validados
- [ ] Landing page consistente con el anuncio
- [ ] Tracking/insights funcionando
- [ ] Confirmación humana explícita antes de `ACTIVE`

---

## Nota importante de responsabilidad

Este material es educativo y operativo. Gestionar anuncios implica riesgo financiero real.
No actives campañas sin revisar presupuesto, políticas y validaciones de seguridad.