"""
Script para fazer pull de prompts do LangSmith Prompt Hub.
Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml
SIMPLIFICADO: Usa serializacao nativa do LangChain para extrair prompts.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Configuracao

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = PROMPTS_DIR / "bug_to_user_story_v1.yml"

# Cabecalho de comentarios escrito no topo do YAML gerado
YAML_HEADER = """\
# Este arquivo contem o prompt inicial de BAIXA QUALIDADE que voce deve otimizar.
# Os problemas sao intencionais (ex: {bug_report} duplicado no system e user prompt,
# instrucoes vagas, falta de exemplos, sem persona definida).
# Use-o como base para entender o que precisa ser melhorado na v2.
"""


# Helpers

def extract_messages(prompt) -> tuple[str, str]:
    """
    Extrai system_prompt e user_prompt de um ChatPromptTemplate.

    Itera sobre prompt.messages e identifica cada parte pelo nome da classe
    (SystemMessagePromptTemplate -> system, HumanMessagePromptTemplate -> user).

    Args:
        prompt: ChatPromptTemplate retornado pelo hub.pull()

    Returns:
        (system_content, user_content) como strings
    """
    system_content = ""
    user_content = ""

    for msg in prompt.messages:
        # O texto fica em msg.prompt.template para *PromptTemplate
        # ou em msg.content para mensagens concretas
        if hasattr(msg, "prompt") and hasattr(msg.prompt, "template"):
            text = msg.prompt.template
        elif hasattr(msg, "content"):
            text = msg.content
        else:
            text = str(msg)

        role = msg.__class__.__name__.lower()
        if "system" in role:
            system_content = text
        elif "human" in role or "user" in role:
            user_content = text

    return system_content, user_content


# Core

def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt SOURCE_PROMPT do LangSmith Hub e salva como YAML local.

    O arquivo gerado segue o formato:
        bug_to_user_story_v1:
          description: ...
          system_prompt: |
            ...
          user_prompt: "..."
          version: "v1"
          created_at: "2025-01-15"
          tags: [...]

    Returns:
        True se sucesso, False caso contrario
    """
    print_section_header(f"Pull: {SOURCE_PROMPT}")
    print(f"Baixando prompt: {SOURCE_PROMPT}")

    # 1. Baixar via hub.pull()
    prompt = hub.pull(SOURCE_PROMPT)
    print("Prompt baixado com sucesso.")

    # 2. Extrair system e user
    system_content, user_content = extract_messages(prompt)

    # 3. Montar dicionario no formato exato do projeto
    #    chave raiz = nome curto do prompt (sem o owner/)
    #    campos aninhados incluindo metadados
    prompt_key = SOURCE_PROMPT.split("/")[-1]

    prompt_data = {
        prompt_key: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_content,
            "user_prompt": user_content,
            # Metadados
            "version": "v1",
            "created_at": "2025-01-15",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    # 4. Salvar com save_yaml (de utils.py) + escrever cabecalho de comentarios
    #    save_yaml nao suporta comentarios, entao: salva o corpo primeiro,
    #    le de volta, e reescreve com o cabecalho no topo.
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    success = save_yaml(prompt_data, str(OUTPUT_FILE))
    if not success:
        return False

    original = OUTPUT_FILE.read_text(encoding="utf-8")
    OUTPUT_FILE.write_text(YAML_HEADER + original, encoding="utf-8")

    print(f"Salvo em: {OUTPUT_FILE}")
    return True


# Main

def main():
    """Funcao principal"""
    print_section_header("Pull de Prompts - LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print("\nPull concluido com sucesso.")
        print(f"Arquivo: {OUTPUT_FILE}")
        print("\nProximo passo: revise prompts/bug_to_user_story_v1.yml")
        print("e crie a versao otimizada em prompts/bug_to_user_story_v2.yml.")
        return 0
    else:
        print("\nPull falhou. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())