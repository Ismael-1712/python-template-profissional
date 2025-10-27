# --- Estágio 1: Build (O "Construtor") ---
# Usamos uma imagem completa para construir as dependências
FROM python:3.11-slim-bookworm as builder

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
COPY . .

# O CMD (Comando) dependerá do seu projeto.
# Isto é um placeholder que apenas mostra a versão do Python.
CMD ["python", "--version"]
