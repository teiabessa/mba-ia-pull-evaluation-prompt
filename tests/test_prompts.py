"""
tests/test_prompts.py

Testes automatizados para validacao estrutural do prompt otimizado.

Estes testes verificam se o arquivo prompts/bug_to_user_story_v2.yml
atende aos requisitos minimos do projeto de MBA, independentemente
dos scores de avaliacao das metricas (F1, Clarity, Precision, etc).

Tecnicas verificadas:
    - Role Prompting: persona de PM Senior definida no system prompt
    - Few-shot Learning: exemplos de entrada/saida presentes
    - Skeleton of Thought: formato de User Story e Criterios de Aceitacao
    - Chain of Thought: passos de raciocinio (verificado indiretamente pela estrutura)

Como executar:
    pytest tests/test_prompts.py -v
    pytest tests/test_prompts.py -v --tb=short

Requisitos:
    - pip install pytest pyyaml
    - Arquivo prompts/bug_to_user_story_v2.yml deve existir e estar preenchido
"""

import re
import pytest
import yaml
import sys
from pathlib import Path

# Adiciona src/ ao path para importar utils.py
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

# Configuracao dos caminhos
PROMPT_FILE = str(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")
PROMPT_KEY  = "bug_to_user_story_v2"


def load_prompts(file_path: str) -> dict:
    """
    Carrega o arquivo YAML do prompt e retorna seu conteudo completo.

    Args:
        file_path: Caminho absoluto para o arquivo .yml

    Returns:
        Dicionario com o conteudo completo do YAML, incluindo a chave raiz.

    Raises:
        FileNotFoundError: Se o arquivo nao existir
        yaml.YAMLError: Se o arquivo tiver sintaxe YAML invalida
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestPrompts:
    """
    Suite de testes para validacao estrutural do prompt v2.

    Cada teste valida um requisito especifico do enunciado do projeto.
    Todos os testes sao independentes e podem ser executados em qualquer ordem.

    Os testes validam o ARQUIVO LOCAL (prompts/bug_to_user_story_v2.yml),
    nao o prompt publicado no LangSmith Hub. Certifique-se de que o arquivo
    local esta atualizado antes de rodar os testes.
    """

    def test_prompt_has_system_prompt(self):
        """
        Verifica se o campo 'system_prompt' existe e nao esta vazio.

        Requisito: o prompt deve ter um system prompt com instrucoes claras.
        Um system prompt vazio indica que o prompt nao foi preenchido corretamente.

        Tecnica relacionada: todas as tecnicas dependem do system prompt.
        """
        data = load_prompts(PROMPT_FILE)
        prompt_data = data[PROMPT_KEY]

        assert "system_prompt" in prompt_data, (
            "Campo 'system_prompt' nao encontrado no YAML.\n"
            "Adicione o campo 'system_prompt' com as instrucoes do prompt."
        )

        system = prompt_data["system_prompt"]
        assert isinstance(system, str) and len(system.strip()) > 0, (
            "O campo 'system_prompt' esta vazio.\n"
            "Preencha com persona, regras, esqueleto e exemplos few-shot."
        )

    def test_prompt_has_role_definition(self):
        """
        Verifica se o prompt define uma persona clara para o modelo.

        Requisito: o prompt deve usar Role Prompting para definir o papel
        do modelo antes de qualquer instrucao.

        Exemplos validos:
            - 'Voce e um Product Manager Senior...'
            - 'Voce e uma especialista em Agile...'
            - 'Seu papel e transformar bugs em user stories...'

        Tecnica relacionada: Role Prompting.
        """
        data = load_prompts(PROMPT_FILE)
        system = data[PROMPT_KEY]["system_prompt"].lower()

        patterns = [
            r"voce e um",
            r"voce e uma",
            r"você é um",
            r"você é uma",
            r"seu papel e",
            r"sua funcao e",
            r"sua função é",
            r"atue como",
        ]
        found = any(re.search(p, system) for p in patterns)
        assert found, (
            "O system_prompt nao define uma persona.\n"
            "Adicione Role Prompting como: 'Voce e um Product Manager Senior...'\n"
            "Isso ancora o modelo em um frame de referencia consistente."
        )

    def test_prompt_mentions_format(self):
        """
        Verifica se o prompt especifica o formato de saida esperado.

        Requisito: o prompt deve exigir o formato padrao de User Story Agil:
            - Cabecalho: 'Como um [persona], eu quero [acao], para que [beneficio]'
            - Criterios: formato Dado/Quando/Entao (BDD/Gherkin)

        Tecnica relacionada: Skeleton of Thought — define a estrutura da resposta.
        """
        data = load_prompts(PROMPT_FILE)
        system = data[PROMPT_KEY]["system_prompt"].lower()

        # Verifica formato de User Story
        assert "como um" in system and "eu quero" in system and "para que" in system, (
            "O prompt nao menciona o formato 'Como um... eu quero... para que...'.\n"
            "Inclua o esqueleto de User Story Agil no system prompt.\n"
            "Exemplo: 'Como um [persona], eu quero [acao], para que [beneficio].'"
        )

        # Verifica formato de Criterios de Aceitacao
        assert "dado que" in system and "quando" in system, (
            "O prompt nao menciona o formato Dado/Quando/Entao.\n"
            "Inclua o padrao de Criterios de Aceitacao (BDD/Gherkin):\n"
            "'- Dado que [contexto]\n- Quando [acao]\n- Entao [resultado]'"
        )

    def test_prompt_has_few_shot_examples(self):
        """
        Verifica se o prompt contem exemplos de entrada/saida (Few-shot Learning).

        Requisito: o projeto exige obrigatoriamente Few-shot Learning com
        pelo menos 2 exemplos claros de Bug -> User Story.

        Os exemplos devem:
            - Estar numerados (Exemplo 1, Exemplo 2, ...)
            - Mostrar o relato do bug como entrada (marcador 'Bug:')
            - Mostrar a User Story esperada como saida

        Tecnica relacionada: Few-shot Learning — obrigatoria pelo enunciado.
        """
        data = load_prompts(PROMPT_FILE)
        system = data[PROMPT_KEY]["system_prompt"].lower()

        # Conta exemplos numerados
        count = len(re.findall(r"exemplo\s+\d+", system))
        assert count >= 2, (
            f"Encontrados apenas {count} exemplo(s) no system_prompt.\n"
            "O projeto exige no minimo 2 exemplos de Few-shot Learning.\n"
            "Adicione exemplos numerados cobrindo diferentes complexidades do dataset."
        )

        # Verifica marcador de entrada
        assert "bug:" in system, (
            "Os exemplos nao contem o marcador 'Bug:' antes do relato.\n"
            "Cada exemplo deve mostrar claramente:\n"
            "  Bug: [relato do bug]\n"
            "  [User Story esperada]"
        )

    def test_prompt_no_todos(self):
        """
        Garante que nenhum marcador de trabalho pendente foi deixado no prompt.

        Requisito: o prompt deve estar 100% preenchido antes de ser publicado.
        Marcadores como [TODO], [PLACEHOLDER] ou [FIXME] indicam trabalho incompleto.

        Verifica tanto o system_prompt quanto o user_prompt.
        """
        data = load_prompts(PROMPT_FILE)
        prompt_data = data[PROMPT_KEY]

        full_text = (
            prompt_data.get("system_prompt", "")
            + "\n"
            + prompt_data.get("user_prompt", "")
        )

        todo_patterns = [
            r"\[TODO\]",
            r"\[PLACEHOLDER\]",
            r"\[FIXME\]",
            r"\[PREENCHER\]",
            r"\[INSERT\]",
        ]

        found = [p for p in todo_patterns if re.search(p, full_text, re.IGNORECASE)]
        assert not found, (
            f"Marcadores de trabalho pendente encontrados: {found}\n"
            "Remova ou substitua todos os marcadores antes de publicar o prompt.\n"
            "O prompt deve estar completamente preenchido."
        )

    def test_minimum_techniques(self):
        """
        Verifica se o YAML declara pelo menos 2 tecnicas de prompt engineering.

        Requisito: o campo 'techniques_applied' deve listar no minimo 2 tecnicas,
        sendo 'few_shot_learning' obrigatoria pelo enunciado do projeto.

        Tecnicas aceitas:
            - few_shot_learning (OBRIGATORIA)
            - role_prompting
            - chain_of_thought
            - skeleton_of_thought
            - tree_of_thought
            - react

        Alem de declarar as tecnicas nos metadados, elas devem estar
        efetivamente aplicadas no conteudo do prompt (verificado pelos outros testes).
        """
        data = load_prompts(PROMPT_FILE)
        prompt_data = data[PROMPT_KEY]

        # Valida estrutura geral via utils.py
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, (
            f"validate_prompt_structure falhou com os seguintes erros:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

        # Verifica quantidade minima de tecnicas
        techniques = prompt_data.get("techniques_applied", [])
        assert len(techniques) >= 2, (
            f"Apenas {len(techniques)} tecnica(s) declarada(s): {techniques}\n"
            "O projeto exige pelo menos 2 tecnicas de prompt engineering.\n"
            "Adicione ao campo 'techniques_applied' no YAML."
        )

        # Verifica que few_shot_learning esta presente (obrigatoria)
        normalized = [t.lower().replace("-", "_") for t in techniques]
        assert "few_shot_learning" in normalized, (
            f"'few_shot_learning' nao encontrado em techniques_applied: {techniques}\n"
            "Few-shot Learning e OBRIGATORIA conforme o enunciado do projeto.\n"
            "Adicione 'few_shot_learning' ao campo 'techniques_applied' no YAML."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
