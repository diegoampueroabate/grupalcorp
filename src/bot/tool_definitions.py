"""Claude tool schemas for Meta Ads operations."""

TOOL_DEFINITIONS = [
    {
        "name": "get_campaigns",
        "description": (
            "Lista todas las campanas de la cuenta publicitaria. "
            "Devuelve ID, nombre, objetivo, status y presupuesto de cada campana."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["ACTIVE", "PAUSED", "ARCHIVED", "ALL"],
                    "description": "Filtrar por estado. ALL para todas.",
                    "default": "ALL",
                },
                "limit": {
                    "type": "integer",
                    "description": "Cantidad maxima de campanas a devolver. Default 25.",
                    "default": 25,
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_campaign",
        "description": (
            "Crea una nueva campana publicitaria en Meta Ads. SIEMPRE se crea en estado PAUSED. "
            "El presupuesto se especifica en CENTAVOS (ej: $50.00 = 5000). "
            "Antes de llamar esta herramienta, DEBES haber mostrado un resumen al usuario y recibido confirmacion explicita."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre de la campana"},
                "objective": {
                    "type": "string",
                    "enum": [
                        "OUTCOME_AWARENESS", "OUTCOME_TRAFFIC", "OUTCOME_ENGAGEMENT",
                        "OUTCOME_LEADS", "OUTCOME_APP_PROMOTION", "OUTCOME_SALES",
                    ],
                    "description": "Objetivo de la campana",
                },
                "special_ad_categories": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["CREDIT", "EMPLOYMENT", "HOUSING", "ISSUES_ELECTIONS_POLITICS"],
                    },
                    "description": "Categorias especiales de anuncios. Usar [] si no aplica ninguna.",
                },
                "daily_budget": {
                    "type": "integer",
                    "description": "Presupuesto diario en CENTAVOS (ej: $50 = 5000). Para CBO.",
                },
                "spend_cap": {
                    "type": "integer",
                    "description": "Limite de gasto total de la campana en centavos.",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Si es true, solo muestra preview sin crear.",
                },
            },
            "required": ["name", "objective", "special_ad_categories"],
        },
    },
    {
        "name": "create_adset",
        "description": (
            "Crea un conjunto de anuncios (Ad Set) dentro de una campana existente. "
            "SIEMPRE se crea en estado PAUSED. Presupuesto en CENTAVOS. "
            "Si el presupuesto diario supera $100 (10000 centavos), se requiere confirmacion explicita del usuario. "
            "Usa budget_confirmed=true SOLO si el usuario ya confirmo explicitamente el monto."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string", "description": "ID de la campana padre"},
                "name": {"type": "string", "description": "Nombre del ad set"},
                "daily_budget": {"type": "integer", "description": "Presupuesto diario en centavos"},
                "optimization_goal": {
                    "type": "string",
                    "enum": [
                        "LINK_CLICKS", "LANDING_PAGE_VIEWS", "IMPRESSIONS", "REACH",
                        "OFFSITE_CONVERSIONS", "LEAD_GENERATION", "POST_ENGAGEMENT",
                        "VIDEO_VIEWS", "APP_INSTALLS", "QUALITY_LEAD", "ENGAGED_USERS", "CONVERSATIONS",
                    ],
                    "description": "Objetivo de optimizacion",
                },
                "targeting": {
                    "type": "object",
                    "description": "Segmentacion. DEBE incluir geo_locations con al menos countries, regions o cities.",
                },
                "start_time": {"type": "string", "description": "Fecha de inicio ISO 8601"},
                "end_time": {"type": "string", "description": "Fecha de fin ISO 8601. Opcional."},
                "budget_confirmed": {
                    "type": "boolean",
                    "description": "True SOLO si el usuario ya confirmo explicitamente un presupuesto > $100/dia.",
                },
                "dry_run": {"type": "boolean"},
            },
            "required": ["campaign_id", "name", "optimization_goal", "targeting"],
        },
    },
    {
        "name": "create_ad_with_creative",
        "description": (
            "Crea un anuncio completo: sube imagen (si hay), crea el creativo y luego el anuncio. "
            "Todo se crea como PAUSED. Valida longitudes de texto automaticamente. "
            "Limites: primary_text max 2200 chars, headline max 40, description max 30."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "adset_id": {"type": "string", "description": "ID del ad set padre"},
                "ad_name": {"type": "string", "description": "Nombre del anuncio"},
                "primary_text": {
                    "type": "string",
                    "description": "Texto principal del anuncio (max 2200 chars, primeros 125 visibles)",
                },
                "headline": {
                    "type": "string",
                    "description": "Titular (max 40 chars, 27 visibles en movil)",
                },
                "description": {
                    "type": "string",
                    "description": "Descripcion (max 30 chars)",
                },
                "link": {"type": "string", "description": "URL de destino"},
                "cta_type": {
                    "type": "string",
                    "enum": [
                        "LEARN_MORE", "SHOP_NOW", "SIGN_UP", "BOOK_NOW", "CONTACT_US",
                        "DOWNLOAD", "GET_OFFER", "APPLY_NOW", "SUBSCRIBE", "SEND_MESSAGE", "ORDER_NOW",
                    ],
                    "default": "LEARN_MORE",
                },
                "image_hash": {"type": "string", "description": "Hash de imagen ya subida."},
                "has_pending_image": {
                    "type": "boolean",
                    "description": "True si el usuario envio una imagen en la conversacion.",
                },
                "dry_run": {"type": "boolean"},
            },
            "required": ["adset_id", "ad_name", "primary_text", "headline", "link"],
        },
    },
    {
        "name": "get_insights",
        "description": (
            "Obtiene metricas de rendimiento de Meta Ads. "
            "Devuelve spend, impressions, clicks, CTR, CPC, CPM, conversiones y recomendaciones automaticas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["account", "campaign", "adset", "ad"],
                    "default": "campaign",
                },
                "date_preset": {
                    "type": "string",
                    "enum": [
                        "today", "yesterday", "this_month", "last_month", "this_quarter",
                        "last_3d", "last_7d", "last_14d", "last_28d", "last_30d", "last_90d",
                        "last_week_mon_sun", "last_week_sun_sat", "last_quarter", "last_year", "this_year",
                    ],
                    "default": "last_7d",
                },
                "object_id": {"type": "string", "description": "ID especifico de campana/adset/ad."},
                "time_increment": {"type": "integer", "description": "1 para diario, 7 para semanal."},
                "breakdowns": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["age", "gender", "country", "publisher_platform", "placement", "device_platform"],
                    },
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_targeting_preset",
        "description": "Obtiene un preset de segmentacion predefinido para usar en la creacion de ad sets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "preset_name": {
                    "type": "string",
                    "enum": ["us_broad", "us_young_adults", "latam_broad", "spain_broad", "ecommerce_shoppers"],
                    "description": "Nombre del preset de segmentacion",
                },
            },
            "required": ["preset_name"],
        },
    },
    {
        "name": "get_ad_copy_template",
        "description": "Obtiene un framework de copy publicitario con estructura y ejemplos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_name": {
                    "type": "string",
                    "enum": ["aida", "pas", "bab", "social_proof", "direct_offer"],
                },
            },
            "required": ["template_name"],
        },
    },
    {
        "name": "check_token_status",
        "description": "Verifica si el token de acceso a Meta es valido y muestra info de la cuenta.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
