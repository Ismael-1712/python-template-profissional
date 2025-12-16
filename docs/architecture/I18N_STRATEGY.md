---
id: i18n-strategy
type: arch
status: active
version: 1.0.0
author: GEM & SRE Team
date: '2025-12-16'
tags: [internationalization, i18n, gettext, babel, localization]
context_tags: [architecture, user-experience, globalization]
linked_code:
  - scripts/audit/reporter.py
  - scripts/audit_dashboard/cli.py
  - scripts/audit_dashboard/exporters.py
  - scripts/ci_recovery/main.py
  - scripts/cli/install_dev.py
  - scripts/smart_git_sync.py
title: 'Internationalization Strategy - GNU gettext & Babel Architecture'
---

# 🌍 Internationalization Strategy - GNU gettext & Babel Architecture

## Status

**Active** - Sistema bilíngue nativo (pt-BR + en-US) validado durante Sprint 4 (P28 - Nov 2025)

## Contexto e Motivação

### O Problema: Monolinguismo Hardcoded

No início do projeto, o sistema sofria de **Dívida Técnica de Internacionalização**:

- **Strings de UI Hardcoded**: Mensagens de usuário misturadas com lógica de negócio (violação de SoC - Separation of Concerns)
- **Português único**: O sistema falava apenas pt-BR, limitando adoção internacional
- **Sem infraestrutura i18n**: Modificar idiomas requeria refatoração massiva de código

#### Impacto Operacional

```python
# ❌ ANTES: Strings hardcoded (não traduzível)
print(f"Processando {count} arquivos...")
logger.info("Auditoria concluída com sucesso")

# ✅ DEPOIS: Strings externalizadas (traduzível via gettext)
print(_("Processando {} arquivos...").format(count))
logger.info(_("Auditoria concluída com sucesso"))
```

### A Solução: GNU gettext + Babel

Durante o **Sprint 4 (Tarefa P28)**, implementamos infraestrutura de i18n de nível empresarial baseada no padrão **GNU gettext**, gerenciada pela biblioteca **Babel**.

---

## Arquitetura da Solução

### Componentes Principais

```mermaid
graph TD
    A[Código Fonte Python] -->|1. Marca strings| B[_\('Texto'\)]
    B -->|2. pybabel extract| C[locales/messages.pot]
    C -->|3. pybabel init/update| D[locales/en_US/LC_MESSAGES/messages.po]
    C -->|3. pybabel init/update| E[locales/pt_BR/LC_MESSAGES/messages.po]
    D -->|4. pybabel compile| F[messages.mo - Binário EN]
    E -->|4. pybabel compile| G[messages.mo - Binário PT]

    H[Runtime: LANGUAGE=en_US] --> I[gettext.translation\(...\)]
    I --> F
    I --> J[_ = translation.gettext]
    J --> K[Texto traduzido exibido]

    style C fill:#e1f5ff
    style F fill:#c8e6c9
    style G fill:#c8e6c9
    style K fill:#fff4e1
```

### 1️⃣ Extração de Strings (Source → Template)

**Arquivo:** `babel.cfg` (configuração de extração)

```ini
[python: **.py]
encoding = utf-8
```

**Comando:**

```bash
make i18n-extract
# Executa: pybabel extract -F babel.cfg -o locales/messages.pot .
```

**Saída:** `locales/messages.pot` (template com todas as strings traduzíveis)

```pot
#: scripts/audit/reporter.py:51
msgid "🔍 CODE SECURITY AUDIT REPORT"
msgstr ""

#: scripts/audit/reporter.py:93
#, python-brace-format
msgid "📄 Files Scanned: {count}"
msgstr ""
```

### 2️⃣ Inicialização de Catálogos (Template → Locales)

**Para novo idioma:**

```bash
make i18n-init LOCALE=en_US
# Executa: pybabel init -i locales/messages.pot -d locales -l en_US
```

**Saída:** `locales/en_US/LC_MESSAGES/messages.po`

**Para atualizar catálogos existentes:**

```bash
make i18n-update
# Executa: pybabel update -i locales/messages.pot -d locales
```

### 3️⃣ Tradução (Manual)

Editores traduzem os arquivos `.po`:

```po
#: scripts/audit/reporter.py:51
msgid "🔍 CODE SECURITY AUDIT REPORT"
msgstr "🔍 CODE SECURITY AUDIT REPORT"

#: scripts/audit/reporter.py:93
#, python-brace-format
msgid "📄 Files Scanned: {count}"
msgstr "📄 Files Scanned: {count}"
```

### 4️⃣ Compilação (PO → MO Binário)

```bash
make i18n-compile
# Executa: pybabel compile -d locales
```

**Saída:** `locales/en_US/LC_MESSAGES/messages.mo` (binário otimizado para runtime)

### 5️⃣ Uso em Runtime

**Pattern Standard (usado em todos os scripts):**

```python
import gettext
import os
from pathlib import Path

# Setup i18n
_locale_dir = Path(__file__).parent.parent.parent / "locales"
try:
    _translation = gettext.translation(
        "messages",
        localedir=str(_locale_dir),
        languages=[os.getenv("LANGUAGE", "pt_BR")],  # Default: pt-BR
        fallback=True,  # Se locale não encontrado, usa strings originais
    )
    _ = _translation.gettext
except Exception:
    # Fallback se gettext não disponível
    def _(message: str) -> str:
        return message

# Uso
logger.info(_("🚀 Starting Smart Git Synchronization"))
print(_("Found {count} changes to process").format(count=len(changes)))
```

**Variável de Ambiente:**

```bash
# Rodar em inglês
LANGUAGE=en_US python scripts/cli/git_sync.py

# Rodar em português (default)
python scripts/cli/git_sync.py
```

---

## Padrões de Implementação

### ✅ DO: Padrão Recomendado

```python
# 1. Strings simples
print(_("Auditoria concluída"))

# 2. Strings com substituição
logger.info(_("Processando {} arquivos").format(count))

# 3. Strings multilinhas
msg = _(
    "\n"
    "📊 SEVERITY DISTRIBUTION:"
)
print(msg)

# 4. Strings com emojis (preservados)
print(_("✅ Validation PASSED"))
```

### ❌ DON'T: Anti-Padrões

```python
# ❌ ERRADO: f-strings não são extraídas pelo gettext
print(_(f"Processando {count} arquivos"))  # gettext não detecta variáveis

# ❌ ERRADO: Concatenação dentro de _()
print(_("Total: " + str(count)))  # Tradutores veem string quebrada

# ❌ ERRADO: Strings não marcadas
print("Auditoria concluída")  # Nunca será traduzido

# ✅ CORRETO
print(_("Processando {} arquivos").format(count))
print(_("Total: {}").format(count))
```

---

## Cobertura Atual

### Módulos Internacionalizados (100% UI crítica)

| Módulo | Arquivo | Strings Traduzíveis | Status |
|--------|---------|---------------------|--------|
| **Audit Reporter** | `scripts/audit/reporter.py` | 12 | ✅ Completo |
| **Audit Dashboard** | `scripts/audit_dashboard/` | 18 | ✅ Completo |
| **CI Recovery** | `scripts/ci_recovery/main.py` | 8 | ✅ Completo |
| **Git Sync** | `scripts/smart_git_sync.py` | 25 | ✅ Completo |
| **Install Dev** | `scripts/cli/install_dev.py` | 6 | ✅ Completo |

**Total:** ~70 strings extraídas no catálogo `messages.pot`

### Idiomas Suportados

- 🇧🇷 **Português (pt_BR)**: Idioma padrão, 100% completo (código-fonte nativo)
- 🇺🇸 **Inglês (en_US)**: 100% traduzido e compilado

---

## Fluxo de Trabalho para Desenvolvedores

### Ao Adicionar Novas Strings de UI

1. **Instrumentação:**

   ```python
   # Sempre use _("...") para strings visíveis ao usuário
   print(_("Sua nova mensagem aqui"))
   ```

2. **Extração:**

   ```bash
   make i18n-extract
   ```

3. **Atualização de Catálogos:**

   ```bash
   make i18n-update
   ```

4. **Tradução Manual:**

   Edite `locales/en_US/LC_MESSAGES/messages.po` e adicione tradução:

   ```po
   msgid "Sua nova mensagem aqui"
   msgstr "Your new message here"
   ```

5. **Compilação:**

   ```bash
   make i18n-compile
   ```

6. **Validação:**

   ```bash
   # Testar em inglês
   LANGUAGE=en_US python seu_script.py

   # Testar em português
   python seu_script.py
   ```

7. **Commit:**

   ```bash
   git add locales/ babel.cfg
   git commit -m "i18n: add translations for new feature X"
   ```

### Verificação de Cobertura

```bash
# Ver estatísticas de tradução
make i18n-stats

# Saída exemplo:
# 📄 locales/en_US/LC_MESSAGES/messages.po:
# 70 translated messages, 0 fuzzy, 0 untranslated
```

---

## Observabilidade e Debugging

### Logs de Inicialização

**Apenas `smart_git_sync.py` anuncia o locale carregado** (outros scripts são silenciosos):

```python
logger.info("🌐 Current Locale: %s", os.getenv("LANGUAGE", "pt_BR"))
```

**Débito Técnico Conhecido:**

> Outros scripts (`audit_dashboard.py`, `ci_recovery/main.py`) não anunciam o locale no log de inicialização. Isso é uma **prioridade baixa** mas pode dificultar troubleshooting de problemas de i18n.

**Recomendação Futura:**

Padronizar logging de locale em todos os entry points:

```python
logger.info("🌐 Locale: %s | Translations: %s",
            os.getenv("LANGUAGE", "pt_BR"),
            "loaded" if _translation else "fallback")
```

---

## Testes e Qualidade

### Estratégia de Testes de i18n

**Problema:** Testes devem ser **determinísticos** independente do locale do sistema.

**Solução:** Mock da função `_()` nos testes:

```python
# Exemplo: tests/test_reporter.py
@pytest.fixture(autouse=True)
def mock_translation() -> Generator[None, None, None]:
    """Mock i18n para garantir testes determinísticos."""
    with patch("scripts.audit.reporter._", side_effect=lambda x: x):
        yield

def test_format_structure(sample_report: dict[str, Any]) -> None:
    """Teste valida estrutura sem depender de traduções."""
    formatter = ConsoleAuditFormatter()
    output = formatter.format(sample_report)
    assert "CODE SECURITY AUDIT REPORT" in output  # String original
```

**Benefícios:**

- ✅ Testes passam em qualquer locale do sistema
- ✅ Assertions validam chaves de tradução (não valores traduzidos)
- ✅ Mudanças em traduções não quebram testes

### Validação de Traduções

```python
def test_i18n_preservation(sample_report: dict[str, Any]) -> None:
    """Valida que funções de tradução são chamadas."""
    with patch("scripts.audit.reporter._") as mock_gettext:
        mock_gettext.side_effect = lambda x: f"[[{x}]]"

        formatter = ConsoleAuditFormatter()
        output = formatter.format(sample_report)

        # Verifica que _() foi chamado com strings corretas
        mock_gettext.assert_any_call("🔍 CODE SECURITY AUDIT REPORT")
        mock_gettext.assert_any_call("\n📊 SEVERITY DISTRIBUTION:")
```

---

## Performance e Overhead

### Custo de Runtime

- **Compilação (`.mo`)**: Binários otimizados, lookup O(1) via hash table
- **Overhead de `_()`**: ~1-5 microsegundos por string (negligível)
- **Memory footprint**: ~20KB por locale (catálogo `messages.mo`)

**Conclusão:** Impacto de performance é desprezível mesmo em scripts críticos (CI/CD).

### Otimizações Aplicadas

1. **Compilação Obrigatória:** `.po` não é lido em runtime, apenas `.mo` compilado
2. **Fallback Graceful:** Se locale não encontrado, usa strings originais (sem crash)
3. **Lazy Loading:** `gettext.translation()` carrega apenas o locale solicitado

---

## Roadmap e Próximos Passos

### Melhorias Futuras (Prioridade Baixa)

- [ ] **Locale Announcement:** Adicionar logging de locale em todos os entry points
- [ ] **Suporte a Plurais:** Implementar `ngettext()` para strings com plural
  ```python
  # Futuro
  print(ngettext(
      "Processando {} arquivo",
      "Processando {} arquivos",
      count
  ).format(count))
  ```
- [ ] **Locale Automático:** Detectar locale do sistema (não apenas `LANGUAGE` env var)
  ```python
  import locale
  system_locale = locale.getdefaultlocale()[0]  # Ex: 'pt_BR'
  ```
- [ ] **Novos Idiomas:** Adicionar `fr_FR`, `es_ES` se demanda existir

### Melhorias Imediatas (Prioridade Baixa)

Nenhuma ação crítica necessária. O sistema atual é **production-ready** e cobre 100% da UI.

---

## Referências Técnicas

### Documentação Oficial

- [GNU gettext Manual](https://www.gnu.org/software/gettext/manual/)
- [Babel Documentation](http://babel.pocoo.org/en/latest/)
- [Python gettext Module](https://docs.python.org/3/library/gettext.html)

### Arquivos de Configuração

- **Extração:** [babel.cfg](../../babel.cfg)
- **Template:** [locales/messages.pot](../../locales/messages.pot)
- **Inglês:** [locales/en_US/LC_MESSAGES/messages.po](../../locales/en_US/LC_MESSAGES/messages.po)
- **Makefile:** Targets `i18n-*` em [Makefile](../../Makefile)

### Implementações de Referência

- [scripts/audit/reporter.py](../../scripts/audit/reporter.py) - Setup padrão de gettext
- [tests/test_reporter.py](../../tests/test_reporter.py) - Mock de i18n em testes
- [scripts/smart_git_sync.py](../../scripts/smart_git_sync.py) - Logging de locale

### Documentação Relacionada

- [CONTRIBUTING.md](../../CONTRIBUTING.md#-mantendo-a-internacionalização-i18n) - Guia para contribuidores
- [README.md](../../README.md#-internationalization-i18n) - Comandos de usuário

---

## Histórico de Revisões

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0.0 | 2025-12-16 | Versão inicial baseada em Sprint 4 learnings e retrospectiva v8.0 |

---

**Mantenha este documento atualizado conforme novos idiomas ou padrões de i18n forem adicionados.**
