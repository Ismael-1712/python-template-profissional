---
id: forense-dependency-guardian-v22-diagrams
type: guide
status: draft
version: 1.0.0
author: Engineering Team
date: 2026-01-11
context_tags: []
linked_code: []
---

```mermaid
sequenceDiagram
    participant DEV as Developer (Local)
    participant PyPI as PyPI Registry
    participant REPO as Git Repository
    participant CI as GitHub CI

    Note over PyPI: 2026-01-11 11:21:45 UTC
    PyPI->>PyPI: tomli 2.4.0 released

    Note over DEV: 2026-01-11 13:24:26 -0300<br/>(~2h after PyPI release)
    DEV->>DEV: make requirements
    DEV->>PyPI: pip-compile resolves deps
    PyPI-->>DEV: tomli==2.3.0 (cached locally)

    Note over DEV: Dependency Guardian v2.2
    DEV->>DEV: Compute SHA-256(dev.in)
    DEV->>DEV: Inject seal: c34d823...

    Note over DEV: File status at commit
    Note right of DEV: dev.in: tomli (no pin)<br/>dev.txt: tomli==2.3.0<br/>seal: c34d823... ✅

    DEV->>REPO: git commit + push

    Note over CI: 2026-01-11 16:XX:XX -0300<br/>(several hours later)
    REPO->>CI: Trigger CI workflow

    CI->>CI: Check lockfile consistency
    CI->>PyPI: pip-compile in memory
    PyPI-->>CI: tomli==2.4.0 (latest)

    Note over CI: Comparison
    Note right of CI: Expected: tomli==2.4.0<br/>Committed: tomli==2.3.0<br/>Result: DESYNC ❌

    CI->>CI: Validate SHA-256 seal
    CI->>CI: Compute SHA-256(dev.in)
    Note right of CI: Hash matches: c34d823... ✅<br/>But lockfile is stale!

    CI-->>REPO: ❌ CI FAILED
    Note over CI: Root Cause:<br/>Seal validates INPUT (dev.in)<br/>but OUTPUT (dev.txt) drifted
```

**Diagrama 1: Race Condition Temporal entre Ambiente Local e CI**

---

```mermaid
graph TD
    A[dev.in: tomli no pin] -->|Local pip-compile| B[dev.txt: tomli==2.3.0]
    A -->|SHA-256 hash| C[Hash: c34d823...]
    C -->|Seal injection| D[dev.txt + SEAL]
    D -->|git commit| E[Repository]

    E -->|CI checkout| F[CI Environment]
    F -->|pip-compile in-memory| G[Expected: tomli==2.4.0]
    F -->|Read committed file| H[Actual: tomli==2.3.0]

    G -.->|Compare| I{Match?}
    H -.->|Compare| I
    I -->|No| J[❌ DESYNC DETECTED]

    F -->|Validate seal| K{Seal valid?}
    K -->|Hash of dev.in unchanged| L[✅ SEAL VALID]

    J --> M[CI FAILS]
    L --> N[FALSE POSITIVE]

    style J fill:#ff6b6b
    style L fill:#51cf66
    style N fill:#ffd43b
    style M fill:#ff6b6b
```

**Diagrama 2: Falha de Design - Selo Valida INPUT mas Ignora OUTPUT**

---

```mermaid
graph LR
    subgraph "Current v2.2 (INSECURE)"
        A1[dev.in] -->|SHA-256| B1[Seal]
        B1 -->|Inject| C1[dev.txt + Seal]
        C1 -.->|Validate| D1{Hash match?}
        D1 -->|Yes| E1[✅ PASS]
        D1 -->|No| F1[❌ FAIL]

        G1[PyPI drift] -.->|Undetected| C1
    end

    subgraph "Proposed v2.3 (SECURE)"
        A2[dev.in] -->|SHA-256| B2[Seal-IN]
        C2[dev.txt] -->|SHA-256| D2[Seal-OUT]
        B2 -->|Inject| E2[dev.txt + Dual Seal]
        D2 -->|Inject| E2

        E2 -.->|Validate IN| F2{Hash match?}
        E2 -.->|Validate OUT| G2{Hash match?}
        F2 -->|Yes| H2[✅ Input OK]
        G2 -->|Yes| I2[✅ Output OK]
        F2 -->|No| J2[❌ Input changed]
        G2 -->|No| K2[❌ PyPI drift detected]

        L2[PyPI drift] -.->|Detected| K2
    end

    style E1 fill:#51cf66
    style F1 fill:#ff6b6b
    style G1 fill:#ffd43b
    style H2 fill:#51cf66
    style I2 fill:#51cf66
    style J2 fill:#ff6b6b
    style K2 fill:#ff6b6b
```

**Diagrama 3: Comparação de Segurança - v2.2 vs v2.3 Proposta**

---

```mermaid
flowchart TD
    START([make requirements]) --> A[pip-compile dev.in]
    A -->|Write| B[dev.txt with tomli==X.Y.Z]

    B --> C{Editor has<br/>dev.txt open?}

    C -->|No| D[Guardian inject seal]
    D --> E[Write sealed dev.txt]
    E --> F([✅ SUCCESS])

    C -->|Yes| G[Guardian inject seal]
    G --> H[Write sealed dev.txt]
    H --> I[Editor detects change]
    I --> J[Editor reloads buffer]

    J --> K{User saves<br/>buffer?}

    K -->|No| L([✅ SUCCESS])
    K -->|Yes| M[Buffer overwrites file]
    M --> N[❌ Seal on stale content]

    style F fill:#51cf66
    style L fill:#51cf66
    style N fill:#ff6b6b
    style M fill:#ffd43b

    O[SOLUTION: Atomic Write<br/>with File Locking]
    O -.->|Prevents| M
```

**Diagrama 4: Race Condition de Buffer (VS Code/Editor)**
