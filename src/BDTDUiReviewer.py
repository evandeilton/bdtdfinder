import os
import csv
import json
import requests
import shutil
from datetime import datetime
from typing import List, Dict, Optional

# Reaproveitamos os prompts e funções de BDTDReviewer

class BDTDUiReviewer:
    """
    Classe adaptada para a UI, que gera a revisão de literatura a partir de um CSV 
    (results_page.csv) contendo apenas os trabalhos selecionados pelo usuário.
    """
    
    def __init__(
        self,
        theme: str,
        output_lang: str = "pt-BR",
        download_pdfs: bool = True,
        scrape_text: bool = True,
        output_dir: str = "output",
        debug: bool = False,
        openrouter_api_key: Optional[str] = None,
        model: Optional[str] = "google/gemini-2.0-pro-exp-02-05:free",
        log_callback = None
    ):
        """
        Inicializa o BDTDUiReviewer com os parâmetros fornecidos.
        
        Args:
            theme: Tema da revisão
            output_lang: Idioma da revisão (default: pt-BR)
            download_pdfs: Se True, baixa PDFs (não utilizado na lógica de revisão, mas mantido para compatibilidade)
            scrape_text: Se True, extrai texto (não utilizado aqui, pois a raspagem já ocorreu)
            output_dir: Diretório de saída onde o CSV e a revisão serão salvos
            debug: Modo debug
            openrouter_api_key: Chave API para chamadas ao OpenRouter (obrigatória)
            model: Modelo a ser utilizado para geração da revisão
            log_callback: Função de log, se necessário
        """
        self.theme = theme
        self.output_lang = output_lang
        self.download_pdfs = download_pdfs
        self.scrape_text = scrape_text
        self.output_dir = output_dir
        self.debug = debug
        self.model = model
        self.log_callback = log_callback
        
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key é necessária")
        
        self.available_models = [
            "google/gemini-2.0-pro-exp-02-05:free",
            "anthropic/claude-3.5-sonnet",
            "openai/chatgpt-4o-latest",
            "google/gemini-2.0-flash-thinking-exp:free",
            "cognitivecomputations/dolphin3.0-mistral-24b:free"
        ]
        
        self.SYSTEM_PROMPT_EXTRACTOR = """You are tasked with extracting metadata from academic thesis/dissertation repository text and structuring it into a standardized JSON format. The input will be a long string containing webpage content from academic repositories.
Expected JSON structure:
{
"title": <string>,
"abstract": <string>,
"author": <string>,
"date": <string>,
"level": <string>
}

Look for these common identifiers in the text:
- Title: "Título", "Title"
- Date/Year: "Data de defesa", "Date", "Ano"
- Author: "Autor", "Author", "Nome completo"
- Abstract: "Resumo", "Abstract"
- Level: "Mestrado", "Doutorado", "Graduação", "Pós-graduação", "Master", "Doctorate", "Graduation", "Post-graduation"

When information is not found, use "Not informed" as default value.
Maintain the original language for abstract and other text."""
        
        self.SYSTEM_PROMPT_REVIEWER = f"""
SYSTEM PROMPT: LITERATURE REVIEW SYNTHESIS AGENT V2

[CORE DEFINITION]
IDENTITY: Expert Literature Review Synthesizer for {self.theme}
PURPOSE: Generate evidence-based, comprehensive literature analysis combining:
- Theoretical frameworks
- Empirical evidence
- Methodological approaches
- Research gaps

[OUTPUT REQUIREMENTS]
FORMAT:
- Language: {self.output_lang}
- Length: 8000 tokens (Use API max tokens limit)
- Structure: Academic review paper
- Citations: APA style with DOIs
- NOTE: No excuses, no shortcuts, no plagiarism, no fake text, no extra questions 

DOCUMENT STRUCTURE (FULL Markdown in {self.output_lang}):
1. Title (theme-focused, concise)
2. Abstract (250 words max)
3. Methodology
   - Source selection criteria
   - Analysis framework
4. Main Sections (H2 headers)
   - Theoretical Framework
   - Methodological Analysis
   - Empirical Evidence
   - Research Gaps
5. Discussion
6. Conclusion
7. References

[ANALYTICAL PARAMETERS]
SOURCE HANDLING:
- Primary: User-provided texts
- Validation: Peer-review status check
- Conflicts: Document and analyze
- Integration: Cross-reference findings

MATHEMATICAL NOTATION:
- Inline: $expression$ for simple math
- Block: $$ for complex equations
- Context: Brief explanation for each formula
- Validation: Mathematical consistency check

QUALITY CHECKS:
1. Source Reliability
   - Peer-review status
   - Publication metrics
   - Author credentials

2. Content Validity
   - Methodological soundness
   - Statistical accuracy
   - Logical consistency
   - Evidence support

3. Output Validation
   - Citation completeness
   - Mathematical accuracy
   - Structural coherence
   - Theme alignment

[BEHAVIORAL CONSTRAINTS]
- Use only verified sources
- Maintain academic objectivity
- Flag uncertain claims
- Document limitations
- Highlight contradictions

[OUTPUT VALIDATION CHECKLIST (INTERNAL USE ONLY)]
□ Theme relevance
□ Structure compliance
□ Citation completeness
□ Mathematical accuracy
□ Evidence support
□ Gap identification
□ Future directions
□ Language consistency
□ Format adherence
□ Word count compliance

END OF PROMPT
"""

    def _log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        print(message)
        
    def _get_models_list(self) -> List[str]:
        if self.model:
            return [self.model] + [m for m in self.available_models if m != self.model]
        return self.available_models

    def _call_openrouter(self, prompt: str, system_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "http://localhost:8080",
            "Content-Type": "application/json"
        }
        models = self._get_models_list()
        for model in models:
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 8000
                    }
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if self.debug:
                    print(f"Erro com modelo {model}: {e}")
                continue
        raise Exception("Nenhum modelo disponível respondeu corretamente")
    
    def _extract_metadata(self, text: str) -> Dict:
        if self.debug:
            print("    [DEBUG] Enviando texto para extração (primeiros 200 caracteres):")
            print(f"    {text[:200]}...\n")
        try:
            response = self._call_openrouter(text, self.SYSTEM_PROMPT_EXTRACTOR)
            if self.debug:
                print("    [DEBUG] Resposta bruta da API:")
                print(f"    {response}\n")
            if response.startswith("```"):
                lines = response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response = "\n".join(lines).strip()
            metadata = json.loads(response)
            if self.debug:
                print("    [DEBUG] Metadados extraídos:")
                print(f"    {metadata}\n")
            return metadata
        except Exception as e:
            if self.debug:
                print(f"Erro na extração de metadados: {e}")
            return {
                "title": "Not informed",
                "abstract": "Not informed",
                "author": "Not informed",
                "date": "Not informed",
                "level": "Not informed"
            }
    
    def _generate_review(self, texts: List[Dict]) -> str:
        formatted_texts = "\n\n".join([
            f"Title: {t['title']}\nAuthor: {t['author']}\nDate: {t['date']}\nAbstract: {t['abstract']}\nLevel: {t['level']}\n"
            for t in texts
        ])
        try:
            return self._call_openrouter(formatted_texts, self.SYSTEM_PROMPT_REVIEWER)
        except Exception as e:
            raise Exception(f"Erro ao gerar revisão: {e}")
    
    def run_ui(self) -> str:
        """
        Executa o processo de revisão de literatura com os textos previamente selecionados.
        Lê o CSV 'results_page.csv' presente em output_dir, extrai metadados de cada entrada
        e gera a revisão final.
        
        Returns:
            str: Caminho do arquivo Markdown com a revisão
        """
        try:
            results_file = os.path.join(self.output_dir, "results_page.csv")
            texts = []
            with open(results_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, 1):
                    if not row['results'].strip():
                        print(f"Linha {i} ignorada: coluna 'results' vazia.")
                        continue
                    if self.debug:
                        print(f"Processando texto {i}...")
                    metadata = self._extract_metadata(row['results'])
                    texts.append(metadata)
                    if self.debug:
                        print(f"✓ Metadados extraídos: {metadata['title'][:50]}...\n")
            
            print("\n==> Iniciando geração da revisão de literatura (UI)...")
            print(f"    Usando modelo: {self.model or 'padrão'}")
            print(f"    Idioma: {self.output_lang}")
            print(f"    Total de textos: {len(texts)}")
            review_text = self._generate_review(texts)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f"literature_review_{timestamp}.md")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(review_text)
            return output_file
        except Exception as e:
            raise Exception(f"Erro no processo de revisão UI: {e}")
