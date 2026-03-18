"""Generate mkdocs reference pages from package modules.

Run this script before building documentation:
    python docs/make_package_docs.py
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODULES = [
    ("scrutiny.models", "Models"),
    ("scrutiny.config", "Config"),
    ("scrutiny.adapters.base", "Adapters"),
    ("scrutiny.chunking", "Chunking"),
    ("scrutiny.detection", "Detection"),
    ("scrutiny.classification", "Classification"),
]

REFERENCE_DIR = Path("docs/reference")


def generate_reference_pages() -> None:
    """Generate mkdocstrings reference pages for each module.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    nav_entries = []
    for module_path, title in MODULES:
        slug = module_path.replace(".", "_")
        page_path = REFERENCE_DIR / f"{slug}.md"
        content = f"# {title}\n\n::: {module_path}\n"
        page_path.write_text(content, encoding="utf-8")
        nav_entries.append(f"  - {title}: reference/{slug}.md")
        logger.info("Generated %s", page_path)

    nav_yaml = "\n".join(nav_entries)
    print("Add to mkdocs.yaml nav section:\n")
    print(nav_yaml)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_reference_pages()
