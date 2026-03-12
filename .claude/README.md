# Meta Ads Agent - .claude/ Assets

## Comandos Disponibles

| Comando | Descripcion |
|---------|-------------|
| `/new-campaign` | Creacion guiada de campana (Campaign + Ad Set + Ad) |
| `/performance-report` | Reporte de performance con recomendaciones |
| `/validate-setup` | Verificar conexion API, token, permisos |
| `/optimize` | Recomendaciones de optimizacion basadas en datos |

## Skills

| Skill | Proposito |
|-------|-----------|
| `meta-ads` | Gestion completa de Meta Marketing API |
| `skill-creator` | Crear nuevas skills |

## Agentes

Los agentes en `agents/` pueden adaptarse para operaciones especificas de Meta Ads.

## PRPs

Template base en `PRPs/prp-base.md` para definir features complejas.

## Prompts

- `bucle-agentico-blueprint.md` - Proceso por fases para implementar features
- `bucle-agentico-sprint.md` - Sprint pattern para tareas menores

## Estructura

```
.claude/
├── commands/         # Comandos slash
│   ├── new-campaign.md
│   ├── performance-report.md
│   ├── validate-setup.md
│   └── optimize.md
├── agents/           # Agentes especializados
├── prompts/          # Metodologias
├── PRPs/             # Product Requirements
└── skills/
    ├── meta-ads/     # Skill principal
    └── skill-creator/
```
