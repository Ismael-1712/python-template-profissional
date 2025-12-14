---
id: cortex-link-resolver-design
type: arch
status: draft
version: 0.1.0
author: Engineering Team
date: 2025-12-14
context_tags:
  - cortex
  - knowledge-graph
  - link-resolution
  - algorithm-design
linked_code:
  - scripts/core/cortex/models.py
  - scripts/core/cortex/link_analyzer.py
dependencies: []
related_docs:
  - docs/architecture/CORTEX_FASE01_DESIGN.md
---

# CORTEX Fase 03 - Link Resolver Design

**Task:** [008] The Link Resolver
**Status:** Design Phase
**Prerequisite:** [007] Link Scanner (Completed)

## 📋 Executive Summary

O **Link Resolver** é o componente responsável por transformar links brutos extraídos pelo `LinkAnalyzer` em conexões validadas no grafo de conhecimento. Ele resolve targets não ambíguos (texto → IDs) e valida a existência dos nós de destino.

**Core Problem:** Um link como `[[Fase 01]]` é apenas texto. O resolver deve descobrir qual `KnowledgeEntry` corresponde a esse título e retornar seu ID (`kno-002`).

---

## 🎯 Objectives

1. **Indexação Reversa:** Criar estruturas de lookup eficientes para resolver targets
2. **Estratégias de Resolução:** Implementar ordem de precedência para diferentes tipos de links
3. **Validação:** Identificar links quebrados e classificar status (VALID/BROKEN/EXTERNAL)
4. **Performance:** Garantir O(1) para lookups em índices (dicts/sets)

---

## 🏗️ Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    KnowledgeIndex                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Primary Index:                                      │    │
│  │   entries: dict[str, KnowledgeEntry]               │    │
│  │   └─ "kno-001" -> KnowledgeEntry(...)              │    │
│  └────────────────────────────────────────────────────┘    │
│                           ↓                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Reverse Indices (NEW):                             │    │
│  │   _path_to_id: dict[Path, str]                     │    │
│  │   └─ Path("docs/knowledge/kno-001.md") -> "kno-001"│    │
│  │                                                      │    │
│  │   _alias_to_id: dict[str, str]                     │    │
│  │   └─ "Fase 01" -> "kno-002"                        │    │
│  │   └─ "Introduction" -> "kno-002"                   │    │
│  │                                                      │    │
│  │   _title_normalized: dict[str, str]                │    │
│  │   └─ "fase01" -> "kno-002"  (fuzzy match)          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    LinkResolver                             │
│  resolve_target(target_raw, source_entry, type) -> Result  │
│                                                              │
│  Strategy Pipeline:                                         │
│    1. Try ID Resolution     (target == entry.id)           │
│    2. Try Path Resolution   (relative/absolute path)        │
│    3. Try Alias Resolution  (match against aliases)         │
│    4. Try Fuzzy Resolution  (normalized title match)        │
│    5. Return BROKEN         (not found)                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                 KnowledgeLink (Updated)                     │
│  target_resolved: str | None   ← Set by resolver           │
│  is_valid: bool                ← Set by resolver           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Design

### 1. KnowledgeIndex Enhancement

**Current State:**

```python
class KnowledgeIndex:
    entries: dict[str, KnowledgeEntry]  # ID -> Entry
```

**Proposed Enhancement:**

```python
class KnowledgeIndex:
    entries: dict[str, KnowledgeEntry]  # ID -> Entry

    # NEW: Reverse indices for efficient lookups
    _path_to_id: dict[Path, str]        # Absolute path -> ID
    _alias_to_id: dict[str, list[str]]  # Alias/Title -> [IDs] (can be multiple)
    _title_normalized: dict[str, str]   # Normalized title -> ID

    def build_reverse_indices(self) -> None:
        """Build all reverse index structures after populating entries."""

    def find_by_path(self, path: Path) -> str | None:
        """Resolve a file path to an entry ID."""

    def find_by_alias(self, alias: str) -> list[str]:
        """Find all entry IDs matching an alias or title."""

    def find_by_normalized_title(self, text: str) -> str | None:
        """Fuzzy match a text string to a normalized title."""
```

**Indexing Logic:**

- `_path_to_id`: Map both `entry.file_path` (absolute) and workspace-relative paths
- `_alias_to_id`: Extract from frontmatter `aliases` field + document title
- `_title_normalized`: Normalize text (lowercase, remove spaces/punctuation) for fuzzy matching

---

### 2. LinkResolver Component

**Interface:**

```python
from dataclasses import dataclass
from pathlib import Path
from scripts.core.cortex.models import KnowledgeLink, LinkType

@dataclass
class ResolutionResult:
    """Result of a link resolution attempt."""

    target_resolved: str | None  # Resolved ID or None
    is_valid: bool               # True if resolution succeeded
    resolution_strategy: str     # "id" | "path" | "alias" | "fuzzy" | "broken"


class LinkResolver:
    """Resolves raw link targets to validated Knowledge Node IDs."""

    def __init__(self, index: KnowledgeIndex) -> None:
        """Initialize with a populated KnowledgeIndex."""
        self.index = index

    def resolve_link(
        self,
        link: KnowledgeLink,
        source_entry: KnowledgeEntry,
    ) -> ResolutionResult:
        """Resolve a single KnowledgeLink to a target ID.

        Args:
            link: The link to resolve (contains target_raw)
            source_entry: The entry where this link was found

        Returns:
            ResolutionResult with resolved ID and validation status
        """

    def resolve_all_links(
        self,
        entries: list[KnowledgeEntry],
    ) -> list[KnowledgeEntry]:
        """Resolve all links in all entries (post-processing phase).

        Args:
            entries: List of entries with extracted but unresolved links

        Returns:
            List of entries with resolved links (new instances, frozen models)
        """
```

---

### 3. Resolution Algorithm (Pseudocode)

```python
def resolve_link(link: KnowledgeLink, source_entry: KnowledgeEntry) -> ResolutionResult:
    """
    Resolution Strategy Pipeline (Order matters!)

    Priority:
        1. ID Resolution (highest priority - exact match)
        2. Path Resolution (for markdown links with file paths)
        3. Alias Resolution (for wikilinks with titles/aliases)
        4. Fuzzy Resolution (last resort - normalized match)
        5. Broken Link (no match found)
    """

    target_raw = link.target_raw
    link_type = link.type

    # ========================================================================
    # STRATEGY 1: Direct ID Match
    # ========================================================================
    # Example: [[kno-001]] or [Doc](kno-001)
    if target_raw in self.index.entries:
        return ResolutionResult(
            target_resolved=target_raw,
            is_valid=True,
            resolution_strategy="id"
        )

    # ========================================================================
    # STRATEGY 2: File Path Resolution
    # ========================================================================
    # Example: [Guide](../guides/setup.md) or [[docs/knowledge/intro.md]]
    if link_type in [LinkType.MARKDOWN, LinkType.WIKILINK]:
        # Try to resolve as a file path (relative or absolute)
        resolved_path = self._resolve_path(target_raw, source_entry.file_path)

        if resolved_path and (target_id := self.index.find_by_path(resolved_path)):
            return ResolutionResult(
                target_resolved=target_id,
                is_valid=True,
                resolution_strategy="path"
            )

    # ========================================================================
    # STRATEGY 3: Alias/Title Exact Match
    # ========================================================================
    # Example: [[Fase 01]] matches entry with title "Fase 01"
    if link_type in [LinkType.WIKILINK, LinkType.WIKILINK_ALIASED]:
        matching_ids = self.index.find_by_alias(target_raw)

        if len(matching_ids) == 1:
            # Unambiguous match
            return ResolutionResult(
                target_resolved=matching_ids[0],
                is_valid=True,
                resolution_strategy="alias"
            )
        elif len(matching_ids) > 1:
            # Ambiguous! Log warning and mark as broken
            logger.warning(
                f"Ambiguous alias '{target_raw}' matches {len(matching_ids)} entries"
            )
            return ResolutionResult(
                target_resolved=None,
                is_valid=False,
                resolution_strategy="ambiguous"
            )

    # ========================================================================
    # STRATEGY 4: Fuzzy Normalized Match (Last Resort)
    # ========================================================================
    # Example: [[fase 01]] (lowercase) matches "Fase 01"
    normalized_target = self._normalize_text(target_raw)

    if target_id := self.index.find_by_normalized_title(normalized_target):
        return ResolutionResult(
            target_resolved=target_id,
            is_valid=True,
            resolution_strategy="fuzzy"
        )

    # ========================================================================
    # STRATEGY 5: Link Broken (Not Found)
    # ========================================================================
    logger.debug(f"Could not resolve link: {target_raw} from {source_entry.id}")
    return ResolutionResult(
        target_resolved=None,
        is_valid=False,
        resolution_strategy="broken"
    )


def _resolve_path(self, target_raw: str, source_file: Path) -> Path | None:
    """
    Convert a relative or absolute path string to an absolute Path.

    Examples:
        - "../guides/setup.md" (relative to source_file's directory)
        - "docs/knowledge/intro.md" (relative to workspace root)
        - "/absolute/path/to/file.md" (absolute)
    """
    # Remove anchor fragments (#section)
    target_clean = target_raw.split('#')[0]

    # Try relative to source file's directory
    if target_clean.startswith(('./', '../')):
        resolved = (source_file.parent / target_clean).resolve()
        if self.index._path_to_id.get(resolved):
            return resolved

    # Try relative to workspace root
    workspace_relative = (self.workspace_root / target_clean).resolve()
    if self.index._path_to_id.get(workspace_relative):
        return workspace_relative

    # Try as absolute path
    absolute_path = Path(target_clean)
    if absolute_path.is_absolute() and absolute_path.exists():
        return absolute_path

    return None


def _normalize_text(self, text: str) -> str:
    """
    Normalize text for fuzzy matching.

    Rules:
        - Convert to lowercase
        - Remove punctuation (except hyphens)
        - Collapse multiple spaces to single space
        - Strip leading/trailing whitespace

    Examples:
        "Fase 01" -> "fase01"
        "Introduction: Part 1" -> "introductionpart1"
    """
    import re
    normalized = text.lower()
    normalized = re.sub(r'[^\w\s-]', '', normalized)  # Remove punctuation
    normalized = re.sub(r'\s+', '', normalized)       # Remove all spaces
    return normalized.strip()
```

---

### 4. Code Reference Resolution (Special Case)

For `LinkType.CODE_REFERENCE` (`[[code:path/to/file.py]]` or `[[code:path::Symbol]]`):

```python
def _resolve_code_reference(self, target_raw: str) -> ResolutionResult:
    """
    Resolve code reference links.

    Format: "code:path/to/file.py" or "code:path/to/file.py::ClassName"

    Steps:
        1. Extract file path from target_raw
        2. Check if file exists in workspace
        3. Optionally validate symbol existence (AST parsing - future enhancement)
        4. Return file path as target_resolved (not an ID)
    """
    # Extract path after "code:" prefix
    if not target_raw.startswith("code:"):
        return ResolutionResult(None, False, "invalid_code_ref")

    path_part = target_raw[5:]  # Remove "code:" prefix
    file_path, _, symbol = path_part.partition("::")

    # Resolve file path
    resolved_file = self._resolve_path(file_path, source_entry.file_path)

    if resolved_file and resolved_file.exists():
        # For code refs, target_resolved is the file path (not an ID)
        return ResolutionResult(
            target_resolved=str(resolved_file),
            is_valid=True,
            resolution_strategy="code_reference"
        )

    return ResolutionResult(None, False, "code_file_not_found")
```

---

## 🔄 Integration with `cortex map`

### Current Flow (After Task [007])

```
1. cortex map
   ↓
2. KnowledgeScanner.scan()
   └─ For each .md file:
      ├─ Parse frontmatter
      ├─ Extract cached_content
      ├─ LinkAnalyzer.extract_links(content)  [007]
      └─ Create KnowledgeEntry (with unresolved links)
   ↓
3. Build KnowledgeIndex(entries)
   ↓
4. Save to .cortex/knowledge.json
```

### Enhanced Flow (With Task [008])

```
1. cortex map
   ↓
2. KnowledgeScanner.scan()
   └─ For each .md file:
      ├─ Parse frontmatter
      ├─ Extract cached_content
      ├─ LinkAnalyzer.extract_links(content)  [007]
      └─ Create KnowledgeEntry (with unresolved links)
   ↓
3. Build KnowledgeIndex(entries)
   ↓
4. index.build_reverse_indices()  [NEW - 008]
   ↓
5. LinkResolver(index).resolve_all_links(entries)  [NEW - 008]
   └─ For each entry:
      └─ For each link in entry.links:
         ├─ resolve_link(link, entry)
         └─ Update link.target_resolved and link.is_valid
   ↓
6. Save to .cortex/knowledge.json (with resolved links)
```

---

## 📊 Model Updates

### KnowledgeLink (Already Supports Resolution)

```python
class KnowledgeLink(BaseModel):
    source_id: str
    target_raw: str                    # Set by LinkAnalyzer [007]
    target_resolved: str | None = None # Set by LinkResolver [008] ← NEW
    type: LinkType
    line_number: int
    context: str
    is_valid: bool = False             # Set by LinkResolver [008] ← NEW
```

**No changes needed!** The model already has the required fields.

---

## 🧪 Testing Strategy

### Unit Tests

```python
# test_link_resolver.py

def test_resolve_link_by_id():
    """Direct ID match should resolve immediately."""
    index = KnowledgeIndex(...)
    resolver = LinkResolver(index)

    link = KnowledgeLink(
        source_id="kno-001",
        target_raw="kno-002",
        type=LinkType.WIKILINK,
        ...
    )

    result = resolver.resolve_link(link, source_entry)
    assert result.target_resolved == "kno-002"
    assert result.is_valid is True
    assert result.resolution_strategy == "id"


def test_resolve_link_by_path_relative():
    """Relative path should resolve to ID."""
    # Setup: entry at docs/knowledge/intro.md with id=kno-001
    # Link: [[../guides/setup.md]] from intro.md

    result = resolver.resolve_link(link, source_entry)
    assert result.target_resolved == "kno-002"  # ID of setup.md
    assert result.resolution_strategy == "path"


def test_resolve_link_by_alias():
    """Wikilink with title/alias should resolve."""
    # Setup: entry with id=kno-002, title="Introduction"
    # Link: [[Introduction]]

    result = resolver.resolve_link(link, source_entry)
    assert result.target_resolved == "kno-002"
    assert result.resolution_strategy == "alias"


def test_resolve_link_fuzzy_normalized():
    """Fuzzy match with normalized text."""
    # Setup: entry with title="Fase 01"
    # Link: [[fase 01]] (lowercase, extra space)

    result = resolver.resolve_link(link, source_entry)
    assert result.target_resolved == "kno-002"
    assert result.resolution_strategy == "fuzzy"


def test_resolve_link_broken():
    """Non-existent target should mark as broken."""
    link = KnowledgeLink(target_raw="NonExistent", ...)

    result = resolver.resolve_link(link, source_entry)
    assert result.target_resolved is None
    assert result.is_valid is False
    assert result.resolution_strategy == "broken"


def test_resolve_link_ambiguous_alias():
    """Multiple matches should fail (ambiguous)."""
    # Setup: Two entries with same title "Setup"
    # Link: [[Setup]]

    result = resolver.resolve_link(link, source_entry)
    assert result.is_valid is False
    assert result.resolution_strategy == "ambiguous"
```

### Integration Tests

```python
def test_end_to_end_resolution():
    """Full pipeline: scan -> index -> resolve."""
    scanner = KnowledgeScanner(workspace_root)
    entries = scanner.scan()

    index = KnowledgeIndex(entries)
    index.build_reverse_indices()

    resolver = LinkResolver(index)
    resolved_entries = resolver.resolve_all_links(entries)

    # Verify all links are processed
    for entry in resolved_entries:
        for link in entry.links:
            assert link.target_resolved is not None or not link.is_valid
```

---

## 🚀 Implementation Checklist

- [ ] **Phase 1: Index Enhancement**
  - [ ] Add reverse index structures to `KnowledgeIndex`
  - [ ] Implement `build_reverse_indices()` method
  - [ ] Implement lookup methods (`find_by_path`, `find_by_alias`, `find_by_normalized_title`)
  - [ ] Write unit tests for index lookups

- [ ] **Phase 2: LinkResolver Core**
  - [ ] Create `scripts/core/cortex/link_resolver.py`
  - [ ] Implement `ResolutionResult` dataclass
  - [ ] Implement `LinkResolver` class skeleton
  - [ ] Implement ID resolution strategy
  - [ ] Implement path resolution strategy
  - [ ] Implement alias resolution strategy
  - [ ] Implement fuzzy resolution strategy
  - [ ] Implement `resolve_all_links()` batch processor
  - [ ] Write unit tests for each strategy

- [ ] **Phase 3: Integration**
  - [ ] Update `cortex map` command to call resolver
  - [ ] Update `KnowledgeScanner` flow to integrate resolution step
  - [ ] Verify serialization of resolved links to JSON
  - [ ] Write integration tests

- [ ] **Phase 4: Validation & Error Handling**
  - [ ] Add logging for broken links
  - [ ] Add metrics collection (% of valid links)
  - [ ] Handle ambiguous aliases gracefully
  - [ ] Add CLI flag to show link validation report

---

## 📈 Performance Considerations

### Time Complexity

- **Index Building:** O(n × m) where n = entries, m = avg links per entry
- **Single Link Resolution:** O(1) for all strategies (dict lookups)
- **Batch Resolution:** O(n × m) where n = entries, m = avg links per entry

### Space Complexity

- **Reverse Indices:** O(n) for each index structure
- **Total Memory:** ~3× size of primary index (acceptable trade-off)

### Optimization Opportunities

1. **Lazy Index Building:** Only build indices when resolver is invoked
2. **Incremental Updates:** Update indices when single entry changes (future)
3. **Caching:** Memoize frequently accessed lookups

---

## 🔗 Dependencies

**Requires:**

- [007] Link Scanner (Completed)
- `scripts/core/cortex/models.py` (KnowledgeLink, KnowledgeEntry)
- `scripts/core/cortex/knowledge_index.py` (to be enhanced)

**Enables:**

- [009] Graph Visualization (requires resolved links)
- [010] Link Health Reporting (requires validation status)

---

## 📝 Open Questions & Future Enhancements

### Q1: How to handle external HTTP links?

**Proposed Answer:** Skip resolution (already filtered in LinkAnalyzer). Add a separate `external_links` field if needed.

### Q2: Should we validate code symbols (AST parsing)?

**Proposed Answer:** Phase 2 enhancement. For now, just validate file existence.

### Q3: How to handle circular references?

**Proposed Answer:** Resolution doesn't traverse the graph, so circular refs are fine. Graph visualization will handle cycles.

### Q4: What about case-sensitive filesystems?

**Proposed Answer:** Use `Path.resolve()` and case-sensitive comparisons. Document this behavior.

---

## 🎓 Design Rationale

### Why Reverse Indices?

**Alternative 1:** Linear search through all entries for each link.

- **Pros:** Simple, no memory overhead
- **Cons:** O(n) for each lookup = O(n²) total complexity

**Alternative 2:** Build indices on-demand (cache as you go).

- **Pros:** Lazy evaluation, only build what's needed
- **Cons:** Unpredictable performance, complex cache invalidation

**Chosen:** Pre-build all indices after scan phase.

- **Pros:** O(1) lookups, predictable performance, simple to reason about
- **Cons:** Memory overhead (acceptable for typical project sizes)

### Why Strategy Pipeline?

The order of resolution strategies matters because:

1. **ID match is most specific** (exact identifier)
2. **Path match is unambiguous** (filesystem guarantees uniqueness)
3. **Alias match can be ambiguous** (multiple docs with same title)
4. **Fuzzy match is least reliable** (normalization may cause false positives)

---

## ✅ Success Criteria

1. **Correctness:** All valid links resolve to correct IDs
2. **Performance:** Resolution completes in <1s for 1000 entries with 10 links each
3. **Robustness:** Broken links don't crash the system
4. **Observability:** Clear logs for debugging resolution issues
5. **Testability:** 90%+ test coverage for resolver logic

---

## 📚 References

- **CORTEX Phase 01 Design:** [docs/architecture/CORTEX_FASE01_DESIGN.md](../architecture/CORTEX_FASE01_DESIGN.md)
- **Link Scanner Implementation:** [docs/architecture/CORTEX_FASE03_DIAGRAMS.py](../architecture/CORTEX_FASE03_DIAGRAMS.py)
- **Knowledge Models:** [scripts/core/cortex/models.py](../../scripts/core/cortex/models.py)

---

**Status:** Ready for Implementation
**Next Step:** Begin Phase 1 (Index Enhancement)
**Estimated Effort:** 2-3 development sessions
