# ======================================================================
# STAGE 1: Build da Aplicação
# ======================================================================
# Usamos a imagem oficial do Python 3.11 (slim) como base
FROM python:3.11-slim as builder

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Atualiza o pip e instala o 'build' para construir o pacote
RUN pip install --upgrade pip build

# Copia os arquivos necessários para o build
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src

# Constrói o "wheel" (pacote instalável)
# Isso cria um arquivo .whl em /app/dist
RUN python -m build

# ======================================================================
# STAGE 2: Imagem Final de Produção
# ======================================================================
# Começamos de novo com uma base limpa (slim)
FROM python:3.11-slim

WORKDIR /app

# Copia APENAS o pacote construído (wheel) do stage 'builder'
COPY --from=builder /app/dist/*.whl .

# Instala o pacote (que, por sua vez, puxa 'fastapi' e 'uvicorn')
# Usamos --no-cache-dir para manter a imagem final leve
RUN pip install --no-cache-dir *.whl

# Expõe a porta 8000 (padrão do FastAPI/Uvicorn)
EXPOSE 8000

# Comando para iniciar a aplicação usando o Uvicorn (servidor de produção)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
