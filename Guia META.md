# Guia META - Referencia Operativa Completa

Referencia rapida de todo lo que puedes hacer con el agente Meta Ads desde Claude Code.

---

## Dos Vias de Ejecucion

| Via | Que es | Cuando usarla |
|-----|--------|---------------|
| **MCP (meta-ads-mcp)** | Servidor MCP que Claude llama directamente | Operaciones rapidas, busquedas, lectura de datos |
| **Python Scripts (src/)** | Scripts con facebook-business SDK | Creacion con safety checks, validacion, audit logging |

Claude elige automaticamente la mejor via segun la tarea.

---

## Herramientas MCP Disponibles (29 tools)

### Cuenta y Autenticacion
| Tool | Que hace |
|------|----------|
| `get_ad_accounts` | Lista todas las cuentas publicitarias accesibles |
| `get_account_info` | Info detallada de una cuenta (nombre, moneda, timezone, status) |
| `get_account_pages` | Paginas asociadas a la cuenta |
| `get_login_link` | Link de autenticacion de Meta |

### Campanas
| Tool | Que hace |
|------|----------|
| `get_campaigns` | Lista campanas con filtro por status |
| `get_campaign_details` | Detalle de una campana especifica |
| `create_campaign` | Crea campana nueva (objetivo, presupuesto, SAC) |
| `create_budget_schedule` | Programa presupuesto para periodos de alta demanda |

### Ad Sets
| Tool | Que hace |
|------|----------|
| `get_adsets` | Lista ad sets con filtro por campana |
| `get_adset_details` | Detalle de un ad set especifico |
| `create_adset` | Crea ad set (targeting, presupuesto, schedule) |
| `update_adset` | Modifica ad set (frequency caps, bidding, status) |

### Ads
| Tool | Que hace |
|------|----------|
| `get_ads` | Lista ads con filtro por campana o ad set |
| `get_ad_details` | Detalle de un ad especifico |
| `create_ad` | Crea ad usando un creative existente |
| `update_ad` | Modifica ad (status, bid) |

### Creativos
| Tool | Que hace |
|------|----------|
| `get_ad_creatives` | Obtiene creativos de un ad |
| `create_ad_creative` | Crea creative con imagen y texto |
| `update_ad_creative` | Modifica contenido del creative |
| `upload_ad_image` | Sube imagen para usar en creativos |
| `get_ad_image` | Descarga/visualiza imagen de un ad |

### Performance y Analytics
| Tool | Que hace |
|------|----------|
| `get_insights` | Metricas de performance con breakdowns y attribution windows |

### Targeting y Busqueda
| Tool | Que hace |
|------|----------|
| `search_interests` | Busca intereses por keyword para targeting |
| `get_interest_suggestions` | Sugerencias de intereses basadas en intereses existentes |
| `validate_interests` | Valida que un interes exista y sea usable |
| `search_behaviors` | Lista opciones de targeting por comportamiento |
| `search_demographics` | Opciones demograficas por categoria |
| `search_geo_locations` | Busca ubicaciones geograficas para targeting |
| `search` | Busqueda generica (cuentas, campanas, ads, paginas) |

---

## Scripts Python Disponibles

### `src/create_campaign.py`
Crea campanas con safety checks integrados.
```bash
python src/create_campaign.py \
  --name "Mi Campana" \
  --objective OUTCOME_TRAFFIC \
  --special-ad-categories "[]" \
  --daily-budget 5000 \
  --dry-run
```
- Fuerza status PAUSED
- Valida objetivo y SAC
- Soporta `--spend-cap` y `--dry-run`

### `src/create_adset.py`
Crea ad sets con validacion de targeting.
```bash
python src/create_adset.py \
  --campaign-id 123456 \
  --name "Ad Set 1" \
  --daily-budget 5000 \
  --optimization-goal LINK_CLICKS \
  --targeting '{"geo_locations":{"countries":["CL"]},"age_min":25,"age_max":45}'
```
- Valida geo_locations obligatorio
- Confirma si budget > $100/dia
- Soporta `--start-time` ISO 8601

### `src/create_ad.py`
Crea ad creative + ad en secuencia.
```bash
python src/create_ad.py \
  --adset-id 789 \
  --name "Ad 1" \
  --primary-text "Hook aqui" \
  --headline "Titulo" \
  --link "https://misite.com" \
  --cta LEARN_MORE \
  --image-path "creative.jpg"
```
- Sube imagen automaticamente
- Crea creative y luego ad
- Valida limites de caracteres

### `src/get_insights.py`
Reportes de performance con recomendaciones.
```bash
python src/get_insights.py \
  --level campaign \
  --date-preset last_7d \
  --fields spend,impressions,clicks,ctr,cpc,actions
```
- Niveles: `campaign`, `adset`, `ad`
- Presets: `today`, `yesterday`, `last_7d`, `last_14d`, `last_30d`, `last_90d`
- Soporta `--breakdowns`, `--time-increment`, `--campaign-id`
- Genera recomendaciones automaticas (CTR bajo, frecuencia alta, quality ranking)

### `scripts/check_token.py`
Verificacion rapida de token y cuenta.
```bash
python scripts/check_token.py
```
- Valida token contra Graph API
- Muestra permisos y expiracion
- Verifica acceso a la cuenta publicitaria

---

## Comandos Claude Code (Slash Commands)

| Comando | Que hace |
|---------|----------|
| `/new-campaign` | Entrevista guiada de 6 preguntas para crear Campaign + Ad Set + Ad |
| `/performance-report` | Reporte de metricas con analisis y recomendaciones |
| `/validate-setup` | Diagnostico completo: .env, token, permisos, MCP, dependencias |
| `/optimize` | Analisis de campanas activas con recomendaciones ranked por impacto |

---

## Que Puedes Hacer (y Que No)

### SI puedes
- Crear campanas completas (Campaign + Ad Set + Ad) en PAUSED
- Subir imagenes y crear creativos
- Consultar metricas de cualquier periodo
- Buscar intereses, comportamientos, demograficos y ubicaciones para targeting
- Modificar ad sets (bidding, frequency caps, presupuesto)
- Activar/pausar campanas (con confirmacion)
- Programar presupuestos variables (budget schedules)
- Generar reportes con breakdowns (edad, genero, pais, placement)
- Obtener sugerencias de intereses para expandir audiencias
- Comparar periodos y detectar tendencias

### NO puedes (limitaciones actuales)
- Crear audiencias personalizadas (Custom Audiences) - requiere Business Manager UI
- Configurar pixel de Meta - se hace desde Events Manager
- Crear reglas automatizadas de Meta - se configuran en Ads Manager
- Gestionar permisos de Business Manager
- Crear lookalike audiences directamente
- Configurar catalogo de productos
- Gestionar billing y metodos de pago

---

## Configuracion Actual

```
Cuenta: act_3821209348158916 (iacondiego)
Pagina: 837897279401299 (Setterless 360)
Moneda: USD
Timezone: America/Santiago
API: v25.0
```

---

## Seguridad (Reglas No Negociables)

1. Todo se crea en **PAUSED** - nunca ACTIVE en creacion
2. Budget > $100/dia requiere **confirmacion explicita**
3. Presupuestos siempre en **centavos** ($50 = 5000)
4. Toda operacion de escritura se **loguea** en `logs/api_actions.log`
5. Writes fallidos **no se reintentan** automaticamente
6. Tokens y secrets **nunca se muestran** en pantalla

---

## Troubleshooting Rapido

| Problema | Solucion |
|----------|----------|
| Token expirado (error 190) | Generar nuevo token en Business Settings > System Users |
| Rate limit (error 17/80004) | Esperar 60 segundos, reducir frecuencia de requests |
| Sin permisos (error 10/200) | Verificar que el token tiene `ads_management` y `ads_read` |
| Validacion fallida (error 100) | Revisar parametros: act_ prefix, budget positivo, fechas ISO |
| MCP no conecta | Verificar `.mcp.json` y que META_ACCESS_TOKEN esta seteado |
| Token expira rapido | Usar System User token (no expira) en vez de user token |

---

## Flujo Tipico de Trabajo

```
1. /validate-setup              → Verificar que todo funciona
2. "dame un reporte last_7d"    → Entender estado actual
3. /new-campaign                → Crear nueva campana (PAUSED)
4. "activa la campana X"        → Activar con confirmacion
5. /performance-report          → Monitorear resultados
6. /optimize                    → Obtener recomendaciones
7. "pausa la campana X"         → Pausar si es necesario
```

---

## Recursos de Templates

### Targeting Presets (`templates/targeting-presets.json`)
- `us_broad` - USA 18-65, todos los generos
- `us_young_adults` - USA 18-34
- `latam_broad` - CL, AR, CO, MX, PE 18-55
- `spain_broad` - Espana 18-55
- `ecommerce_shoppers` - USA 25-54, intereses e-commerce

### Ad Copy Frameworks (`templates/ad-copy-templates.json`)
- **AIDA** - Attention, Interest, Desire, Action
- **PAS** - Problem, Agitation, Solution
- **BAB** - Before, After, Bridge
- **Social Proof** - Testimonios y numeros
- **Direct Offer** - Oferta directa con urgencia

ads_management
ads_read
business_management
catalog_management
manage_app_solution
pages_manage_ads
pages_read_engagement
pages_show_list
threads_business_basic
whatsapp_business_manage_events
whatsapp_business_management
whatsapp_business_messaging