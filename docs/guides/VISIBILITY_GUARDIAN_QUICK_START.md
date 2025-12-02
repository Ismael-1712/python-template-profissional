---
id: visibility-guardian-quick-start
type: guide
status: draft
version: 1.0.0
author: Engineering Team
date: 2025-12-01
context_tags: []
linked_code: []
---

# Visibility Guardian - Quick Reference

## Instalação

```python
from scripts.core.guardian import ConfigScanner, ConfigFinding, ScanResult
```

## API Básica

### Escanear um arquivo

```python
from pathlib import Path
from scripts.core.guardian.scanner import ConfigScanner

scanner = ConfigScanner()
findings = scanner.scan_file(Path("my_app/config.py"))

for finding in findings:
    print(f"{finding.key} @ linha {finding.line_number}")
```

### Escanear projeto inteiro

```python
scanner = ConfigScanner()
result = scanner.scan_project(Path("."), pattern="**/*.py")

print(f"Total: {result.total_findings}")
print(f"Env vars: {len(result.env_vars)}")
print(f"Arquivos: {result.files_scanned}")
print(f"Tempo: {result.scan_duration_ms:.2f}ms")
```

## Modelos de Dados

### ConfigFinding

```python
@dataclass
class ConfigFinding:
    key: str                    # "DB_HOST"
    config_type: ConfigType     # ENV_VAR | CLI_ARG | FEATURE_FLAG
    source_file: Path           # Caminho do arquivo
    line_number: int            # Linha no código
    default_value: str | None   # "localhost" ou None
    required: bool              # True se sem default
    context: str                # Nome da função/classe
```

### ScanResult

```python
@dataclass
class ScanResult:
    findings: list[ConfigFinding]
    files_scanned: int
    errors: list[str]
    scan_duration_ms: float

    # Propriedades úteis:
    total_findings: int
    env_vars: list[ConfigFinding]
    cli_args: list[ConfigFinding]
```

## Padrões Detectados

| Padrão | Detectado | Required | Default |
|--------|-----------|----------|---------|
| `os.getenv("VAR")` | ✅ | Sim | None |
| `os.getenv("VAR", "val")` | ✅ | Não | "val" |
| `os.environ.get("VAR")` | ✅ | Sim | None |
| `os.environ.get("VAR", "val")` | ✅ | Não | "val" |
| `os.environ["VAR"]` | ✅ | Sim | None |

## Exemplo Completo

```python
from pathlib import Path
from scripts.core.guardian.scanner import ConfigScanner

def analyze_project():
    scanner = ConfigScanner()
    result = scanner.scan_project(Path("."))

    print(result.summary())

    # Agrupar por arquivo
    by_file = {}
    for finding in result.findings:
        if finding.source_file not in by_file:
            by_file[finding.source_file] = []
        by_file[finding.source_file].append(finding)

    # Mostrar configurações obrigatórias
    required = [f for f in result.findings if f.required]
    print(f"\nConfigurations obrigatórias: {len(required)}")
    for f in required:
        print(f"  - {f.key} ({f.source_file}:{f.line_number})")

    # Verificar erros
    if result.has_errors():
        print("\n⚠️  Erros:")
        for error in result.errors:
            print(f"  {error}")

if __name__ == "__main__":
    analyze_project()
```

## Testes

```bash
# Executar testes
pytest tests/test_guardian_scanner.py -v

# Com cobertura
pytest tests/test_guardian_scanner.py --cov=scripts.core.guardian

# Teste rápido
python -m pytest tests/test_guardian_scanner.py -q
```

## Exemplo de Uso Real

```bash
# Executar o exemplo incluído
python scripts/example_guardian_scanner.py
```

**Saída esperada**:

```
Scan completo: 14 configurações em 77 arquivos (14 env vars, 0 CLI args)

📊 Estatísticas:
  Total de variáveis de ambiente: 14
  Variáveis obrigatórias (sem default): 7
  Variáveis opcionais (com default): 7
  Arquivos escaneados: 77
  Tempo de scan: 132.50ms
```

## Limitações Atuais (Fase 1)

- ✅ Detecta variáveis de ambiente
- ❌ Não detecta argumentos CLI (typer, argparse) - **Fase 5**
- ❌ Não cruza com documentação - **Fase 2**
- ❌ Não gera relatórios formatados - **Fase 3**
- ❌ Não integra com CLI cortex - **Fase 4**

## Próximos Passos

1. **Fase 2**: Implementar matcher de documentação
2. **Fase 3**: Criar reporter com formatos table/json/markdown
3. **Fase 4**: Integrar com `cortex guardian check`
4. **Fase 5**: Detectar CLI args (typer, argparse)
5. **Fase 6**: Integração CI com bloqueio de commits

## Troubleshooting

### Import Error

```python
# ❌ Errado
from guardian import ConfigScanner

# ✅ Correto
from scripts.core.guardian import ConfigScanner
```

### SyntaxError durante scan

O scanner captura e registra erros de sintaxe:

```python
result = scanner.scan_project(Path("."))
if result.has_errors():
    for error in result.errors:
        print(f"Erro: {error}")
```

### Performance

O scanner é eficiente:

- 77 arquivos em ~130ms
- Ignora automaticamente `__pycache__` e `.venv`
- Não carrega todo o conteúdo em memória

---

**Documentação completa**: `docs/architecture/VISIBILITY_GUARDIAN_DESIGN.md`
**Histórico**: `docs/history/sprint_5/`
**Testes**: `tests/test_guardian_scanner.py`
