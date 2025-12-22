---
title: "Sistema de Introspecção Dinâmica CORTEX"
type: guide
id: cortex-introspection-system
version: "1.0.0"
date: "2025-12-01"
author: Engineering Team
status: active
tags:
  - cortex
  - introspection
  - automation
  - llm
related_docs:
  - docs/architecture/CORTEX_INDICE.md
  - .github/copilot-instructions.md
---

# Sistema de Introspecção Dinâmica CORTEX

## Visão Geral

Este documento descreve o sistema de introspecção dinâmica do CORTEX, que permite
que ferramentas de automação (como LLMs) descubram a estrutura e capacidades do
projeto sem depender de regras hardcoded.

## Motivação

**Problema**: Templates de projeto precisam ser genéricos, mas as instruções para
LLMs frequentemente assumem arquiteturas específicas.

**Solução**: Sistema de introspecção que gera um mapa dinâmico do projeto, permitindo
que as ferramentas descubram a estrutura atual em vez de presumir.

## Componentes

### 1. Instruções Agnósticas (`.github/copilot-instructions.md`)

Arquivo de instruções perpétuas que **não assume nada** sobre a arquitetura do projeto:

- ✅ Consulte `docs/architecture/` para entender a topologia
- ✅ Use `cortex map` para descobrir comandos disponíveis
- ✅ Verifique o estado do Git antes de sugerir operações
- ❌ Não presuma a existência de branches específicos
- ❌ Não presuma padrões arquiteturais (como "Tríade")

### 2. Comando de Mapeamento (`cortex map`)

Gera um arquivo JSON com o contexto completo do projeto:

```bash
# Gerar mapa de contexto
cortex map

# Com saída detalhada
cortex map --verbose

# Caminho customizado
cortex map --output custom/path.json
```

### 3. Arquivo de Contexto (`.cortex/context.json`)

JSON gerado dinamicamente contendo:

```json
{
  "project_name": "nome-do-projeto",
  "version": "1.0.0",
  "python_version": ">=3.10",
  "cli_commands": [
    {
      "name": "cortex",
      "script_path": "scripts/cortex/cli.py",
      "description": "CORTEX - Documentation as Code CLI"
    }
  ],
  "documents": [...],
  "architecture_docs": [...],
  "dependencies": [...],
  "dev_dependencies": [...],
  "scripts_available": {
    "cortex": "scripts.cli.cortex:main",
    "dev-doctor": "scripts.cli.doctor:main"
  }
}
```

## Fluxo de Trabalho

### Para LLMs/Copilot

1. **Introspecção Primeiro**

   ```bash
   cortex map
   cat .cortex/context.json
   ```

2. **Consultar Arquitetura**
   - Ler documentos listados em `architecture_docs`
   - Entender padrões do projeto atual

3. **Verificar Capacidades**
   - Comandos disponíveis em `cli_commands`
   - Scripts instaláveis em `scripts_available`

4. **Agir com Contexto**
   - Usar informações descobertas
   - Não fazer suposições

### Para Desenvolvedores

1. **Após mudanças estruturais**

   ```bash
   cortex map
   ```

2. **Antes de commitar instruções customizadas**
   - Verificar se a instrução é genérica ou específica
   - Instruções específicas vão em `.github/copilot-instructions-custom.md`

3. **Em projetos derivados**
   - O template vem com instruções agnósticas
   - Adicione customizações sem modificar as instruções base

## Extensibilidade

### Adicionando Nova Fonte de Contexto

Para adicionar nova informação ao mapa de contexto:

1. Edite `scripts/core/cortex/mapper.py`
2. Adicione campo em `ProjectContext` dataclass
3. Implemente método de escaneamento em `ProjectMapper`
4. Atualize este documento

Exemplo:

```python
@dataclass
class ProjectContext:
    # ... campos existentes ...

    # Nova fonte de contexto
    custom_configs: list[dict] = field(default_factory=list)

class ProjectMapper:
    def map_project(self) -> ProjectContext:
        # ... lógica existente ...

        # Escanear nova fonte
        context.custom_configs = self._scan_custom_configs()
        return context

    def _scan_custom_configs(self) -> list[dict]:
        # Implementar escaneamento
        pass
```

### Adicionando Instruções Customizadas

Para projetos derivados com necessidades específicas:

1. Crie `.github/copilot-instructions-custom.md`
2. Adicione instruções específicas do projeto
3. Referencie o contexto dinâmico:

   ```markdown
   De acordo com `.cortex/context.json`, este projeto usa...
   ```

## Princípios de Design

1. **Sem Suposições**: Nunca hardcode padrões arquiteturais
2. **Descoberta Dinâmica**: Todas as informações são descobertas em runtime
3. **Volátil por Design**: O contexto é local e regenerado conforme necessário
4. **Extensível**: Fácil adicionar novas fontes de contexto
5. **Agnóstico**: Funciona independente da arquitetura do projeto

## Casos de Uso

### ✅ Cenário 1: Projeto com Arquitetura Customizada

```bash
# Projeto derivado usa padrão hexagonal em vez de Tríade
cortex map

# .cortex/context.json reflete a estrutura atual
# LLM lê e adapta suas sugestões
```

### ✅ Cenário 2: Novos Comandos CLI

```bash
# Desenvolvedor adiciona novo comando
# LLM executa cortex map e descobre automaticamente
cortex map --verbose
# Saída mostra novo comando disponível
```

### ✅ Cenário 3: Documentação Arquitetural

```bash
# LLM não sabe qual arquitetura está sendo usada
cortex map
cat .cortex/context.json | jq '.architecture_docs'
# Descobre documentos relevantes e os lê
```

## Integração com CI/CD

### Validação de Contexto

Adicione ao pipeline:

```yaml
- name: Validate Context
  run: |
    cortex map
    test -f .cortex/context.json
    # Validar schema do JSON se necessário
```

### Auditoria de Introspecção

Verifique se as instruções permanecem agnósticas:

```bash
# Detectar hardcoding nas instruções
grep -r "Tríade\|src/api\|develop branch" .github/copilot-instructions.md
# Deve retornar vazio
```

## Limitações Conhecidas

1. **Performance**: Escaneamento pode ser lento em projetos grandes
   - Solução: Cache inteligente (futuro)

2. **Contexto Estático**: JSON não reflete mudanças em tempo real
   - Solução: Regenerar após mudanças estruturais

3. **Sem Validação Semântica**: Mapa não valida coerência arquitetural
   - Solução: Ferramentas de linting arquitetural (futuro)

## Próximos Passos

- [ ] Cache inteligente para performance
- [ ] Validação de schema do context.json
- [ ] Integração com `dev-doctor` para diagnóstico
- [ ] Suporte para múltiplos formatos de saída (YAML, TOML)
- [ ] API programática para consumir contexto

## Referências

- `.github/copilot-instructions.md` - Instruções agnósticas
- `scripts/core/cortex/mapper.py` - Implementação do mapper
- `scripts/cortex/cli.py` - CLI do CORTEX
- `.cortex/context.json` - Contexto gerado (volátil)

---

**Status**: ✅ Implementado e funcional
**Versão**: 1.0
**Última Atualização**: 2025-12-01
