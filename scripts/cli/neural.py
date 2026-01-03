#!/usr/bin/env python3
"""CORTEX Neural Interface CLI.

Commands for semantic search and vector indexing using ChromaDB and embeddings.

Usage:
    cortex neural index           # Index all documentation
    cortex neural ask "query"     # Semantic search

Author: Engineering Team
License: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# Add project root to sys.path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner  # noqa: E402
from scripts.core.cortex.neural.adapters.memory import InMemoryVectorStore  # noqa: E402
from scripts.core.cortex.neural.domain import SearchResult  # noqa: E402
from scripts.core.cortex.neural.ports import (  # noqa: E402
    EmbeddingPort,
    VectorStorePort,
)
from scripts.core.cortex.neural.vector_bridge import VectorBridge  # noqa: E402
from scripts.utils.logger import setup_logging  # noqa: E402

logger = setup_logging(__name__, log_file="cortex_neural.log")
console = Console()

# Create Typer app
app = typer.Typer(
    name="neural",
    help="Neural Interface & Semantic Search",
    add_completion=False,
)


# Placeholder for EmbeddingPort (fallback quando SentenceTransformer falha)
class PlaceholderEmbeddingService(EmbeddingPort):
    """Placeholder embedding service - fallback for when real AI is unavailable."""

    def embed(self, text: str) -> list[float]:
        """Generate dummy embedding."""
        logger.warning("Using placeholder embedding service (not production-ready)")
        return [0.0] * 384  # Standard dimension for many models

    def batch_embed(self, texts: list[str]) -> list[list[float]]:
        """Generate dummy embeddings for batch."""
        return [self.embed(text) for text in texts]


def _print_system_status_banner(
    embedding_service: EmbeddingPort,
    vector_store: VectorStorePort,
    memory_type: str,
    db_path: Path,
) -> None:
    """Display system status banner with cognitive engine and memory info.

    Args:
        embedding_service: The embedding service being used
        vector_store: The vector store being used
        memory_type: Type of memory ('ram' or 'chroma')
        db_path: Path to database storage
    """
    # Determine cognitive engine status
    is_real_ai = not isinstance(embedding_service, PlaceholderEmbeddingService)
    ai_status = (
        "🟢 SentenceTransformers (Real AI)"
        if is_real_ai
        else "⚠️  Placeholder (Dummy Mode)"
    )
    ai_color = "green" if is_real_ai else "yellow"

    # Determine memory type
    from scripts.core.cortex.neural.adapters.memory import InMemoryVectorStore

    is_chroma = memory_type == "chroma" and not isinstance(
        vector_store,
        InMemoryVectorStore,
    )
    memory_status = (
        "🟢 ChromaDB (Persistent)" if is_chroma else "⚠️  RAM (Volatile + JSON)"
    )
    memory_color = "green" if is_chroma else "yellow"

    # Get model name
    model_name = "all-MiniLM-L6-v2" if is_real_ai else "N/A (No AI Model)"

    # Create status table
    status_lines = Text()
    status_lines.append("Motor Cognitivo: ", style="bold")
    status_lines.append(ai_status, style=ai_color)
    status_lines.append("\n")

    status_lines.append("Memória:        ", style="bold")
    status_lines.append(memory_status, style=memory_color)
    status_lines.append("\n")

    status_lines.append("Modelo:         ", style="bold")
    status_lines.append(model_name, style="cyan")
    status_lines.append("\n")

    status_lines.append("Caminho:        ", style="bold")
    status_lines.append(str(db_path), style="dim")

    panel = Panel(
        status_lines,
        title="[bold cyan]🧠 CORTEX Neural System Status[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)
    console.print()


def _get_embedding_service() -> EmbeddingPort:
    """Factory function to get the best available embedding service.

    Returns:
        SentenceTransformerAdapter if available, otherwise PlaceholderEmbeddingService

    Raises:
        typer.Exit: If no embedding service is available and strict mode is on
    """
    try:
        from scripts.core.cortex.neural.adapters.sentence_transformer import (
            SentenceTransformerAdapter,
        )

        logger.info("Loading SentenceTransformer adapter...")
        console.print("[cyan]🧠 Loading AI model (all-MiniLM-L6-v2)...[/cyan]")
        return SentenceTransformerAdapter()
    except Exception as e:
        logger.warning(f"Failed to load SentenceTransformer: {e}")
        console.print(
            "[yellow]⚠️  Could not load AI model. Using placeholder service.[/yellow]",
        )
        console.print(
            "[yellow]   For production use, ensure sentence-transformers "
            "is installed.[/yellow]",
        )
        return PlaceholderEmbeddingService()


def _get_vector_store(memory_type: str, persist_dir: Path) -> VectorStorePort:
    """Factory function to get the vector store based on memory type.

    Args:
        memory_type: Type of storage ('ram' or 'chroma')
        persist_dir: Directory for persistent storage

    Returns:
        VectorStorePort implementation (InMemoryVectorStore or ChromaDBVectorStore)
    """
    if memory_type == "chroma":
        try:
            from scripts.core.cortex.neural.adapters.chroma import ChromaDBVectorStore

            logger.info("Using ChromaDB persistent vector store")
            console.print("[cyan]💾 Using ChromaDB (persistent storage)...[/cyan]")
            return ChromaDBVectorStore(persist_directory=str(persist_dir))
        except ImportError:
            logger.warning("ChromaDB not available, falling back to RAM storage")
            console.print(
                "[yellow]⚠️  ChromaDB not installed. "
                "Using RAM storage instead.[/yellow]",
            )
            console.print(
                "[yellow]   Install with: pip install chromadb[/yellow]",
            )
            return InMemoryVectorStore(store_path=persist_dir / "store.json")
    else:
        # Default to RAM storage
        logger.info("Using in-memory vector store")
        console.print("[cyan]🧠 Using RAM storage (with JSON persistence)...[/cyan]")
        return InMemoryVectorStore(store_path=persist_dir / "store.json")


@app.command()
def index(
    docs_path: Annotated[
        Path,
        typer.Option(
            "--docs",
            "-d",
            help="Path to documentation directory",
        ),
    ] = Path("docs"),
    db_path: Annotated[
        Path,
        typer.Option(
            "--db",
            help="Path to vector database storage",
        ),
    ] = Path(".cortex/memory"),
    memory_type: Annotated[
        str,
        typer.Option(
            "--memory-type",
            "-m",
            help="Storage type: 'ram' (JSON) or 'chroma' (persistent DB)",
        ),
    ] = "chroma",
) -> None:
    """Index all documentation into the vector store.

    Scans documentation files and creates semantic embeddings for RAG.

    Args:
        docs_path: Path to documentation directory
        db_path: Path to vector database storage
        memory_type: Storage type ('ram' or 'chroma')
    """
    console.print("\n[bold cyan]🧬 CORTEX Neural Interface - Indexing[/bold cyan]\n")

    project_root = _project_root
    docs_absolute = project_root / docs_path

    if not docs_absolute.exists():
        console.print(
            f"[red]Error: Documentation path not found: {docs_absolute}[/red]",
        )
        raise typer.Exit(code=1)

    # Initialize VectorBridge with dependencies
    db_absolute = project_root / db_path
    db_absolute.mkdir(parents=True, exist_ok=True)

    embedding_service = _get_embedding_service()  # Use factory with fallback
    vector_store = _get_vector_store(memory_type, db_absolute)

    # Display system status banner
    _print_system_status_banner(
        embedding_service,
        vector_store,
        memory_type,
        db_absolute,
    )

    bridge = VectorBridge(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    # Scan knowledge entries
    console.print(f"[yellow]Scanning documentation at {docs_absolute}...[/yellow]")
    scanner = KnowledgeScanner(workspace_root=project_root)
    entries = scanner.scan(knowledge_dir=docs_absolute)

    if not entries:
        console.print("[yellow]No documentation entries found.[/yellow]")
        return

    console.print(f"[green]Found {len(entries)} documents to index.[/green]\n")

    # Index documents with progress bar
    indexed_count = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Indexing documents...", total=len(entries))

        for entry in entries:
            try:
                # Extract content and index (skip entries without file_path)
                if (
                    hasattr(entry, "cached_content")
                    and entry.cached_content
                    and entry.file_path
                ):
                    # Ensure file_path is a Path object
                    file_path = (
                        entry.file_path
                        if isinstance(entry.file_path, Path)
                        else Path(entry.file_path)
                    )
                    bridge.index_document(
                        content=entry.cached_content,
                        source_file=file_path,
                    )
                    indexed_count += 1
                progress.advance(task)
            except Exception as e:
                logger.error("Failed to index %s: %s", entry.file_path, e)
                console.print(f"[red]Error indexing {entry.file_path}: {e}[/red]")

    # Persist the vector store
    vector_store.persist()

    console.print(
        f"\n[bold green]✓ Successfully indexed {indexed_count}/{len(entries)} "
        f"documents[/bold green]",
    )


def _format_search_results(results: list[SearchResult]) -> Table:
    """Format search results as rich table with traceability.

    Args:
        results: List of SearchResult objects

    Returns:
        Rich Table with formatted results
    """
    table = Table(
        title="🎯 Resultados da Busca Semântica",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Confiança", justify="right", width=12)
    table.add_column("Fonte", style="cyan", width=35)
    table.add_column("Snippet", width=60)

    for i, result in enumerate(results, start=1):
        score = result.score
        chunk = result.chunk

        # Format confidence score with conditional color
        if score >= 0.8:
            score_style = "bold green"
        elif score >= 0.6:
            score_style = "yellow"
        else:
            score_style = "red"

        score_text = Text(f"{score:.2f}", style=score_style)

        # Format source with file:line traceability
        source_file = chunk.source_file.name if chunk.source_file else "Desconhecido"
        line_start = chunk.line_start if hasattr(chunk, "line_start") else 0
        source_location = (
            f"{source_file}:{line_start}" if line_start > 0 else source_file
        )

        # Format snippet with intelligent truncation
        snippet = chunk.content.strip().replace("\n", " ")
        if len(snippet) > 150:
            snippet = snippet[:147] + "..."

        table.add_row(
            str(i),
            score_text,
            source_location,
            snippet,
        )

    return table


@app.command()
def ask(
    query: Annotated[str, typer.Argument(help="Search query")],
    n_results: Annotated[
        int,
        typer.Option(
            "--top",
            "-n",
            help="Number of results to return",
        ),
    ] = 5,
    db_path: Annotated[
        Path,
        typer.Option(
            "--db",
            help="Path to vector database storage",
        ),
    ] = Path(".cortex/memory"),
    memory_type: Annotated[
        str,
        typer.Option(
            "--memory-type",
            "-m",
            help="Storage type: 'ram' (JSON) or 'chroma' (persistent DB)",
        ),
    ] = "chroma",
) -> None:
    """Perform semantic search on indexed documentation.

    Args:
        query: Natural language search query
        n_results: Number of top results to return
        db_path: Path to vector database storage
        memory_type: Storage type ('ram' or 'chroma')
    """
    console.print("\n[bold cyan]🧬 CORTEX Neural Interface - Search[/bold cyan]\n")
    console.print(f"[yellow]Query:[/yellow] {query}\n")

    project_root = _project_root
    db_absolute = project_root / db_path

    # Check if database exists (different for each type)
    if memory_type == "ram" and not (db_absolute / "store.json").exists():
        console.print(
            "[red]Error: Vector database not found. "
            "Run 'cortex neural index' first.[/red]",
        )
        raise typer.Exit(code=1)

    # Initialize VectorBridge with dependencies
    embedding_service = _get_embedding_service()  # Use factory with fallback
    vector_store = _get_vector_store(memory_type, db_absolute)

    # Display system status banner
    _print_system_status_banner(
        embedding_service,
        vector_store,
        memory_type,
        db_absolute,
    )

    # Load existing data for RAM storage
    if memory_type == "ram":
        vector_store.load()

    bridge = VectorBridge(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    # Query
    try:
        results = bridge.query_similar(query, limit=n_results)
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        logger.error("Query failed: %s", e)
        raise typer.Exit(code=1) from e

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    # Display results with rich traceability
    table = _format_search_results(results)
    console.print()
    console.print(table)
    console.print(
        f"\n[bold green]✓ {len(results)} resultados relevantes "
        f"encontrados[/bold green]",
    )


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
