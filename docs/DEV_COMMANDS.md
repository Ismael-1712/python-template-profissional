# Sistema de Comandos de Desenvolvimento

Este documento descreve o sistema unificado de comandos de desenvolvimento implementado no template Python profissional.

## Visão Geral

O `dev_commands.py` fornece uma interface consistente e segura para executar comandos comuns de desenvolvimento, CI/CD e qualidade de código. Ele substitui o conceito problemático do arquivo original `copilot_chat_commands.py` com uma implementação robusta e idiomática.

## Uso Básico

```bash
# Listar todos os comandos disponíveis
python3 scripts/dev_commands.py list

# Executar linting
python3 scripts/dev_commands.py lint

# Executar testes
python3 scripts/dev_commands.py test

# Dry run (mostrar o que seria executado)
python3 scripts/dev_commands.py lint --dry-run

# Exportar configuração para VS Code
python3 scripts/dev_commands.py --export-vscode
```

## Comandos Disponíveis

### Qualidade de Código (QUALITY)

- **`lint`** - Executa análise estática com ruff
- **`format`** - Formata código usando ruff (substituto do black)

### Testes (TESTING)

- **`test`** - Executa testes com pytest
- **`test-cov`** - Executa testes com cobertura de código

### Build (BUILD)

- **`build`** - Constrói pacote distribuível
- **`install-dev`** - Instala projeto em modo desenvolvimento

## Melhorias de Segurança

Comparado ao sistema original, esta implementação inclui:

1. **Validação de Comandos**: Todos os comandos são validados antes da execução
2. **Template Seguro**: Uso de `shlex.split()` para parsing seguro de comandos
3. **Logging Estruturado**: Sistema de logging adequado em vez de prints
4. **Timeouts**: Proteção contra comandos que ficam presos
5. **Tratamento de Erros**: Manejo adequado de exceções

## Integração com VS Code

Para integrar com o VS Code, execute:

```bash
python3 scripts/dev_commands.py --export-vscode
```

Isto criará um arquivo `.vscode/tasks.json` com tasks configuradas para todos os comandos.

## Extensibilidade

Para adicionar novos comandos, registre-os no método `_register_default_commands()`:

```python
self.register_command(DevCommand(
    name="novo-comando",
    description="Descrição do comando",
    category=CommandCategory.CODE_QUALITY,
    command_template="comando {args}",
))
```

## Padrões Seguidos

- **Idempotência**: Comandos podem ser executados múltiplas vezes
- **Portabilidade**: Compatível com sistemas POSIX
- **Type Hints**: Anotações de tipo completas
- **Logging**: Uso de logging em vez de prints
- **Pathlib**: Uso de `pathlib` em vez de `os.path`

## Branch de Destino

Este script deve ser incluído no **branch `main`** do template, pois é **GENÉRICO** e útil para qualquer tipo de projeto Python.
