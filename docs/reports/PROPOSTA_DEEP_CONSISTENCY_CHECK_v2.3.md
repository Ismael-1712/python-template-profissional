---
id: proposta-deep-consistency-check-v23
type: arch
version: 1.0.0
author: GitHub Copilot
title: "Proposta de Implementação - Deep Consistency Check v2.3"
date: 2026-01-11
status: active
priority: "CRITICAL"
tags: [dependency-guardian, enhancement, security]
---

# 🛡️ PROPOSTA: DEEP CONSISTENCY CHECK v2.3

## OBJETIVO

Implementar validação de paridade total entre `requirements/*.in` e `requirements/*.txt`, eliminando falsos positivos causados por drift temporal de dependências no PyPI.

---

## DESIGN DE ARQUITETURA

### 1. MÓDULO: `scripts/core/dependency_guardian.py`

#### Nova Funcionalidade: `validate_deep_consistency()`

```python
class DependencyGuardian:
    """Cryptographic guardian for dependency integrity (v2.3)."""

    def validate_deep_consistency(
        self,
        req_name: str,
        python_exec: str | None = None,
    ) -> tuple[bool, str]:
        """Validate lockfile against in-memory pip-compile (deep check).

        This is the ULTIMATE consistency validation that catches:
        - Manual edits to lockfile
        - PyPI drift (upstream version changes)
        - Incomplete/corrupted pip-compile runs
        - Seal tampering

        Args:
            req_name: Requirements file name (e.g., 'dev')
            python_exec: Path to Python interpreter (uses sys.executable if None)

        Returns:
            tuple[bool, str]: (is_valid, diff_report)
                - is_valid: True if lockfile matches pip-compile output exactly
                - diff_report: Human-readable diff if desynchronized, empty if synced

        Example:
            guardian = DependencyGuardian(Path("requirements"))
            is_valid, diff = guardian.validate_deep_consistency("dev")

            if not is_valid:
                print("❌ Lockfile desynchronized:")
                print(diff)
        """
        in_file = self.requirements_dir / f"{req_name}.in"
        txt_file = self.requirements_dir / f"{req_name}.txt"

        if not in_file.exists():
            return False, f"Input file not found: {in_file}"

        if not txt_file.exists():
            return False, f"Lockfile not found: {txt_file}"

        # Use system python if not specified
        if python_exec is None:
            python_exec = sys.executable

        # Compile in memory to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w+",
            delete=False,
            suffix=".txt",
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Execute pip-compile (same flags as verify_deps.py for consistency)
            result = subprocess.run(
                [
                    python_exec,
                    "-m",
                    "piptools",
                    "compile",
                    str(in_file),
                    "--output-file",
                    str(tmp_path),
                    "--resolver=backtracking",
                    "--strip-extras",
                    "--allow-unsafe",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return False, f"pip-compile failed: {result.stderr}"

            # Compare content (comment-agnostic, like verify_deps.py)
            is_match, diff_lines = self._compare_content_deep(txt_file, tmp_path)

            if is_match:
                return True, ""
            else:
                diff_report = self._format_diff_report(diff_lines, txt_file, tmp_path)
                return False, diff_report

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def _compare_content_deep(
        self,
        file_a: Path,
        file_b: Path,
    ) -> tuple[bool, list[tuple[str, str]]]:
        """Compare two lockfiles, ignoring comments.

        Returns:
            tuple[bool, list[tuple[str, str]]]:
                - bool: True if files match
                - list: [(line_a, line_b)] for mismatched lines
        """
        with open(file_a, encoding="utf-8") as fa, open(
            file_b,
            encoding="utf-8",
        ) as fb:
            lines_a = [
                line.strip()
                for line in fa
                if line.strip() and not line.strip().startswith("#")
            ]
            lines_b = [
                line.strip()
                for line in fb
                if line.strip() and not line.strip().startswith("#")
            ]

        if lines_a == lines_b:
            return True, []

        # Find mismatches for detailed reporting
        mismatches = []
        max_len = max(len(lines_a), len(lines_b))

        for i in range(max_len):
            line_a = lines_a[i] if i < len(lines_a) else "<missing>"
            line_b = lines_b[i] if i < len(lines_b) else "<missing>"

            if line_a != line_b:
                mismatches.append((line_a, line_b))

        return False, mismatches

    def _format_diff_report(
        self,
        mismatches: list[tuple[str, str]],
        file_a: Path,
        file_b: Path,
    ) -> str:
        """Format human-readable diff report."""
        report = [
            "📊 LOCKFILE DESYNCHRONIZATION DETECTED",
            "",
            f"  Committed:  {file_a.name}",
            f"  Expected:   (in-memory pip-compile)",
            "",
            "🔍 DIFFERENCES:",
            "",
        ]

        for i, (line_a, line_b) in enumerate(mismatches, 1):
            report.append(f"  [{i}] Mismatch:")
            report.append(f"      COMMITTED: {line_a}")
            report.append(f"      EXPECTED:  {line_b}")
            report.append("")

        report.append("💊 REMEDIATION:")
        report.append("   make requirements  (or make deps-fix)")
        report.append("")

        return "\n".join(report)
```

---

### 2. INTEGRAÇÃO AO MAKEFILE

**Adicionar novo target `validate-deep`:**

```makefile
## validate: Validação completa (lint + tipos + deep deps check)
validate: lint type-check deps-deep-check audit

## deps-deep-check: Validação profunda de dependências (compilação em memória)
deps-deep-check:
 @echo "🛡️  Executando Deep Consistency Check (Protocolo v2.3)..."
 @$(PYTHON) -m scripts.core.dependency_guardian validate-deep dev
 @echo "✅ Lockfile em paridade total com estado atual do PyPI"

## deps-check: Validação rápida (apenas selo SHA-256) [DEPRECATED - use deps-deep-check]
deps-check:
 @echo "⚠️  Aviso: deps-check usa validação de selo (v2.2), que pode ter falsos positivos."
 @echo "   Considere usar: make deps-deep-check (v2.3)"
 @$(PYTHON) scripts/ci/verify_deps.py
```

---

### 3. ATUALIZAÇÃO DO CLI (`dependency_guardian.py` main)

```python
def main() -> None:
    """CLI entry point for dependency guardian operations."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Dependency Guardian - Integrity Seal Manager v2.3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute hash of dev.in
  python -m scripts.core.dependency_guardian compute dev

  # Inject seal into dev.txt
  python -m scripts.core.dependency_guardian seal dev

  # Validate dev.txt integrity (seal only - v2.2)
  python -m scripts.core.dependency_guardian validate dev

  # Deep consistency check (pip-compile in-memory - v2.3)
  python -m scripts.core.dependency_guardian validate-deep dev

Exit Codes:
  0 - Success / Validation passed
  1 - Failure / Validation failed
        """,
    )

    parser.add_argument(
        "action",
        choices=["compute", "seal", "validate", "validate-deep"],
        help="Action to perform",
    )
    parser.add_argument(
        "req_name",
        help="Requirements file name (e.g., 'dev' for dev.in/dev.txt)",
    )
    parser.add_argument(
        "--requirements-dir",
        type=Path,
        default=Path("requirements"),
        help="Path to requirements directory (default: requirements/)",
    )
    parser.add_argument(
        "--python-exec",
        type=str,
        help="Path to Python interpreter for pip-compile (default: sys.executable)",
    )

    args = parser.parse_args()

    guardian = DependencyGuardian(args.requirements_dir)

    try:
        if args.action == "compute":
            hash_value = guardian.compute_input_hash(args.req_name)
            print(f"SHA-256: {hash_value}")
            sys.exit(0)

        elif args.action == "seal":
            hash_value = guardian.compute_input_hash(args.req_name)
            guardian.inject_seal(args.req_name, hash_value)
            print(f"✅ Seal injected: {hash_value}")
            sys.exit(0)

        elif args.action == "validate":
            is_valid = guardian.validate_seal(args.req_name)
            if is_valid:
                print("✅ Integrity seal VALID (v2.2 protocol)")
                sys.exit(0)
            else:
                print("❌ Integrity seal INVALID or MISSING")
                sys.exit(1)

        elif args.action == "validate-deep":
            print(
                "🔍 Executing Deep Consistency Check (v2.3 protocol)...",
                flush=True,
            )
            is_valid, diff_report = guardian.validate_deep_consistency(
                args.req_name,
                python_exec=args.python_exec,
            )

            if is_valid:
                print("✅ Lockfile is in PERFECT SYNC with PyPI state")
                print("✅ Deep Consistency Check: PASSED")
                sys.exit(0)
            else:
                print("❌ Deep Consistency Check: FAILED")
                print("")
                print(diff_report)
                sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
```

---

### 4. ATUALIZAÇÃO DO CI WORKFLOW

**Substituir validação de selo por Deep Check:**

```yaml
# .github/workflows/ci.yml (linhas 78-84)
- name: "Check Lockfile Deep Consistency (v2.3)"
  env:
    PYTHON_BASELINE: "3.10"
  run: |
    echo "🛡️ Validando sincronização de dependências (Deep Check)..."
    python -m scripts.core.dependency_guardian validate-deep dev --python-exec python3.10
    echo "✅ Lockfile em paridade total com PyPI (v2.3 protocol)"
```

**Benefícios:**

✅ Detecta drift de PyPI em tempo real
✅ Elimina falsos positivos do selo SHA-256
✅ Mantém compatibilidade com baseline Python 3.10

---

## PLANO DE TESTES

### Teste 1: Detecção de PyPI Drift

```python
# tests/test_dependency_guardian_v23.py
def test_deep_consistency_detects_pypi_drift(tmp_path):
    """Test that deep check detects when PyPI has newer versions."""
    # Setup: Create dev.in with unpinned dependency
    in_file = tmp_path / "dev.in"
    in_file.write_text("tomli; python_version < '3.11'\n")

    # Compile with current PyPI state
    subprocess.run(
        ["pip-compile", str(in_file), "--output-file", str(tmp_path / "dev.txt")],
        check=True,
    )

    # Simulate older lockfile by editing dev.txt
    txt_file = tmp_path / "dev.txt"
    content = txt_file.read_text()
    content = content.replace("tomli==2.4.0", "tomli==2.3.0")  # Downgrade
    txt_file.write_text(content)

    # Execute deep check
    guardian = DependencyGuardian(tmp_path)
    is_valid, diff = guardian.validate_deep_consistency("dev")

    # Assert drift is detected
    assert not is_valid
    assert "tomli==2.3.0" in diff
    assert "tomli==2.4.0" in diff
```

### Teste 2: Validação de Lockfile Sincronizado

```python
def test_deep_consistency_passes_when_synced(tmp_path):
    """Test that deep check passes when lockfile is fresh."""
    in_file = tmp_path / "dev.in"
    in_file.write_text("ruff==0.14.10\npytest==9.0.2\n")

    # Fresh compile
    subprocess.run(
        ["pip-compile", str(in_file), "--output-file", str(tmp_path / "dev.txt")],
        check=True,
    )

    # Execute deep check
    guardian = DependencyGuardian(tmp_path)
    is_valid, diff = guardian.validate_deep_consistency("dev")

    # Assert sync is validated
    assert is_valid
    assert diff == ""
```

### Teste 3: Detecção de Edição Manual

```python
def test_deep_consistency_detects_manual_edit(tmp_path):
    """Test that deep check detects manual edits to lockfile."""
    in_file = tmp_path / "dev.in"
    in_file.write_text("ruff==0.14.10\n")

    # Fresh compile
    subprocess.run(
        ["pip-compile", str(in_file), "--output-file", str(tmp_path / "dev.txt")],
        check=True,
    )

    # Manual edit: add a fake dependency
    txt_file = tmp_path / "dev.txt"
    content = txt_file.read_text()
    content += "fake-package==1.0.0\n"
    txt_file.write_text(content)

    # Execute deep check
    guardian = DependencyGuardian(tmp_path)
    is_valid, diff = guardian.validate_deep_consistency("dev")

    # Assert tampering is detected
    assert not is_valid
    assert "fake-package==1.0.0" in diff
```

---

## IMPACTO EM PERFORMANCE

### Análise de Custo

| Operação | v2.2 (Selo SHA-256) | v2.3 (Deep Check) | Delta |
|----------|---------------------|-------------------|-------|
| **Validação de Selo** | ~50ms | N/A | - |
| **pip-compile in-memory** | N/A | ~3-8s | +3-8s |
| **Comparação de conteúdo** | ~10ms | ~20ms | +10ms |
| **Total** | **~60ms** | **~3-8s** | **+50-130x** |

### Estratégias de Mitigação

#### 1. Cache de Compilação (CI)

```yaml
- name: "Cache pip-compile results"
  uses: actions/cache@v5
  with:
    path: .cache/pip-compile
    key: deps-${{ hashFiles('requirements/dev.in') }}-${{ hashFiles('requirements/dev.txt') }}
```

**Benefício:** Se o hash do `.in` E do `.txt` não mudaram, skip deep check.

#### 2. Validação Incremental (Local)

```python
def validate_deep_consistency_cached(self, req_name: str) -> tuple[bool, str]:
    """Deep check with cache (skip if seal is valid)."""
    # Fast path: check seal first
    if self.validate_seal(req_name):
        # Seal is valid, but we still need deep check for PyPI drift
        # UNLESS we have a recent successful deep check cached
        cache_file = self.requirements_dir / f".{req_name}.deep_check_cache"

        if cache_file.exists():
            cache_data = json.loads(cache_file.read_text())
            if cache_data["seal"] == self._extract_seal(...):
                # Seal hasn't changed since last deep check
                return True, ""

    # Slow path: full deep check
    return self.validate_deep_consistency(req_name)
```

#### 3. Validação Assíncrona (Background)

```makefile
## validate-deep-async: Deep check em background (não bloqueia)
validate-deep-async:
 @$(PYTHON) -m scripts.core.dependency_guardian validate-deep dev &
 @echo "✅ Deep check iniciado em background (PID: $!)"
```

---

## DOCUMENTAÇÃO E MIGRAÇÃO

### README Update

```markdown
### Validação de Dependências (v2.3)

O projeto usa o **Dependency Guardian v2.3** com Deep Consistency Check:

- **Selo SHA-256 (v2.2):** Validação rápida contra edições manuais
- **Deep Check (v2.3):** Validação completa contra drift do PyPI

#### Uso Diário

```bash
# Antes de commitar
make validate  # Inclui deep check

# Se falhar, sincronizar
make requirements
```

#### Limitações Conhecidas

- Deep check requer conexão com PyPI (~5s de latência)
- Em ambientes offline, use apenas validação de selo: `make deps-check`

```

---

## ROLLOUT PLAN

### Fase 1: Implementação (Sprint Atual)

- [x] Investigação forense (concluída)
- [ ] Implementar `validate_deep_consistency()`
- [ ] Adicionar testes unitários (3 cenários)
- [ ] Atualizar Makefile

### Fase 2: Integração CI (Sprint +1)

- [ ] Atualizar workflow do GitHub Actions
- [ ] Adicionar cache de compilação
- [ ] Documentar no README

### Fase 3: Monitoramento (Sprint +2)

- [ ] Coletar métricas de performance do CI
- [ ] Otimizar cache strategy
- [ ] Considerar implementação de Dual-Hash Seal (v2.4)

---

## CONCLUSÃO

O Deep Consistency Check resolve a falha fundamental do protocolo v2.2 ao validar o **estado final** (lockfile compilado) em vez de apenas o **estado inicial** (.in file). Apesar do impacto em performance, a garantia de consistência absoluta justifica o custo, especialmente em ambientes CI onde a reprodutibilidade é crítica.

**Próximo Milestone:** v2.4 com Dual-Hash Seal para validação offline instantânea.

---

**Proposta por:** GitHub Copilot (Claude Sonnet 4.5)
**Data:** 2026-01-11
**Status:** Design Approval Pending
