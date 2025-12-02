"""Matcher para cruzar configurações encontradas com documentação.

Detecta "Configurações Órfãs" - configurações que aparecem no código mas não
estão documentadas em nenhum arquivo .md em docs/.
"""

import logging
import re
import time
from pathlib import Path

from scripts.core.guardian.models import ConfigFinding

logger = logging.getLogger(__name__)


class DocumentationMatcher:
    """Cruza ConfigFinding com documentação para detectar órfãos.

    Um ConfigFinding é considerado órfão se:
    - A chave (nome da variável) não aparece em nenhum documento .md
    - Busca é case-sensitive para evitar falsos positivos
    """

    def __init__(self, docs_path: Path) -> None:
        """Inicializa o matcher.

        Args:
            docs_path: Caminho para o diretório de documentação (docs/)
        """
        self.docs_path = docs_path
        self._doc_content_cache: dict[Path, str] = {}

    def find_orphans(
        self,
        findings: list[ConfigFinding],
    ) -> tuple[list[ConfigFinding], dict[str, list[Path]]]:
        """Encontra configurações órfãs (não documentadas).

        Args:
            findings: Lista de ConfigFinding do scanner

        Returns:
            Tupla contendo:
            - Lista de ConfigFinding órfãos (não encontrados na doc)
            - Dict mapeando chave -> lista de arquivos onde foi documentada
        """
        start_time = time.time()

        # Carrega toda a documentação
        self._load_documentation()

        orphans: list[ConfigFinding] = []
        documented: dict[str, list[Path]] = {}

        for finding in findings:
            doc_files = self._find_in_documentation(finding.key)

            if not doc_files:
                # Não encontrado em nenhum documento -> órfão
                orphans.append(finding)
            else:
                # Encontrado -> documentar onde está
                documented[finding.key] = doc_files

        duration_ms = (time.time() - start_time) * 1000
        self._log_match_summary(findings, orphans, documented, duration_ms)

        return orphans, documented

    def _load_documentation(self) -> None:
        """Carrega todo o conteúdo de arquivos .md no cache."""
        if not self.docs_path.exists():
            return

        for md_file in self.docs_path.rglob("*.md"):
            try:
                self._doc_content_cache[md_file] = md_file.read_text(
                    encoding="utf-8",
                )
            except (OSError, UnicodeDecodeError) as e:
                # Ignora erros de leitura silenciosamente
                # (pode haver arquivos binários ou corrompidos)
                logger.warning("Erro ao ler %s: %s", md_file, e)

    def _find_in_documentation(self, key: str) -> list[Path]:
        """Procura uma chave de configuração na documentação.

        Args:
            key: Nome da variável (ex: "DB_HOST")

        Returns:
            Lista de arquivos onde a chave foi encontrada
        """
        found_in: list[Path] = []

        # Busca exata (case-sensitive) para evitar falsos positivos
        # Exemplo: "DB_HOST" não deve casar com "db_hostname"
        pattern = re.compile(rf"\b{re.escape(key)}\b")

        for doc_file, content in self._doc_content_cache.items():
            if pattern.search(content):
                found_in.append(doc_file)

        return found_in

    def _log_match_summary(
        self,
        findings: list[ConfigFinding],
        orphans: list[ConfigFinding],
        documented: dict[str, list[Path]],
        duration_ms: float,
    ) -> None:
        """Imprime resumo do matching."""
        total = len(findings)
        orphan_count = len(orphans)
        documented_count = len(documented)

        logger.info("\n📊 Resultado do Matching:")
        logger.info("   Total de configurações: %d", total)
        logger.info("   ✅ Documentadas: %d", documented_count)
        logger.info("   ❌ Órfãs: %d", orphan_count)
        logger.info("   ⏱️  Duração: %.2fms", duration_ms)


class MatchResult:
    """Resultado do processo de matching.

    Attributes:
        orphans: Configurações não documentadas
        documented: Mapa de configurações documentadas -> arquivos
        match_duration_ms: Tempo de execução do matching
    """

    def __init__(
        self,
        orphans: list[ConfigFinding],
        documented: dict[str, list[Path]],
        match_duration_ms: float,
    ) -> None:
        """Inicializa o resultado."""
        self.orphans = orphans
        self.documented = documented
        self.match_duration_ms = match_duration_ms

    @property
    def has_orphans(self) -> bool:
        """Verifica se há configurações órfãs."""
        return len(self.orphans) > 0

    def summary(self) -> str:
        """Resumo do matching."""
        return (
            f"Matching completo: "
            f"{len(self.orphans)} órfãs, "
            f"{len(self.documented)} documentadas "
            f"({self.match_duration_ms:.2f}ms)"
        )
