#!/usr/bin/env python3
"""
Hook SessionStart — cria automaticamente CLAUDE.md em novos projetos.
Ignora: diretório home, ~/.claude, diretórios de sistema.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Diretórios a ignorar (não criar CLAUDE.md nesses)
IGNORED_DIRS = {
    str(Path.home()),
    str(Path.home() / ".claude"),
    str(Path.home() / "AppData"),
    str(Path.home() / "Downloads"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Desktop"),
    "/tmp",
    "/",
    "C:\\",
    "C:\\Windows",
    "C:\\Users",
}

def should_create(cwd: str) -> bool:
    """Verifica se deve criar CLAUDE.md neste diretório."""
    # Ignorar diretórios do sistema
    for ignored in IGNORED_DIRS:
        if cwd == ignored or cwd.startswith(ignored + os.sep):
            if cwd == ignored:
                return False

    # Ignorar o próprio ~/.claude
    claude_dir = str(Path.home() / ".claude")
    if cwd == claude_dir or cwd.startswith(claude_dir + os.sep):
        return False

    # Ignorar node_modules e similares
    bad_segments = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", ".next"}
    parts = set(Path(cwd).parts)
    if parts & bad_segments:
        return False

    return True

def get_project_name(cwd: str) -> str:
    return Path(cwd).name

def create_claude_md(cwd: str):
    """Cria o CLAUDE.md com template inicial."""
    claude_md_path = Path(cwd) / "CLAUDE.md"
    if claude_md_path.exists():
        return  # Já existe, não sobrescrever

    project_name = get_project_name(cwd)
    date_str = datetime.now().strftime("%Y-%m-%d")

    content = f"""# {project_name}

> Criado automaticamente em {date_str}. Atualize com as informações do projeto.

## Visão Geral

<!-- Descreva o projeto: o que faz, para quem, qual problema resolve -->

## Stack Tecnológica

<!-- Liste as principais tecnologias usadas -->

## Regras do Projeto

<!-- Regras específicas deste projeto que o Claude deve seguir -->

1.
2.
3.

## Arquitetura

<!-- Descreva a estrutura de pastas e módulos principais -->

## Integrações

<!-- APIs externas, serviços, MCPs utilizados -->

## Contexto de Negócio

<!-- Informações de negócio relevantes para o desenvolvimento -->

## Notas Importantes

<!-- Decisões técnicas, débitos, pendências -->

---
*Memória ativa do projeto — mantenha este arquivo atualizado conforme o projeto evolui.*
"""

    claude_md_path.write_text(content, encoding="utf-8")
    print(f"\n📄 CLAUDE.md criado automaticamente em: {cwd}\n   → Abra e preencha as informações do projeto para ativar a memória contextual.\n")

def main():
    cwd = os.getcwd()

    if not should_create(cwd):
        sys.exit(0)

    # Só cria se parecer um projeto (tem arquivos de código ou config)
    project_indicators = {
        "package.json", "pyproject.toml", "setup.py", "requirements.txt",
        "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
        ".env", ".env.local", "docker-compose.yml", "Dockerfile",
        "next.config.ts", "next.config.js", "vite.config.ts",
        "tsconfig.json", ".gitignore",
    }

    try:
        files_in_dir = set(os.listdir(cwd))
    except PermissionError:
        sys.exit(0)

    has_indicator = bool(files_in_dir & project_indicators)
    has_src = "src" in files_in_dir or "app" in files_in_dir or "lib" in files_in_dir

    if has_indicator or has_src:
        create_claude_md(cwd)

if __name__ == "__main__":
    main()
