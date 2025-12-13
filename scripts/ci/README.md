# CI/CD Scripts

Este diretório contém scripts otimizados para execução em pipelines de CI/CD.

## 📁 Estrutura

```
scripts/ci/
├── __init__.py          # Inicializador do módulo
├── check_docs.py        # Validador de documentação CLI
└── README.md            # Este arquivo
```

## 🔍 Scripts Disponíveis

### `check_docs.py` - Validador de Documentação CLI

Valida que a documentação CLI está sincronizada com o código-fonte.

**Uso:**

```bash
python scripts/ci/check_docs.py
```

**Exit Codes:**

- `0`: Documentação atualizada ✅
- `1`: Documentação desatualizada ou erro ❌

**Documentação Completa:** [docs/reference/CI_DOCS_VALIDATOR.md](../../docs/reference/CI_DOCS_VALIDATOR.md)

**Quando usar:**

- Em workflows de CI/CD (GitHub Actions, GitLab CI, etc.)
- Em pre-commit hooks
- Antes de merges em branches principais
- Como gate de qualidade para PRs

**Exemplo de integração:**

```yaml
# .github/workflows/ci.yml
- name: Validate Documentation
  run: python scripts/ci/check_docs.py
```

## 🎯 Princípios de Design

Scripts neste diretório devem:

1. **✅ Serem Determinísticos**: Mesmo input → mesmo output
2. **✅ Exit Codes Apropriados**: 0 = sucesso, != 0 = falha
3. **✅ Output Claro**: Mensagens descritivas para debugging
4. **✅ Sem Efeitos Colaterais**: Não modificam o repositório
5. **✅ Rápidos**: Otimizados para execução frequente
6. **✅ Testáveis**: Cobertura de testes unitários

## 📊 Integração com CI/CD

### GitHub Actions

```yaml
name: CI

on: [push, pull_request]

jobs:
  ci-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements/dev.txt
      - run: python scripts/ci/check_docs.py
```

### GitLab CI

```yaml
ci-checks:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements/dev.txt
    - python scripts/ci/check_docs.py
```

### Azure Pipelines

```yaml
- script: |
    pip install -r requirements/dev.txt
    python scripts/ci/check_docs.py
  displayName: 'CI Checks'
```

## 🧪 Testes

Todos os scripts CI devem ter testes em `tests/test_ci_*.py`:

```bash
# Rodar testes específicos
pytest tests/test_ci_check_docs.py -v

# Rodar todos os testes CI
pytest tests/test_ci_*.py -v
```

## 📝 Adicionando Novos Scripts

Ao adicionar um novo script CI:

1. **Crie o script** em `scripts/ci/novo_script.py`
2. **Adicione docstring** detalhada no início do arquivo
3. **Implemente exit codes** apropriados (0 = sucesso)
4. **Crie testes** em `tests/test_ci_novo_script.py`
5. **Documente** neste README
6. **Adicione ao CI** se aplicável

**Template básico:**

```python
#!/usr/bin/env python3
"""Brief description.

Detailed description here.

Exit Codes:
    0: Success
    1: Failure

Usage:
    python scripts/ci/script_name.py

Author: DevOps Engineering Team
"""

import sys
from pathlib import Path

def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Script logic here
        print("✅ Success!")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## 🔧 Troubleshooting

### Script falha localmente mas passa no CI

**Causa**: Diferenças de ambiente (Python version, dependencies, etc.)

**Solução**:

```bash
# Replique ambiente do CI
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
python scripts/ci/check_docs.py
```

### Script muito lento no CI

**Causa**: Operações custosas (I/O, network, etc.)

**Solução**:

- Use cache quando possível
- Paralelise operações independentes
- Minimize operações de disco
- Considere memoização

### Exit code incorreto

**Causa**: Exceptions não capturadas ou lógica incorreta

**Solução**:

- Use try/except apropriadamente
- Retorne explicitamente exit codes
- Teste casos de erro

## 📚 Recursos

- [Documentação do Validador de Docs](../../docs/reference/CI_DOCS_VALIDATOR.md)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/learn-github-actions/best-practices-for-workflows)
- [GitLab CI/CD Best Practices](https://docs.gitlab.com/ee/ci/yaml/index.html)
- [Exit Codes Convention](https://tldp.org/LDP/abs/html/exitcodes.html)

## 🤝 Contribuindo

Ao contribuir com scripts CI:

1. Siga os princípios de design acima
2. Adicione testes abrangentes
3. Documente claramente o propósito e uso
4. Considere impacto na performance do CI
5. Valide em múltiplos ambientes

---

**Manutenção**: DevOps Engineering Team
**Última Atualização**: 2024-12-13
