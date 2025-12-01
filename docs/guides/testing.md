---
id: testing
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: '2025-12-01'
context_tags: []
linked_code:
- tests/test_smart_git_sync.py
title: Guia de Testes (SRE Standard)
---

# 🧪 Guia de Testes (SRE Standard)

Este projeto adota uma filosofia estrita de **Testes Unitários Isolados**.
O objetivo é garantir que a suíte de testes seja rápida (< 50ms), determinística e segura (sem efeitos colaterais).

## 🚫 O Que Não Fazer (Anti-Patterns)

1.  **Nunca toque no disco real:** Não use `os.mkdir`, `open("arquivo_real")` ou `tempfile.mkdtemp`.
2.  **Nunca execute comandos reais:** Não chame `subprocess.run(["git", ...])` sem mock.
3.  **Nunca dependa de estado externo:** Não assuma que o usuário tem Git instalado ou configurado.

## ✅ Como Escrever Testes (The Right Way)

Usamos `unittest.mock` intensivamente.

### Exemplo: Mockando Arquivos e Comandos

```python
from unittest.mock import MagicMock, patch
from pathlib import Path

# 1. Patch no subprocess (Blindagem)
@patch("scripts.git_sync.sync_logic.subprocess.run")
# 2. Patch no Path (Filesystem Virtual)
@patch("scripts.git_sync.sync_logic.Path")
def test_exemplo_seguro(self, mock_path, mock_run):

    # Configurar o Mock do Filesystem
    mock_path.return_value.exists.return_value = True

    # Configurar o Mock do Comando
    mock_run.return_value.returncode = 0

    # Executar (O código acha que está tocando no disco, mas não está)
    resultado = minha_funcao_perigosa()

    # Validar
    assert resultado == True
```

Consulte `tests/test_smart_git_sync.py` para exemplos avançados de mocks em cadeia.
