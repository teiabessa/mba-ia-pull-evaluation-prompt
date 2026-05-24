"""
Script para depurar e inspecionar o dataset de avaliação no LangSmith.

Este script:
1. Conecta ao LangSmith usando as credenciais do .env
2. Carrega o dataset configurado em DATASET_NAME
3. Para cada exemplo do dataset, executa o prompt e exibe:
   - INPUT: o bug report enviado ao modelo
   - REFERENCE: a user story esperada (ground truth)
   - OUTPUT GERADO: a user story gerada pelo modelo

Finalidade:
- Validar se o modelo está gerando os outputs corretos
- Comparar visualmente output gerado vs reference esperada
- Diagnosticar exemplos com scores baixos no evaluate.py
- Confirmar que o dataset contém os exemplos corretos e na ordem certa

Uso:
  python src/debug_dataset.py

Pré-requisitos:
  - Ter rodado push_prompts.py para publicar o prompt no LangSmith Hub
  - Ter rodado evaluate.py pelo menos uma vez para criar o dataset
  - DATASET_NAME configurado no .env (ex: bug_to_user_story-eval)

Configure as credenciais no arquivo .env:
  LANGSMITH_API_KEY=...
  LANGSMITH_PROJECT=...
  DATASET_NAME=...
  USERNAME_LANGSMITH_HUB=...
"""

import os
from dotenv import load_dotenv
from langsmith import Client
from langchain import hub
from utils import get_llm

load_dotenv()


def main():

    client = Client()

    dataset_name = os.getenv("DATASET_NAME")

    # Carrega o prompt do LangSmith Hub
    username = os.getenv("USERNAME_LANGSMITH_HUB", "")
    prompt_name = f"{username}/bug_to_user_story_v2"

    print("\n" + "=" * 80)
    print("DEBUG LANGSMITH DATASET + OUTPUT DO MODELO")
    print("=" * 80)

    print(f"\nDataset: {dataset_name}")
    print(f"Prompt:  {prompt_name}")

    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    print(f"Provider: {provider} | Model: {model}")

    # Carrega prompt e LLM
    try:
        prompt = hub.pull(prompt_name)
        llm = get_llm(temperature=0)
        chain = prompt | llm
        print("Prompt e LLM carregados com sucesso.")
    except Exception as e:
        print(f"Erro ao carregar prompt/LLM: {e}")
        chain = None

    examples = list(client.list_examples(dataset_name=dataset_name))
    print(f"Total examples: {len(examples)}")
    print("\n" + "=" * 80)

    for i, example in enumerate(examples, 1):

        print(f"\nEXAMPLE {i}")
        print("-" * 80)
        print(f"Example ID: {example.id}")

        try:
            bug_report = example.inputs.get("bug_report", "N/A")
        except:
            bug_report = "N/A"

        try:
            reference = example.outputs.get("reference", "N/A")
        except:
            reference = "N/A"

        print("\nINPUT:")
        print(bug_report)

        print("\nREFERENCE:")
        print(reference)

        # Gera output do modelo
        if chain and bug_report != "N/A":
            try:
                response = chain.invoke({"bug_report": bug_report})
                print("\nOUTPUT GERADO PELO MODELO:")
                print(response.content)
            except Exception as e:
                print(f"\nOUTPUT GERADO PELO MODELO: ERRO — {e}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
