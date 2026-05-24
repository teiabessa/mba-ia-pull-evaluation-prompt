"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Le os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PUBLICO para o LangSmith Hub
4. Adiciona metadados (tags, tecnicas utilizadas)

Compativel com langsmith==0.2.7 e langchain==0.3.13.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from langsmith.evaluation import evaluate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "bug_to_user_story_v2.yml")
PROMPT_KEY  = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura basica de um prompt.

    Args:
        prompt_data: Dados do prompt (conteudo aninhado, sem a chave raiz)

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ["description", "system_prompt", "user_prompt", "version"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatorio faltando: {field}")

    system_prompt = prompt_data.get("system_prompt", "").strip()
    if not system_prompt:
        errors.append("system_prompt esta vazio")

    if "TODO" in system_prompt:
        errors.append("system_prompt ainda contem TODOs nao resolvidos")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(
            f"Minimo de 2 tecnicas requeridas, encontradas: {len(techniques)}."
        )

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (publico).

    Monta um ChatPromptTemplate a partir dos campos system_prompt e user_prompt
    do YAML e publica via hub.push() com tags.

    Nota: hub.push() no langsmith==0.2.7 aceita apenas:
    prompt_name, object, tags e new_repo_is_public.
    O campo description nao e suportado nessa versao via hub.push().
    Para atualizar a descricao acesse o dashboard do LangSmith Hub.

    Args:
        prompt_name: Nome completo no Hub, ex: "username/bug_to_user_story_v2"
        prompt_data: Dados do prompt (conteudo aninhado, sem a chave raiz)

    Returns:
        True se sucesso, False caso contrario
    """
    print_section_header(f"Push: {prompt_name}")

    system_prompt = prompt_data["system_prompt"]
    user_prompt   = prompt_data["user_prompt"]

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human",  user_prompt),
    ])

    version    = prompt_data.get("version", "v2")
    techniques = prompt_data.get("techniques_applied", [])
    tags = [version] + techniques

    description = prompt_data.get(
        "description",
        "Prompt otimizado para converter relatos de bugs em User Stories"
    )

    print(f"Publicando prompt: {prompt_name}")
    print(f"Tags: {tags}")
    print(f"Descricao: {description}")

    hub.push(
        prompt_name,
        chat_prompt,
        tags=tags,
        new_repo_is_public=True,
    )

    print(f"Push realizado com sucesso.")
    print(f"Acesse: https://smith.langchain.com/hub/{prompt_name}")
    return True


def main():
    """Funcao principal"""
    print_section_header("Push de Prompts - LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("USERNAME_LANGSMITH_HUB nao configurado no .env")
        return 1

    username_slug = username.lower().replace(" ", "-")
    if username_slug != username:
        print(f"Username ajustado para slug: '{username}' -> '{username_slug}'")
        username = username_slug

    print(f"Carregando: {PROMPT_FILE}")
    yaml_data = load_yaml(PROMPT_FILE)

    if yaml_data is None:
        print("Falha ao carregar o arquivo YAML.")
        return 1

    prompt_data = yaml_data.get(PROMPT_KEY)
    if prompt_data is None:
        print(f"Chave '{PROMPT_KEY}' nao encontrada no YAML.")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("Prompt invalido. Corrija os erros antes de publicar:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Prompt validado com sucesso.")

    prompt_name = f"{username}/{PROMPT_KEY}"

    try:
        push_prompt_to_langsmith(prompt_name, prompt_data)
    except Exception as e:
        print(f"Erro durante o push: {e}")
        return 1

    print("\nPush concluido com sucesso.")
    print(f"Prompt disponivel em: https://smith.langchain.com/hub/{prompt_name}")
    print("\nProximo passo: execute a avaliacao:")
    print("  python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())