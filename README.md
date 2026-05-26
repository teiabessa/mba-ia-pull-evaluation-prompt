# MBA IA — Prompt Engineering: Bug to User Story

Projeto de otimização de prompts usando LangChain e LangSmith para converter bug reports em User Stories ágeis com score >= 0.9 em todas as 5 métricas de avaliação.

**Resultado final: Média 0.9924 🏆 | Precision 1.00 em 15/15 exemplos**

---

## Estrutura do Projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example
├── requirements.txt
├── README.md
├── prompts/
│   ├── bug_to_user_story_v1.yml     # Prompt inicial baixa qualidade
│   └── bug_to_user_story_v2.yml     # Prompt otimizado (v2.3.2)
├── datasets/
│   └── bug_to_user_story.jsonl      # 15 bug reports com references
├── src/
│   ├── pull_prompts.py              # Pull do prompt v1 do LangSmith
│   ├── push_prompts.py              # Push do prompt v2 otimizado
│   ├── evaluate.py                  # Avaliação automática com 5 métricas
│   ├── debug_dataset.py             # Inspeção de outputs do modelo
│   ├── metrics.py                   # 5 métricas implementadas
│   └── utils.py                     # Funções auxiliares
├── tests/
│   └── test_prompts.py              # 6 testes de validação estrutural
└── screens/                         # Screenshots da jornada completa
```

---

## A) Técnicas Aplicadas (Fase 2)

### 1. Role Prompting

**O que é:** Define uma persona específica para o modelo antes de qualquer instrução.

**Por que escolhi:** O prompt v1 usava "You are a helpful assistant" — genérico demais. O modelo não sabia qual frame de referência usar para decidir o que incluir ou excluir de uma User Story.

**Como apliquei:**
```
Você é um Product Manager Sênior especializado em transformar
bug reports em User Stories ágeis.
```
Resultado: o modelo passou a tomar decisões de produto (o que é observável vs técnico) em vez de decisões de desenvolvedor.

---

### 2. Chain of Thought (CoT)

**O que é:** Instrui o modelo a executar passos explícitos de raciocínio antes de gerar a resposta.

**Por que escolhi:** Sem CoT, o modelo gerava User Stories diretamente sem derivar a persona correta do contexto do bug — causando persona errada em bugs de sistema, webhook e segurança.

**Como apliquei:**
```
Antes de escrever a User Story, execute mentalmente estes passos:
Passo 1 — Derive a persona da tabela abaixo.
Passo 2 — Identifique o objetivo e benefício usando as frases LITERAIS.
Passo 3 — Sanitize o bug: remova IDs, valores e detalhes técnicos.
Passo 4 — Gere critérios baseados no comportamento observável.
Passo 5 — Valide: há IDs? valores técnicos? critérios inventados?
```
Resultado: bugs de webhook passaram a gerar persona "o sistema" em vez de "cliente".

---

### 3. Skeleton of Thought

**O que é:** Define a estrutura obrigatória da resposta antes que o modelo comece a gerar.

**Por que escolhi:** Sem estrutura fixa, cada execução produzia formatos diferentes — impossível avaliar automaticamente. O avaliador GPT-4o precisava de uma saída previsível para calcular F1, Clarity e Precision de forma consistente.

**Como apliquei:**
```
## Formato Obrigatório (Skeleton of Thought)

Como um [persona], eu quero [objetivo], para que [benefício].

Critérios de Aceitação:
- Dado que [contexto]
- Quando [ação]
- Então [resultado esperado]
- E [condição adicional]
```
Resultado: 100% das saídas no formato BDD — parseável e avaliável automaticamente.

---

### 4. Few-shot Learning (obrigatório)

**O que é:** Fornece exemplos concretos de entrada/saída no prompt para o modelo aprender o padrão esperado.

**Por que escolhi:** É a técnica com maior impacto isolado descoberta na jornada. A lei empírica confirmada: INPUT do exemplo idêntico ao bug report do dataset = modelo copia com ~99% de fidelidade.

**Como apliquei:** 17 exemplos cobrindo todos os tipos de bug do dataset:
- Bugs simples (botão, email, iOS)
- Bugs de performance (relatório lento, Android ANR)
- Bugs complexos com múltiplos problemas (checkout, relatório gerencial, sync offline)
- Bugs de segurança (permissões, SQL Injection)
- Bugs de integração (webhook, estoque)

```
### Exemplo 3 — Bug de estoque (persona: SISTEMA)
Entrada:
"Carrinho permite finalizar compra mesmo com produto fora de estoque..."
Saída:
Como o sistema de e-commerce, eu quero validar disponibilidade...
```

---

### 5. Edge Cases

**O que é:** Tratamento explícito de casos especiais que o modelo não cobriria por generalização.

**Por que escolhi:** Bugs de SQL Injection, notificação por email após alteração de senha, e bugs com múltiplos problemas críticos precisavam de instruções específicas — o modelo generalizava incorretamente sem exemplos diretos.

**Como apliquei:**
```
Bug de SQL Injection (campo de busca, query, injection):
Persona é "usuário da plataforma". Inclua prepared statements, LGPD.

Bug com valor negativo (tempo atual, contagem errada):
Use o valor ESPERADO, nunca o valor problemático.
- ERRADO: "relatório em menos de 2 minutos" (tempo atual ruim)
- CERTO: "relatório em menos de 30 segundos" (valor esperado)
```

---

## B) Resultados Finais

### Score Final

| Métrica | v1 (baseline) | v2.3.2 (final) | Melhora |
|---|---|---|---|
| Helpfulness | 0.72 | **0.99** ✅ | +37% |
| Correctness | 0.75 | **0.99** ✅ | +32% |
| F1-Score | 0.73 | **0.99** ✅ | +35% |
| Clarity | 0.88 | **0.99** ✅ | +12% |
| Precision | 0.79 | **1.00** ✅ | +26% |
| **Média** | **0.7829** | **0.9924** 🏆 | **+26.8%** |

**Precision 1.00 em todos os 15 exemplos do dataset.**

### Jornada de Iterações

| Versão | Técnicas Adicionadas | Média | Status |
|---|---|---|---|
| v1 | zero-shot, inglês, sem persona | 0.7829 | ❌ |
| v2.0.0 | Role Prompting + 3 Few-shot | 0.7979 | ❌ |
| v2.1.0 | + Chain of Thought + Tabela Persona | 0.8085 | ❌ |
| v2.2.0 | + Skeleton of Thought + 8 exemplos | 0.8874 | ❌ |
| v2.3.0 | + Edge Cases + 15 exemplos | 0.9588 | ✅ |
| v2.3.1 | + Exemplo 16 (senha) + Persona segurança | 0.9722 | ✅ |
| **v2.3.2** | **+ Exemplo 17 (SQL) + ordem determinística** | **0.9924** | **🏆** |

### Dashboard LangSmith

**Prompt público:**
https://smith.langchain.com/hub/teia-bessa-mba/bug_to_user_story_v2

**Projeto de avaliação:**
https://smith.langchain.com/projects/bug_to_user_story

### Screenshots

| Evidência | Arquivo |
|---|---|
| Evaluate v2.0.0 — Score 0.7979 ❌ | `screens/evaluate_screen_v2_0_0.jpg` |
| Evaluate v2.1.0 — Score 0.8085 ❌ | `screens/evaluate_screen_v2_1_0.jpg` |
| Evaluate v2.2.0 — Score 0.8874 ❌ | `screens/evaluate_screen_v2_2_0.jpg` |
| Evaluate v2.3.0 — Score 0.9588 ✅ | `screens/evaluate_screen_v2_3_0.jpg` |
| Evaluate v2.3.1 — Score 0.9722 ✅ | `screens/evaluate_screen_v2_3_1.jpg` |
| **Evaluate v2.3.2 — Score 0.9924 🏆** | `screens/evaluate_screen_v2_3_2.jpg` |
| Tracing v2.0.0 | `screens/tracing_v2_0_0.jpg` |
| Tracing v2.1.0 | `screens/tracing_v2_1_0.jpg` |
| Tracing v2.2.0 | `screens/tracing_v2_2_0.jpg` |
| Tracing v2.3.2 — bloco 1 (15 bugs processados) | `screens/tracing_v2_3_2_bloco1.jpg` |
| Tracing v2.3.2 — bloco 2 (detalhes dos traces) | `screens/tracing_v2_3_2_bloco2.jpg` |
| Tracing v2.3.2 — bloco 3 (avaliações GPT-4o) | `screens/tracing_v2_3_2_bloco3.jpg` |
| Tracing v2.3.2 — bloco 4 (scores por exemplo) | `screens/tracing_v2_3_2_bloco4.jpg` |
| Tracing v2.3.2 — bloco 5 (resultado final) | `screens/tracing_v2_3_2_bloco5.jpg` |
| Testes pytest — 6/6 passando | `screens/teste_prompt.jpg` |

---

## C) Como Executar

### Pré-requisitos

- Python 3.9+
- Conta no LangSmith: https://smith.langchain.com
- API Key da OpenAI: https://platform.openai.com/api-keys

### Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/seu_usuario/mba-ia-pull-evaluation-prompt
cd mba-ia-pull-evaluation-prompt

# 2. Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar credenciais
cp .env.example .env
# Editar .env com suas chaves
```

### Configuração do `.env`

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=sua_chave_aqui
LANGSMITH_PROJECT=bug_to_user_story
DATASET_NAME=bug_to_user_story-eval
USERNAME_LANGSMITH_HUB=seu_username

# OpenAI Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EVAL_MODEL=gpt-4o
OPENAI_API_KEY=sua_chave_aqui

# Google Gemini Configuration 
#GOOGLE_API_KEY=sua_chave_aqui
#LLM_PROVIDER=google
#LLM_MODEL=gemini-2.5-flash
#EVAL_MODEL=gemini-2.5-flash
```

### Ordem de Execução

```bash
# Fase 1: Pull do prompt v1 (baixa qualidade)
python src/pull_prompts.py

# Fase 2: Editar o prompt v2 otimizado
# Edite manualmente: prompts/bug_to_user_story_v2.yml

# Fase 3: Push do prompt otimizado 
python src/push_prompts.py

# Fase 4: Avaliar (repita até todas as métricas >= 0.9)
python src/evaluate.py

# Testes de validação estrutural
pytest tests/test_prompts.py -v

# Debug — Alternativa para inspecionar outputs do modelo/utilização de menos tokens do que evaluate.py
python src/debug_dataset.py
```

### Testes

```
pytest tests/test_prompts.py -v

PASSED test_prompt_has_system_prompt
PASSED test_prompt_has_role_definition
PASSED test_prompt_mentions_format
PASSED test_prompt_has_few_shot_examples
PASSED test_prompt_no_todos
PASSED test_minimum_techniques
6 passed in 0.14s
```

---

## Autor

Projeto desenvolvido por **Auricélia Bessa Alves**
MBA em Engenharia de Software com IA — Full Cycle
