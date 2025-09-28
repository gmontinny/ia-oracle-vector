# Modelo Arquitetural - Busca Semântica com Oracle 23ai

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐         ┌─────────────────────────┐    │
│  │     APP SERVICE     │         │   ORACLE-DB SERVICE     │    │
│  │                     │         │                         │    │
│  │  ┌───────────────┐  │         │  ┌───────────────────┐  │    │
│  │  │   main.py     │  │         │  │  Oracle 23ai Free │  │    │
│  │  │   (CLI)       │  │◄────────┤  │                   │  │    │
│  │  └───────────────┘  │         │  │  ┌─────────────┐  │  │    │
│  │          │          │         │  │  │   FREEPDB1  │  │  │    │
│  │          ▼          │         │  │  │             │  │  │    │
│  │  ┌───────────────┐  │         │  │  │ ┌─────────┐ │  │  │    │
│  │  │   ingest.py   │  │         │  │  │ │products │ │  │  │    │
│  │  │   search.py   │  │         │  │  │ │ table   │ │  │  │    │
│  │  └───────────────┘  │         │  │  │ └─────────┘ │  │  │    │
│  │          │          │         │  │  └─────────────┘  │  │    │
│  │          ▼          │         │  └───────────────────┘  │    │
│  │  ┌───────────────┐  │         └─────────────────────────┘    │
│  │  │ AI Models:    │  │                                        │
│  │  │ - Sentence    │  │         ┌─────────────────────────┐    │
│  │  │   Transformers│  │         │     EXTERNAL APIs       │    │
│  │  │ - OpenAI API  │  │◄────────┤                         │    │
│  │  └───────────────┘  │         │  ┌───────────────────┐  │    │
│  └─────────────────────┘         │  │   OpenAI API      │  │    │
│                                  │  │ text-embedding-   │  │    │
│  ┌─────────────────────┐         │  │   3-small         │  │    │
│  │    DATA VOLUME      │         │  └───────────────────┘  │    │
│  │                     │         └─────────────────────────┘    │
│  │  products.csv       │                                        │
│  └─────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes da Arquitetura

### 1. Camada de Orquestração (Docker Compose)
- **Responsabilidade**: Gerenciar e conectar todos os serviços
- **Configuração**: Variáveis de ambiente, volumes, redes
- **Serviços**: `oracle-db` e `app`

### 2. Camada de Aplicação (App Service)

#### 2.1 Interface CLI (main.py)
```python
Comandos:
├── ingest  → Executa ingestão de dados
└── search  → Executa busca semântica
```

#### 2.2 Módulo de Ingestão (ingest.py)
```
Fluxo de Ingestão:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ Lê CSV      │ -> │ Gera         │ -> │ Conecta     │ -> │ Insere no    │
│ products    │    │ Embeddings   │    │ Oracle DB   │    │ Banco        │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

**Responsabilidades**:
- Leitura do arquivo CSV
- Geração de embeddings (Sentence Transformers ou OpenAI)
- Criação da tabela com dimensões dinâmicas
- Inserção de dados usando `array.array`

#### 2.3 Módulo de Busca (search.py)
```
Fluxo de Busca:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ Recebe      │ -> │ Gera         │ -> │ Executa     │ -> │ Retorna      │
│ Consulta    │    │ Embedding    │    │ SQL Vetorial│    │ Resultados   │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

**Responsabilidades**:
- Vetorização da consulta do usuário
- Execução de busca por similaridade
- Formatação e exibição dos resultados

### 3. Camada de Dados

#### 3.1 Oracle Database 23ai
```sql
Estrutura da Tabela:
┌─────────────┬─────────────────┬──────────────────┬─────────────────────┐
│ product_id  │ product_name    │ description      │ embedding           │
│ (NUMBER)    │ (VARCHAR2(255)) │ (VARCHAR2(1000)) │ (VECTOR(384/1536))  │
├─────────────┼─────────────────┼──────────────────┼─────────────────────┤
│ 1           │ Laptop          │ High-performance │ [0.1, -0.2, ...]   │
│ 2           │ Mouse           │ Wireless mouse   │ [0.3, 0.1, ...]    │
└─────────────┴─────────────────┴──────────────────┴─────────────────────┘
```

**Características**:
- Tipo `VECTOR` nativo para embeddings
- Função `VECTOR_DISTANCE` para cálculo de similaridade
- Suporte a diferentes dimensões (384 ou 1536)

#### 3.2 Volume de Dados
- **products.csv**: Dados fonte dos produtos
- **Persistência**: Volume Docker para dados do Oracle

### 4. Camada de IA

#### 4.1 Sentence Transformers (Local)
```
Modelo: all-MiniLM-L6-v2
├── Dimensões: 384
├── Tipo: Open Source
└── Execução: Local
```

#### 4.2 OpenAI API (Externa)
```
Modelo: text-embedding-3-small
├── Dimensões: 1536
├── Tipo: API Comercial
└── Execução: Remota
```

## Fluxos de Dados

### Fluxo de Ingestão
```
1. CSV Reader → 2. AI Model → 3. Vector Generation → 4. Oracle Insert
   products.csv    (ST/OpenAI)    array.array('f')    VECTOR column
```

### Fluxo de Busca
```
1. User Query → 2. AI Model → 3. Vector Search → 4. Results
   "laptop"        (ST/OpenAI)    VECTOR_DISTANCE    Top 5 products
```

## Configuração e Variáveis de Ambiente

```yaml
Variáveis Principais:
├── USE_OPENAI: true/false (Seleção do modelo)
├── OPENAI_API_KEY: sk-proj-... (Chave da API)
├── ORACLE_USER: sys (Usuário do banco)
├── ORACLE_PASSWORD: oracle (Senha do banco)
└── ORACLE_DSN: oracle-db:1521/FREEPDB1 (Conexão)
```

## Padrões Arquiteturais Aplicados

### 1. **Separation of Concerns**
- Cada módulo tem uma responsabilidade específica
- CLI, ingestão e busca são independentes

### 2. **Strategy Pattern**
- Seleção dinâmica entre Sentence Transformers e OpenAI
- Configuração via variáveis de ambiente

### 3. **Factory Pattern**
- Criação de embeddings baseada na configuração
- Ajuste automático de dimensões

### 4. **Container Pattern**
- Isolamento de dependências via Docker
- Orquestração de serviços

## Escalabilidade e Performance

### Pontos Fortes
- **Oracle 23ai**: Performance nativa para operações vetoriais
- **Docker**: Facilita deployment e escalabilidade horizontal
- **Modularidade**: Permite otimizações independentes

### Considerações para Produção
- **Cache de Embeddings**: Evitar recálculos desnecessários
- **Batch Processing**: Processar múltiplas consultas simultaneamente
- **Índices Vetoriais**: Usar índices especializados do Oracle para grandes volumes
- **Load Balancing**: Múltiplas instâncias da aplicação

## Segurança

### Implementado
- Conexão segura com Oracle via SYSDBA
- API Key da OpenAI via variáveis de ambiente
- Isolamento via containers Docker

### Recomendações Adicionais
- Usar secrets management (Docker Secrets, Kubernetes Secrets)
- Implementar rate limiting para APIs externas
- Adicionar autenticação na aplicação
- Criptografia de dados sensíveis

## Monitoramento e Observabilidade

### Métricas Sugeridas
- Tempo de resposta das consultas
- Taxa de sucesso das chamadas à OpenAI API
- Utilização de recursos do Oracle
- Latência de geração de embeddings

### Logs Importantes
- Erros de conexão com banco de dados
- Falhas na API da OpenAI
- Performance de consultas vetoriais
- Estatísticas de uso por modelo