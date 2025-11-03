# --- Estágio 1: Build (O "Construtor") ---
# Usamos uma imagem completa para construir as dependências
FROM python:3.11-slim-bookworm as builder

# Expõe a porta padrão do FastAPI/Uvicorn
EXPOSE 8000

# Define o diretório de trabalho
WORKDIR /app

# Impede o Python de gerar arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Impede o Python de armazenar logs em buffer
ENV PYTHONUNBUFFERED=1

# Instala o 'pip' mais recente
RUN pip install --upgrade pip

# Copia o "mapa" do projeto e instala *apenas* as dependências
# Isso aproveita o cache do Docker. As dependências só são reinstaladas
# se o 'pyproject.toml' mudar.
COPY pyproject.toml .
RUN pip install --no-cache-dir .[dev]

# --- Estágio 2: Final (A "Aplicação") ---
# Usamos a mesma imagem 'slim' para um resultado final menor
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copia o ambiente virtual e as dependências do "Construtor"
# (Nota: Esta é uma técnica. Alguns preferem copiar apenas os pacotes.)
# Vamos simplificar e copiar apenas os arquivos do projeto.

# Copia *apenas* as dependências instaladas do estágio 'builder'
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia o código-fonte da aplicação
COPY src/ ./src/

# Comando final para iniciar o servidor Uvicorn
# Ouve em todas as interfaces (0.0.0.0) na porta 8000
# Aponta para o 'app' dentro do 'src/main.py' (que criaremos a seguir)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
