---
type: guide
id: mutation-testing-guide
status: active
date: 2026-01-01
author: SRE Team
version: "1.0.0"
title: "Mutation Testing - Guia de Uso"
description: "Como utilizar Mutation Testing para validar a qualidade dos testes unitários"
category: quality-assurance
tags:
  - testing
  - mutation
  - quality
last_updated: 2026-01-01
---

# 🧟 Mutation Testing - Guia de Uso

## 📚 O Que É Mutation Testing?

**Mutation Testing** é uma técnica avançada de validação da qualidade dos **testes**, não do código de produção. É literalmente "testar os testes".

### Analogia: Guarda vs Inspetor

Imagine que seu código é uma fortaleza e seus testes são os guardas que protegem essa fortaleza contra invasores (bugs).

- **Testes Tradicionais (Guarda):** Verificam se tudo está funcionando corretamente no cenário feliz.
- **Mutation Testing (Inspetor):** Simula invasores tentando invadir a fortaleza por diferentes ângulos para verificar se os guardas realmente estão atentos.

### Como Funciona?

1. **Mutmut** modifica automaticamente seu código (cria "mutantes")
   - Exemplo: Troca `>` por `>=`, muda `True` para `False`, remove condições
2. Executa sua suite de testes contra cada mutante
3. **Mutante Morto (✅):** Seus testes detectaram a mudança → **Ótimo!**
4. **Mutante Sobrevivente (❌):** Seus testes passaram mesmo com o bug → **Problema!**

### Exemplo Prático

```python
# Código Original
def validar_idade(idade: int) -> bool:
    return idade >= 18

# Mutante 1: Troca >= por >
def validar_idade(idade: int) -> bool:
    return idade > 18  # 🧟 Mutante!
```

Se você tiver um teste apenas com `idade=20`, ele passará para **ambas as versões**. O mutante sobreviveu! Você precisa de um teste com `idade=18` para matá-lo.

---

## ⚠️ Quando Usar (Matriz de Decisão)

| Cenário | Usar Mutation? | Justificativa |
|---------|----------------|---------------|
| **Refatoração de Código Core** | ✅ SIM | Garante que os testes realmente protegem contra regressões |
| **Bug Crítico Repetido** | ✅ SIM | Valida se os testes agora detectariam esse tipo de bug |
| **Novo Módulo Crítico (Segurança/Pagamento)** | ✅ SIM | Alta criticidade exige alta confiança nos testes |
| **Código Trivial (Getters/Setters)** | ❌ NÃO | Overhead não justifica o benefício |
| **Protótipos/Spikes** | ❌ NÃO | Código temporário não requer essa profundidade |
| **CI Automático** | ❌ **NUNCA** | Processo lento e caro (pode levar horas) |

### Regra de Ouro

> **Mutation Testing é uma ferramenta de auditoria cirúrgica, não um validador diário.**

---

## 🛠️ Como Usar

### ⚙️ Configuração Central (pyproject.toml)

**IMPORTANTE:** Desde o Mutmut v3.x, toda a configuração é feita **exclusivamente** via `pyproject.toml`. Argumentos CLI antigos (como `--paths-to-mutate`) foram removidos.

**Exemplo de configuração:**

```toml
[tool.mutmut]
runner = "python -m pytest -x"  # Comando para executar testes
tests_dir = "tests/"            # Diretório de testes
paths_to_mutate = ["scripts/"]  # ⚠️ DEVE ser uma lista!
backup = false                  # Não criar backups
```

**Dica:** Para alterar os caminhos a serem mutados, edite `paths_to_mutate` no `pyproject.toml`.

---

### Comando Simplificado (Recomendado)

```bash
# Executar mutation testing em um arquivo específico
make mutation target=scripts/utils/filesystem.py

# Visualizar relatório HTML no navegador
make mutation-report
```

**Comportamento:**

- ✅ Limpa cache anterior automaticamente
- ✅ Executa mutmut apenas no arquivo especificado
- ✅ Exibe resultados no terminal
- ✅ Sugere comando para abrir relatório HTML

### Visualizar Relatório Detalhado

Após executar `make mutation`, você pode visualizar os resultados detalhados:

```bash
make mutation-report
```

Isso irá:

1. Gerar relatório HTML em `html/index.html`
2. Abrir automaticamente no navegador padrão (Linux/Mac/WSL)
3. Em caso de falha, exibir o caminho completo do arquivo

### Sem Target (Erro Didático)

```bash
$ make mutation
❌ Erro: Missing target. Usage: make mutation target=path/to/file.py
```

### Modo Manual Avançado (Opcional)

Se precisar de controle fino, use `mutmut` diretamente:

```bash
# 1. Limpar cache
rm -f .mutmut-cache

# 2. Executar mutation em arquivo específico
mutmut run scripts/utils/filesystem.py

# 3. Ver resultados
mutmut results

# 4. Inspecionar mutante específico
mutmut show <id>

# 5. Gerar HTML
mutmut html
```

**⚠️ ATENÇÃO:** Na v3.x, NÃO use flags como `--paths-to-mutate`. Configure tudo no `pyproject.toml`.

---

## 📊 Interpretando Resultados

### Saída Típica

```
🧟 Mutation Testing - Manual Local Execution
🎯 Target: scripts/utils/filesystem.py

Legend for output:
🎉 Killed mutants.   The goal is for everything to end up in this bucket.
⏰ Timeout.          Test suite took 10 times as long as the baseline so were killed.
🤔 Suspicious.       Tests took a long time, but not long enough to be killed.
🙁 Survived.         This means your tests need to be expanded.
🔇 Skipped.          Skipped.

mutmut cache is out of date, clearing it...
1. TIMEOUT
2. KILLED
3. KILLED
4. SURVIVED
```

### Ações Recomendadas

- **KILLED (🎉):** Tudo certo! Mantenha assim.
- **SURVIVED (🙁):** **Ação Requerida!** Adicione teste específico para cobrir esse caso.
- **TIMEOUT (⏰):** Possível loop infinito. Revise a lógica ou o teste.
- **SUSPICIOUS (🤔):** Teste demorado. Considere otimização.

### Exemplo de Correção

```python
# ❌ Teste Fraco (Mutante Sobrevive)
def test_validar_idade():
    assert validar_idade(20) is True

# ✅ Teste Robusto (Mata o Mutante)
def test_validar_idade():
    assert validar_idade(20) is True  # Acima do limite
    assert validar_idade(18) is True  # Exatamente no limite (mata mutante >= > >)
    assert validar_idade(17) is False # Abaixo do limite
```

---

## 🚫 Política de CI/CD

**❌ Mutation Testing NÃO deve rodar automaticamente no GitHub Actions.**

### Por Quê?

- ⏱️ **Lentidão:** Pode levar de 30 minutos a várias horas.
- 💰 **Custo:** Consome minutos de CI desnecessariamente.
- 🔄 **Frequência:** Não é necessário validar mutantes a cada commit.
- 🎯 **Propósito:** É uma ferramenta de auditoria pontual, não de validação contínua.

### Quando Foi Removido?

Anteriormente existia um workflow `.github/workflows/mutation-audit.yml` que foi **removido** em conformidade com esta política.

---

## 🎓 Melhores Práticas

1. **Execute Localmente Antes de PRs Críticos**
   - Especialmente em refatorações de módulos core.

2. **Comece Pequeno**
   - Use `target=arquivo_especifico.py` ao invés de diretórios inteiros.

3. **Documente Mutantes Sobreviventes Esperados**
   - Alguns mutantes podem ser falsos positivos (ex: logging).
   - Documente no código por que aquele mutante é aceitável.

4. **Não Busque 100% de Morte**
   - Objetivo razoável: 80-90% de mutantes mortos.
   - Custo-benefício diminui conforme se aproxima de 100%.

5. **Combine com Coverage**
   - Coverage diz **O QUE** foi executado.
   - Mutation diz **SE O QUE** foi executado realmente validou o comportamento.

---

## 🔗 Referências

- [Mutmut Documentation](https://mutmut.readthedocs.io/)
- [Mutation Testing Best Practices](https://thevaluable.dev/mutation-testing-python/)
- Arquivo de configuração: `pyproject.toml` → `[tool.mutmut]`

---

## 📞 Suporte

Dúvidas ou problemas com Mutation Testing?

1. Consulte este guia primeiro
2. Revise a documentação do Mutmut
3. Abra uma discussão no repositório com o label `quality-assurance`

---

**Última Atualização:** 2026-01-01
**Responsável:** SRE Team
**Status:** Ativo
