---
id: knowledge-node-manual
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-12-12
context_tags:
  - knowledge-base
  - guardian
  - documentation
  - cortex
linked_code:
  - scripts/core/cortex/knowledge_scanner.py
  - scripts/core/cortex/knowledge_sync.py
  - scripts/core/guardian/hallucination_probe.py
  - scripts/cli/cortex.py
---

# 📚 Knowledge Node Manual

> **Guia Completo do Sistema de Knowledge Nodes**
>
> Aprenda como criar, gerenciar e validar nós de conhecimento que conectam
> documentação externa ao seu projeto.

## 🎯 O Que É um Knowledge Node?

Um **Knowledge Node** (Nó de Conhecimento) é um documento Markdown que atua como
uma ponte entre seu código e fontes externas de conhecimento. Ele resolve o
problema de **documentação fragmentada** ao consolidar referências, validações
e caminhos críticos ("Golden Paths") em um único lugar.

### Por Que Usar Knowledge Nodes?

✅ **Rastreabilidade:** Links bidirecionais entre código e documentação externa
✅ **Validação:** Sistema de canários detecta documentação perdida ou corrompida
✅ **Sincronização:** Atualização automática de conteúdo de fontes externas
✅ **Governança:** Metadados estruturados garantem qualidade e consistência

### Exemplo de Caso de Uso

```yaml
# Cenário: Você está usando uma API de terceiros
# Problema: A documentação oficial muda com frequência
# Solução: Criar um Knowledge Node que:
#   1. Mantém cache local da documentação
#   2. Sincroniza automaticamente com a fonte
#   3. Valida se o código ainda aponta para as mesmas APIs
```

---

## 📖 Anatomia de um Knowledge Node

Um Knowledge Node é um arquivo Markdown com **frontmatter YAML estruturado**.
Aqui está a anatomia completa:

```markdown
---
id: kno-example-001              # Identificador único (obrigatório)
status: active                    # Estado: active | draft | deprecated
version: 1.0.0                    # Versionamento semântico
author: Engineering Team          # Autor ou time responsável
date: 2025-12-12                  # Data de criação
context_tags:                     # Tags de classificação
  - api-integration
  - external-docs
sources:                          # URLs de fontes externas
  - url: https://api.example.com/docs/v1
    title: "Example API v1 Documentation"
    last_synced: "2025-12-12T10:00:00Z"
golden_paths:                     # Caminhos críticos no código
  - src/api/example_client.py
  - tests/integration/test_example_api.py
---

# 🌐 Example API Integration

Este Knowledge Node documenta a integração com a API Example v1.

## 🔗 Referências Críticas

- **Endpoint Base:** `https://api.example.com/v1`
- **Autenticação:** OAuth 2.0
- **Rate Limits:** 1000 req/hora

## 📍 Golden Paths

Os seguintes arquivos dependem desta documentação:
- `src/api/example_client.py`: Cliente HTTP principal
- `tests/integration/test_example_api.py`: Testes de integração
```

---

## 🛠️ Tutorial: Criando Seu Primeiro Knowledge Node

### Passo 1: Criar o Arquivo

```bash
# Crie um arquivo na pasta docs/knowledge/
touch docs/knowledge/my-first-knowledge-node.md
```

### Passo 2: Adicionar o Frontmatter

Use o comando `cortex init` para gerar o frontmatter automaticamente:

```bash
cortex init docs/knowledge/my-first-knowledge-node.md
```

Ou crie manualmente:

```yaml
---
id: kno-my-integration-001
status: active
version: 1.0.0
author: Seu Nome
date: 2025-12-12
context_tags:
  - integration
sources:
  - url: https://docs.external-api.com/guide
    title: "External API Guide"
golden_paths:
  - src/integrations/external_api.py
---
```

### Passo 3: Adicionar Conteúdo

Escreva a documentação abaixo do frontmatter:

```markdown
# 🔌 External API Integration

## 📝 Overview
Este nó documenta a integração com a External API.

## 🚀 Quick Start
\```python
from src.integrations.external_api import ExternalClient

client = ExternalClient(api_key="...")
response = client.fetch_data()
\```

## ⚠️ Notas Importantes
- A API requer autenticação via token
- Rate limit: 500 requisições/minuto
```

### Passo 4: Validar

Escaneie o Knowledge Base para validar:

```bash
cortex knowledge-scan --verbose
```

**Saída esperada:**

```
🧠 Knowledge Base Scanner
Workspace: /home/user/project
Knowledge Directory: docs/knowledge/

✅ Found 1 knowledge entry

✅ kno-my-integration-001 (active)
   Tags: integration
   Golden Paths: ['src/integrations/external_api.py']
   Sources: 1 reference(s)
```

---

## 🎮 Comandos da CLI

### `cortex knowledge-scan`

Escaneia e valida todos os Knowledge Nodes no diretório `docs/knowledge/`.

```bash
# Escaneamento simples
cortex knowledge-scan

# Com detalhes verbosos
cortex knowledge-scan --verbose
```

**O que valida:**

- ✅ Frontmatter YAML válido
- ✅ Campos obrigatórios presentes (`id`, `status`)
- ✅ Status válido (active, draft, deprecated)
- ✅ Estrutura de sources e golden_paths

---

### `cortex knowledge-sync`

Sincroniza Knowledge Nodes com fontes externas, baixando conteúdo e
atualizando metadados de cache.

```bash
# Sincronizar todos os entries
cortex knowledge-sync

# Sincronizar entry específico
cortex knowledge-sync --entry-id kno-001

# Preview sem gravar (dry-run)
cortex knowledge-sync --dry-run
```

**O que faz:**

1. Busca conteúdo das URLs em `sources`
2. Mescla com conteúdo local preservando Golden Paths
3. Atualiza `last_synced` e `etag` no frontmatter
4. Grava as mudanças em disco (exceto em dry-run)

**Exemplo de uso:**

```bash
$ cortex knowledge-sync --entry-id kno-api-001

🔄 Knowledge Synchronizer
Workspace: /home/user/project
Target Entry: kno-api-001

📡 Syncing kno-api-001...
   Source: https://api.example.com/docs/v1
   ✅ Synced successfully (last_synced: 2025-12-12T14:30:00Z)

✅ Synchronization complete: 1 entries processed
```

---

### `cortex guardian-probe`

Executa o **Hallucination Probe** (Teste do Canário) para verificar a
integridade do sistema de Knowledge Nodes.

```bash
# Teste simples
cortex guardian-probe

# Teste com canário customizado
cortex guardian-probe --canary-id kno-002

# Validação detalhada
cortex guardian-probe --verbose
```

**O que é o Hallucination Probe?**

O Probe implementa o padrão "Needle Test": injeta um entry canário conhecido
(por padrão `kno-001`) e verifica se o sistema consegue encontrá-lo e validá-lo.
Se o canário **morrer** (não for encontrado), significa que:

- 🔴 O sistema está "alucinando" (retornando dados incorretos)
- 🔴 O scanner não está funcionando corretamente
- 🔴 Há corrupção no Knowledge Base

**Exemplo de saída (sucesso):**

```bash
$ cortex guardian-probe

🔍 Hallucination Probe
Workspace: /home/user/project
Target Canary: kno-001

✅ System healthy - canary 'kno-001' found and active

💡 Tip: Use --verbose for detailed validation info
```

**Exemplo de saída (falha):**

```bash
$ cortex guardian-probe

🔍 Hallucination Probe
Workspace: /home/user/project
Target Canary: kno-001

❌ System check failed - canary 'kno-001' not found or inactive

⚠️  WARNING: Knowledge system may be hallucinating!
   - Verify that docs/knowledge/kno-001.md exists
   - Check that the entry has status: active
   - Run 'cortex knowledge-scan' to see all entries
```

---

## 🔧 Troubleshooting

### ❓ "O canário morreu" - Probe falhou

**Sintoma:**

```bash
❌ System check failed - canary 'kno-001' not found or inactive
```

**Diagnóstico:**

```bash
# 1. Verifique se o arquivo existe
ls -la docs/knowledge/kno-001.md

# 2. Valide o frontmatter
cortex knowledge-scan --verbose

# 3. Verifique o status
cat docs/knowledge/kno-001.md | head -20
```

**Solução:**

1. Se o arquivo não existe, crie um canário:

   ```bash
   cp docs/knowledge/example-kno-001.md docs/knowledge/kno-001.md
   ```

2. Se o status está errado, edite o frontmatter:

   ```yaml
   status: active  # Deve ser 'active', não 'draft' ou 'deprecated'
   ```

3. Se o frontmatter está inválido, use `cortex init --force`:

   ```bash
   cortex init docs/knowledge/kno-001.md --force
   ```

---

### ❓ Knowledge-sync falha ao baixar fonte externa

**Sintoma:**

```bash
❌ Failed: HTTP Error 404: Not Found
```

**Diagnóstico:**

```bash
# Teste a URL manualmente
curl -I "https://api.example.com/docs/v1"
```

**Solução:**

1. **URL expirada/movida:** Atualize a URL no frontmatter
2. **Requer autenticação:** Adicione headers (feature futura)
3. **Temporariamente offline:** Use `--dry-run` para skip ou tente novamente

---

### ❓ Golden Path aponta para arquivo inexistente

**Sintoma:**
O scanner reporta golden paths, mas os arquivos não existem no repositório.

**Solução:**

```bash
# 1. Verifique quais paths estão listados
cortex knowledge-scan --verbose | grep "Golden Paths"

# 2. Atualize o frontmatter removendo paths obsoletos
# Edite o arquivo manualmente ou use editor:
vim docs/knowledge/kno-xxx.md

# 3. Valide novamente
cortex knowledge-scan
```

---

### ❓ Muitos Knowledge Nodes com status 'draft'

**Sintoma:**

```bash
📝 kno-001 (draft)
📝 kno-002 (draft)
```

**Solução:**

Os drafts não são sincronizados nem validados rigidamente. Para promover a active:

```bash
# Edite cada arquivo manualmente
sed -i 's/status: draft/status: active/' docs/knowledge/kno-*.md

# Ou use um script
for file in docs/knowledge/kno-*.md; do
  sed -i 's/status: draft/status: active/' "$file"
done

# Valide
cortex knowledge-scan
```

---

## 🏗️ Arquitetura e Design

### Componentes do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    Knowledge System                     │
├─────────────────────────────────────────────────────────┤
│  1. KnowledgeScanner    → Scans docs/knowledge/*.md    │
│  2. KnowledgeSyncer     → Syncs with external sources  │
│  3. HallucinationProbe  → Validates system integrity   │
│  4. CLI Commands        → User interface (cortex)      │
└─────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

```
1. Usuário cria Knowledge Node (kno-xyz.md)
       ↓
2. `cortex knowledge-scan` valida frontmatter
       ↓
3. `cortex knowledge-sync` baixa conteúdo externo
       ↓
4. Sistema mescla conteúdo local + externo
       ↓
5. `cortex guardian-probe` valida canário
       ↓
6. ✅ Knowledge Base íntegro e sincronizado
```

### Modelos de Dados

Os Knowledge Nodes seguem o modelo `KnowledgeEntry`:

```python
@dataclass
class KnowledgeEntry:
    id: str                        # Identificador único
    file_path: Path                # Caminho do arquivo
    status: DocStatus              # active | draft | deprecated
    golden_paths: list[str]        # Caminhos críticos no código
    tags: list[str]                # Tags de classificação
    sources: list[ExternalSource]  # Fontes externas
    cached_content: str | None     # Cache do conteúdo baixado
    last_synced: datetime | None   # Timestamp da última sincronização
```

---

## 📚 Referências

### Documentação Relacionada

- [CORTEX_INDICE.md](../architecture/CORTEX_INDICE.md) - Índice geral do sistema CORTEX
- [VISIBILITY_GUARDIAN_DESIGN.md](../architecture/VISIBILITY_GUARDIAN_DESIGN.md) - Design do Visibility Guardian
- [ENGINEERING_STANDARDS.md](./ENGINEERING_STANDARDS.md) - Padrões de engenharia

### Código-Fonte

- [scripts/core/cortex/knowledge_scanner.py](../../scripts/core/cortex/knowledge_scanner.py)
- [scripts/core/cortex/knowledge_sync.py](../../scripts/core/cortex/knowledge_sync.py)
- [scripts/core/guardian/hallucination_probe.py](../../scripts/core/guardian/hallucination_probe.py)
- [scripts/cli/cortex.py](../../scripts/cli/cortex.py)

### Testes

- [tests/test_knowledge_scanner.py](../../tests/test_knowledge_scanner.py)
- [tests/test_knowledge_sync.py](../../tests/test_knowledge_sync.py)
- [tests/test_guardian_scanner.py](../../tests/test_guardian_scanner.py)

---

## 🎓 Best Practices

### ✅ Faça

1. **Use IDs semânticos:** `kno-api-auth-001` é melhor que `kno-123`
2. **Mantenha Golden Paths atualizados:** Valide regularmente se os arquivos existem
3. **Sincronize periodicamente:** Execute `cortex knowledge-sync` em CI/CD
4. **Use tags consistentes:** Defina taxonomia de tags (ex: `api`, `integration`, `deprecated`)
5. **Documente fontes:** Sempre adicione `title` e `url` completos

### ❌ Não Faça

1. **Não deixe drafts permanentes:** Promova para `active` ou delete
2. **Não ignore canários mortos:** Se o probe falha, investigue imediatamente
3. **Não use URLs relativas:** Sempre URLs absolutas em `sources`
4. **Não duplique conhecimento:** Um conceito = um Knowledge Node
5. **Não pule validação:** Sempre rode `knowledge-scan` após edições manuais

---

## 🚀 Próximos Passos

Agora que você domina o Knowledge Node System:

1. **Crie seu primeiro node:** Siga o tutorial acima
2. **Configure CI/CD:** Adicione `cortex guardian-probe` ao pipeline
3. **Estabeleça governança:** Defina quem pode criar/editar nodes
4. **Automatize sincronização:** Agende `knowledge-sync` diariamente
5. **Explore extensões:** Considere adicionar webhooks de sincronização

---

## 📞 Suporte

Encontrou um bug ou tem dúvidas?

- **Issues:** [GitHub Issues](https://github.com/seu-repo/issues)
- **Docs:** [Documentação Completa](../README.md)
- **Logs:** Verifique `.cortex/cortex.log` para detalhes técnicos

---

**Versão:** 1.0.0
**Última Atualização:** 2025-12-12
**Autores:** Engineering Team
