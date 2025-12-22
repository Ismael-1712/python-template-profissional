---
id: cortex-dynamic-readme
type: reference
status: active
version: 1.0.0
author: Cortex Team
date: 2025-12-15
created: 2025-12-15
updated: 2025-12-15
linked_code:
  - scripts/core/cortex/readme_generator.py
  - scripts/cortex/cli.py
  - docs/templates/README.md.j2
tags:
  - cortex
  - documentation
  - automation
  - readme
  - jinja2
---

# 📄 Dynamic README Generation

## Visão Geral

O CORTEX implementa geração dinâmica do `README.md` através de templates Jinja2 e dados vivos do projeto. Isso garante que a documentação principal esteja sempre atualizada com métricas reais.

## Motivação

O README é o cartão de visitas do projeto, mas tende a ficar desatualizado rapidamente:

- **Versões hardcoded** ficam obsoletas
- **Métricas estáticas** não refletem a realidade
- **Health scores** precisam ser atualizados manualmente

**Solução**: Gerar o README automaticamente a partir de dados vivos.

## Arquitetura

### Fontes de Dados

O gerador extrai informações de múltiplas fontes:

| Fonte | Dados Extraídos |
|-------|----------------|
| `pyproject.toml` | Nome, versão, Python version, autores |
| `.cortex/context.json` | Estatísticas do knowledge graph |
| `docs/reports/KNOWLEDGE_HEALTH.md` | Health score e status |
| CLI introspection | Comandos disponíveis |

### Componentes

```
docs/templates/README.md.j2
    ↓ (Template Jinja2)
scripts/core/cortex/readme_generator.py
    ↓ (Extrai dados)
    ├── pyproject.toml
    ├── .cortex/context.json
    ├── docs/reports/KNOWLEDGE_HEALTH.md
    └── CLI commands
    ↓ (Renderiza)
README.md (GERADO)
```

### Código Principal

**Módulo**: `scripts/core/cortex/readme_generator.py`

**Classes**:

- `ReadmeGenerator`: Orquestrador principal
- `ProjectMetadata`: Dados do pyproject.toml
- `GraphStatistics`: Métricas do grafo de conhecimento
- `HealthScore`: Score de saúde da documentação
- `ReadmeData`: Agregador de todos os dados

**Métodos Principais**:

```python
ReadmeGenerator.extract_project_metadata() -> ProjectMetadata
ReadmeGenerator.extract_graph_statistics() -> GraphStatistics
ReadmeGenerator.extract_health_score() -> HealthScore
ReadmeGenerator.collect_all_data() -> ReadmeData
ReadmeGenerator.generate_readme(output_path) -> str
```

## Uso

### Comando CLI

```bash
# Gerar README.md (sobrescreve o existente)
cortex generate

# Preview sem escrever
cortex generate --dry-run

# Output customizado
cortex generate -o docs/README.md
```

### Output

```
🔨 CORTEX Dynamic README Generator
======================================================================

📊 Collecting data sources...

✓ Project Metadata:
  Name: meu_projeto_placeholder
  Version: 0.1.0
  Python: 3.10+

✓ Knowledge Graph:
  Nodes: 89
  Links: 246
  Connectivity: 78.5%

✓ Health Score:
  Score: 88.0/100
  Status: good

✓ CLI Commands:
  Found: 9 commands

🎨 Rendering template...

✅ SUCCESS!
📄 README generated: /home/user/project/README.md
📊 Size: 12045 bytes
📅 Generated at: 2025-12-15T11:04:27.219493
```

## Template Jinja2

**Arquivo**: `docs/templates/README.md.j2`

### Variáveis Disponíveis

```jinja2
{{ project.name }}              # Nome do projeto
{{ project.version }}           # Versão (ex: 0.1.0)
{{ project.python_version }}    # Python version (ex: 3.10+)
{{ project.description }}       # Descrição

{{ graph.total_nodes }}         # Total de nós no grafo
{{ graph.total_links }}         # Total de links
{{ graph.connectivity_score }}  # Score de conectividade (0-100)
{{ graph.broken_links }}        # Número de links quebrados

{{ health.score }}              # Health score (0-100)
{{ health.status }}             # Status: good/warning/critical
{{ health.generated_at }}       # Timestamp do relatório

{{ cli_commands }}              # Lista de comandos CLI
{{ generated_at }}              # Timestamp da geração
```

### Exemplo de Uso

```jinja2
# 🧠 {{ project.name | upper }}

**Version**: {{ project.version }}
**Python**: {{ project.python_version }}

## Health Score

Score: {{ health.score }}/100
Status: {% if health.status == 'critical' %}🔴{% elif health.status == 'warning' %}⚠️{% else %}🟢{% endif %}

## Knowledge Graph

- Nodes: {{ graph.total_nodes }}
- Links: {{ graph.total_links }}
- Connectivity: {{ "%.1f" | format(graph.connectivity_score) }}%
```

### Filtros Úteis

```jinja2
{# Formatação numérica #}
{{ "%.1f" | format(graph.connectivity_score) }}%

{# Inteiro #}
{{ health.score | int }}

{# Condicionais inline #}
{% if graph.broken_links > 0 %}🔴{% else %}🟢{% endif %}
```

## Integração com CI/CD

### Pre-commit Hook (Opcional)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: update-readme
        name: Update README
        entry: python -m scripts.cli.cortex generate
        language: system
        pass_filenames: false
```

### GitHub Actions

```yaml
# .github/workflows/update-readme.yml
name: Update README

on:
  push:
    branches: [main]
    paths:
      - 'pyproject.toml'
      - '.cortex/context.json'
      - 'docs/reports/KNOWLEDGE_HEALTH.md'

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate README
        run: |
          python -m scripts.cli.cortex generate
          git add README.md
          git commit -m "docs: auto-update README [skip ci]" || true
          git push
```

## Workflow Recomendado

1. **Desenvolvimento Local**:

   ```bash
   # Após mudanças significativas
   cortex map              # Atualiza context.json
   cortex audit --links    # Atualiza health score
   cortex generate         # Regenera README
   ```

2. **CI/CD**:
   - Gerar README automaticamente após merge
   - Validar que README está atualizado no PR

3. **Releases**:

   ```bash
   # Bump version em pyproject.toml
   vim pyproject.toml

   # Atualizar métricas
   cortex map
   cortex audit --links

   # Regenerar README
   cortex generate

   # Commit
   git add README.md pyproject.toml
   git commit -m "chore: release v0.2.0"
   ```

## Benefícios

### 1. Sempre Atualizado

- Versão sincronizada com `pyproject.toml`
- Métricas refletem estado real do projeto
- Health score atualizado automaticamente

### 2. Reduz Manutenção

- Elimina edições manuais repetitivas
- Consistência garantida
- Menos erros humanos

### 3. Transparência

- Badges dinâmicos mostram saúde real
- Timestamp de geração visível
- Rastreabilidade total

### 4. Extensível

- Fácil adicionar novas métricas
- Template customizável
- Múltiplos outputs possíveis

## Troubleshooting

### Erro: Template não encontrado

```
FileNotFoundError: docs/templates/README.md.j2
```

**Solução**: Certifique-se de que o template existe:

```bash
ls -la docs/templates/README.md.j2
```

### Erro: context.json não existe

```
Metrics show: Nodes: 0, Links: 0
```

**Solução**: Gere o contexto primeiro:

```bash
cortex map
```

### Erro: Jinja2 não instalado

```
ModuleNotFoundError: No module named 'jinja2'
```

**Solução**: Instale as dependências de dev:

```bash
pip install -e ".[dev]"
```

## Próximos Passos

### Fase 4.1: Templates Múltiplos

- `README_TECHNICAL.md.j2`: Para desenvolvedores
- `README_USER.md.j2`: Para usuários finais
- `CONTRIBUTING.md.j2`: Guia de contribuição dinâmico

### Fase 4.2: Métricas Avançadas

- Cobertura de testes automática
- Análise de dependências
- Performance benchmarks

### Fase 4.3: Internacionalização

- `README_pt_BR.md.j2`
- `README_en_US.md.j2`
- Seleção automática de idioma

## Referências

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [PEP 621 - pyproject.toml](https://peps.python.org/pep-0621/)
- [CORTEX Knowledge Graph](./CORTEX_FASE03_DESIGN.md)

---

**Implementado em**: Sprint 5 - Fase 4
**Autor**: Engineering Team
**Status**: ✅ Production Ready
