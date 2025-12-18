---
id: guide-toml-fusion
title: "TOML Fusion - Intelligent TOML File Merger"
description: "Guide for using toml-fusion to merge pyproject.toml files while preserving comments and customizations"
type: guide
status: active
version: "1.0.0"
date: 2025-12-18
tags:
  - toml
  - configuration
  - automation
  - cli
created: 2025-12-18
updated: 2025-12-18
author: Engineering Team
---

# TOML Fusion - Intelligent TOML File Merger

## 📋 Overview

**TOML Fusion** is a command-line tool that intelligently merges TOML files (particularly `pyproject.toml`) while preserving:

- ✅ Comments (section, inline, and block)
- ✅ Formatting (indentation, quote styles, spacing)
- ✅ User customizations
- ✅ Original structure

This is critical for maintaining template-based projects without losing developer-specific configurations.

## 🎯 Use Cases

### 1. Template Updates

You have a project template (`template/pyproject.toml`) that gets updated with new dependencies or configurations. You want to merge these updates into your project without losing your custom settings.

```bash
toml-fusion template/pyproject.toml pyproject.toml --dry-run
```

### 2. Team Configuration Sync

Synchronize common project configurations across team members while preserving individual customizations.

```bash
toml-fusion team-config.toml my-config.toml --strategy=smart
```

### 3. Dependency List Merge

Combine dependency lists from multiple sources (e.g., base + feature-specific).

```bash
toml-fusion feature-deps.toml pyproject.toml --output=merged-deps.toml
```

## 🚀 Installation

The command is registered in `pyproject.toml` as a console script:

```bash
# After installing the project (pip install -e .)
toml-fusion --help

# Or run directly
python scripts/cli/fusion.py --help
```

## 📖 Usage

### Basic Syntax

```bash
toml-fusion SOURCE TARGET [OPTIONS]
```

**Arguments:**

- `SOURCE`: Template TOML file (to merge from)
- `TARGET`: Project TOML file (to merge into)

**Options:**

- `--output, -o PATH`: Write to different file (default: overwrites TARGET)
- `--strategy, -s NAME`: Merge strategy (smart, template, user)
- `--dry-run, -n`: Preview changes without modifying files
- `--no-backup`: Skip backup creation (not recommended)

### Examples

#### Preview Changes (Dry Run)

```bash
$ toml-fusion template/pyproject.toml pyproject.toml --dry-run

📄 Source: template/pyproject.toml
📄 Target: pyproject.toml
🎯 Strategy: smart

🔍 DRY RUN MODE - No files will be modified

✅ Dry run completed successfully!

📊 Preview of changes:
──────────────────────────────────────────────────────────────────────
-dependencies = ["fastapi>=0.100.0", "pydantic>=2.0.0"]
+dependencies = ["fastapi>=0.115.0", "pydantic>=2.5.0", "requests"]
──────────────────────────────────────────────────────────────────────
```

#### Merge with Backup

```bash
$ toml-fusion template/pyproject.toml pyproject.toml

📄 Source: template/pyproject.toml
📄 Target: pyproject.toml
🎯 Strategy: smart

✅ Merge completed successfully!
   Output: pyproject.toml
   Backup: pyproject.toml.bak.20251218_143022
```

#### Force Template Values

```bash
toml-fusion template/pyproject.toml pyproject.toml --strategy=template
```

#### Preserve User Values

```bash
toml-fusion template/pyproject.toml pyproject.toml --strategy=user
```

#### Merge to Different File

```bash
toml-fusion template/pyproject.toml pyproject.toml -o merged.toml
```

## 🧠 Merge Strategies

### Smart (Default) - `--strategy=smart`

**Behavior:**

- **Lists**: Union with deduplication + version resolution
- **Dicts**: Recursive merge
- **Scalars**: Template value wins

**Example:**

```toml
# Template
dependencies = ["fastapi>=0.115.0", "pydantic>=2.5.0"]

# Project
dependencies = ["fastapi>=0.100.0", "requests"]

# Result
dependencies = ["fastapi>=0.115.0", "requests", "pydantic>=2.5.0"]
```

### Template Priority - `--strategy=template`

**Behavior:** Template values overwrite user values completely.

**Use when:** Forcing a canonical configuration across all projects.

### User Priority - `--strategy=user`

**Behavior:** User values preserved; template only fills gaps.

**Use when:** Minimal disruption; only add missing keys.

## 🔍 Version Conflict Resolution

When the same package appears in both files with different versions, TOML Fusion resolves conflicts:

```toml
# Template
dependencies = ["pydantic>=2.5.0"]

# Project
dependencies = ["pydantic>=2.0.0"]

# Result (higher version wins)
dependencies = ["pydantic>=2.5.0"]
```

**Algorithm:**

1. Extract version numbers using regex
2. Parse and compare semantic versions
3. Choose the more restrictive/higher version

## 💡 Comment Preservation

TOML Fusion uses `tomlkit` to preserve:

✅ **Section comments:**

```toml
# This is my custom configuration
[tool.mypy]
strict = true
```

✅ **Inline comments:**

```toml
line-length = 88  # Black standard
```

✅ **Array comments:**

```toml
ignore = [
    "D203",  # one-blank-line-before-class
    "E501",  # line-too-long
]
```

⚠️ **Limitation:** Inline comments in arrays may be lost if list items are sorted. TOML Fusion does NOT sort arrays to maximize comment preservation.

## 🛡️ Safety Features

### Automatic Backup

By default, TOML Fusion creates timestamped backups:

```
pyproject.toml.bak.20251218_143022
```

**Disable with:** `--no-backup` (not recommended)

### Dry Run Mode

Preview changes before applying:

```bash
toml-fusion source.toml target.toml --dry-run
```

**Output:**

- ✅ Success/failure status
- 📊 Colored unified diff
- ⚠️ No file modifications

### Error Handling

TOML Fusion validates:

- File existence
- TOML syntax validity
- Write permissions

**Errors are reported clearly:**

```
❌ Merge failed!
   • Source file not found: template.toml
   • Target contains invalid TOML syntax
```

## 📚 Advanced Usage

### Programmatic API

```python
from pathlib import Path
from scripts.utils.toml_merger import merge_toml, MergeStrategy

result = merge_toml(
    source_path=Path("template/pyproject.toml"),
    target_path=Path("pyproject.toml"),
    strategy=MergeStrategy.SMART,
    dry_run=True,
    backup=True,
)

if result.success:
    print("Merge successful!")
    print(result.diff)
else:
    print("Errors:", result.conflicts)
```

### Class-based Usage

```python
from scripts.utils.toml_merger import TOMLMerger, MergeStrategy

merger = TOMLMerger(strategy=MergeStrategy.SMART)
result = merger.merge(source_path, target_path)
```

## 🔧 Integration with Makefile

Add to `Makefile`:

```makefile
.PHONY: upgrade-toml
upgrade-toml:  ## Update pyproject.toml from template
 @toml-fusion templates/pyproject.toml pyproject.toml --backup
 @echo "✅ pyproject.toml updated from template"
```

Usage:

```bash
make upgrade-toml
```

## 📊 Testing

TOML Fusion has comprehensive test coverage (15 test cases):

```bash
# Run tests
pytest tests/test_toml_merger.py -v

# Test summary
# ✅ Comment preservation (critical)
# ✅ List merging with deduplication
# ✅ Version conflict resolution
# ✅ Recursive dictionary merge
# ✅ Backup creation
# ✅ Dry run behavior
# ✅ Error handling
```

## 🐛 Troubleshooting

### Issue: Comments Lost in Arrays

**Symptom:** Inline comments in dependency lists disappear after merge.

**Cause:** TOML Fusion modifies arrays in-place to preserve comments, but complex transformations may lose some inline comments.

**Solution:** Avoid sorting arrays. TOML Fusion does not sort to maximize comment preservation.

### Issue: Merge Creates Invalid TOML

**Symptom:** Output file fails TOML validation.

**Cause:** Rare edge case with tomlkit serialization.

**Solution:**

1. Check `result.success` before using output
2. Use `--dry-run` to preview
3. Report issue with sample TOML files

### Issue: Permission Denied

**Symptom:** `Failed to write output: Permission denied`

**Cause:** Target file is read-only or insufficient permissions.

**Solution:**

```bash
chmod u+w pyproject.toml
toml-fusion template.toml pyproject.toml
```

## 📖 Related Documentation

- [pyproject.toml Specification (PEP 621)](https://peps.python.org/pep-0621/)
- [tomlkit Documentation](https://github.com/sdispater/tomlkit)
- [Template Management Best Practices](./TEMPLATE_MANAGEMENT.md) (coming soon)

## 🤝 Contributing

Found a bug or have a feature request? Open an issue!

**Areas for improvement:**

- Better version conflict resolution (use `packaging.specifiers`)
- Interactive merge mode (prompt on conflicts)
- Configuration file for merge rules
- Support for other config formats (YAML, JSON)

---

**Status:** ✅ Production Ready
**Version:** 1.0.0
**Last Updated:** 2025-12-18
