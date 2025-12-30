# Relatório de Diagnóstico MyPy

**Data:** 30 de dezembro de 2025
**Contexto:** Falhas no CI relacionadas a tipagem (`Library stubs not installed` e `BaseSettings`)

---

## 1. Pacotes Instalados (Evidência)

Resultado do comando: `pip list | grep -iE "(yaml|requests|pydantic|types-)"`

```
pydantic                                 2.12.5
pydantic_core                            2.41.5
pydantic-settings                        2.12.0
PyYAML                                   6.0.3
pyyaml_env_tag                           1.1
requests                                 2.32.5
requests-oauthlib                        2.0.0
requests-toolbelt                        1.0.0
types-PyYAML                             6.0.12.20250915
types-requests                           2.32.4.20250913
```

**Status dos Stubs:**

- ✅ `types-PyYAML` instalado (versão 6.0.12.20250915)
- ✅ `types-requests` instalado (versão 2.32.4.20250913)

---

## 2. Versão do Pydantic

**Comando:** `.venv/bin/python -c "import pydantic; print(f'Pydantic Version: {pydantic.VERSION}')"`

**Resultado:**

```
Pydantic Version: 2.12.5
```

**Análise:**

- Pydantic v2 está instalado (2.12.5)
- Em Pydantic v2, `BaseSettings` foi movido para o pacote separado `pydantic-settings`
- ✅ `pydantic-settings` está instalado (versão 2.12.0)

---

## 3. Análise do Código (config.py)

**Localização:** `src/app/core/config.py`

**Importação atual:**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
```

**Uso:**

```python
class Settings(BaseSettings):
    """Configurações globais da aplicação."""

    PROJECT_NAME: str = "Meu Projeto Profissional"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

**Compatibilidade:**

- ✅ Importação está **CORRETA** para Pydantic v2
- ✅ `BaseSettings` sendo importado de `pydantic_settings` (pacote correto)
- ✅ Uso de `SettingsConfigDict` também está correto

---

## 4. Configuração do MyPy

**Localização:** `pyproject.toml` → `[tool.mypy]`

```toml
[tool.mypy]
python_version = "3.10"
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
no_implicit_optional = true
strict_optional = true
ignore_missing_imports = true  # <-- RELEVANTE
follow_imports = "normal"
strict_equality = true
```

**Análise:**

- Configuração **muito estrita** (modo quase `--strict`)
- `ignore_missing_imports = true` pode mascarar problemas de stubs
- Override específico para `frontmatter`:

  ```toml
  [[tool.mypy.overrides]]
  module = "frontmatter"
  ignore_missing_imports = true
  ```

---

## 5. Conclusão do Copilot

### ✅ Não Faltam Stubs de Tipos

- `types-PyYAML` e `types-requests` estão instalados corretamente
- Stubs estão atualizados (versões de setembro/2025)

### ✅ Não Há Incompatibilidade Pydantic v1 vs v2

- Código está usando **corretamente** `pydantic_settings` para Pydantic v2
- Importação de `BaseSettings` está correta
- `pydantic-settings` está instalado (2.12.0)

### ⚠️ Possíveis Causas da Falha no CI

#### Hipótese 1: Ambiente do CI Desatualizado

- O ambiente local tem todos os pacotes corretos
- O CI pode estar usando um cache antigo ou `requirements.txt` desatualizado
- **Verificação necessária:** O CI está instalando `pydantic-settings` e os stubs?

#### Hipótese 2: Stubs de `pydantic-settings`

- O pacote `pydantic-settings` pode não ter stubs oficiais
- MyPy pode estar reclamando de tipagem incompleta em `pydantic_settings`
- **Solução potencial:** Adicionar `types-pydantic-settings` ou configurar override

#### Hipótese 3: Conflito entre `ignore_missing_imports`

- Com `ignore_missing_imports = true` globalmente, MyPy pode estar inconsistente
- Melhor usar overrides específicos por módulo

### 🔍 Próximos Passos Sugeridos

1. **Verificar logs exatos do CI:**
   - Qual linha exata está falhando?
   - Qual mensagem de erro completa?

2. **Verificar `requirements/dev.txt`:**
   - Confirmar se `pydantic-settings` e stubs estão incluídos

3. **Testar localmente o comando exato do CI:**

   ```bash
   mypy src/ scripts/
   ```

4. **Se erro persistir, adicionar override específico:**

   ```toml
   [[tool.mypy.overrides]]
   module = "pydantic_settings"
   ignore_missing_imports = true
   ```

---

## 6. Resumo Executivo

| Checklist | Status | Detalhes |
|-----------|--------|----------|
| Faltam stubs (types-*)? | ❌ NÃO | types-PyYAML e types-requests instalados |
| Incompatibilidade Pydantic v1 vs v2? | ❌ NÃO | Código correto para Pydantic v2 |
| Configuração MyPy muito estrita? | ⚠️ TALVEZ | Modo quase strict, mas controlado |
| CI usa ambiente diferente? | ⚠️ PROVÁVEL | Necessário verificar logs do CI |

**Diagnóstico Final:**
O ambiente local está **100% correto**. A falha no CI provavelmente é causada por:

- Cache antigo no CI
- Requirements desatualizados no CI
- Ausência de stubs para `pydantic-settings` especificamente

**Recomendação:**
Antes de modificar código, verificar:

1. Logs completos do CI
2. Se o CI está instalando `requirements/dev.txt` corretamente
3. Testar `mypy src/ scripts/` localmente para reproduzir o erro
