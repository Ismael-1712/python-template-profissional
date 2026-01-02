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
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add project root to sys.path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner  # noqa: E402
from scripts.core.cortex.neural.adapters.memory import InMemoryVectorStore  # noqa: E402
from scripts.core.cortex.neural.ports import EmbeddingPort  # noqa: E402
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
            help="Path to ChromaDB storage",
        ),
    ] = Path(".cortex/vectordb"),
) -> None:
    """Index all documentation into the vector store.

    Scans documentation files and creates semantic embeddings for RAG.
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
    vector_store = InMemoryVectorStore(store_path=db_absolute / "store.json")
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
            help="Path to ChromaDB storage",
        ),
    ] = Path(".cortex/vectordb"),
) -> None:
    """Perform semantic search on indexed documentation.

    Args:
        query: Natural language search query
        n_results: Number of top results to return
        db_path: Path to vector database
    """
    console.print("\n[bold cyan]🧬 CORTEX Neural Interface - Search[/bold cyan]\n")
    console.print(f"[yellow]Query:[/yellow] {query}\n")

    project_root = _project_root
    db_absolute = project_root / db_path

    if not (db_absolute / "store.json").exists():
        console.print(
            "[red]Error: Vector database not found. "
            "Run 'cortex neural index' first.[/red]",
        )
        raise typer.Exit(code=1)

    # Initialize VectorBridge with dependencies
    embedding_service = _get_embedding_service()  # Use factory with fallback
    vector_store = InMemoryVectorStore(store_path=db_absolute / "store.json")
    vector_store.load()  # Load existing data

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

    # Display results
    table = Table(title="Search Results", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Score", justify="right", width=10)
    table.add_column("Source", style="cyan", width=30)
    table.add_column("Content Preview", width=60)

    for i, result in enumerate(results, start=1):
        score = result.score
        chunk = result.chunk
        metadata = chunk.metadata

        source = metadata.get("header", str(chunk.source_file))
        preview = (
            chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
        )

        table.add_row(
            str(i),
            f"{score:.4f}",
            source,
            preview,
        )

    console.print(table)
    console.print(f"\n[bold green]Found {len(results)} relevant results[/bold green]")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
