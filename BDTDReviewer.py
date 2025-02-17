import os
import csv
import json
import datetime
import argparse
from typing import List, Dict, Optional
import requests
from datetime import datetime
import shutil

# Imports dos módulos existentes
from BDTDfinder import BDTDCrawler
from BDTDdownloader import PDFDownloader
from BDTDResearchAgent import BDTDAgent

class BDTDReviewer:
    """
    Classe responsável por realizar revisões sistemáticas de literatura baseadas em
    teses e dissertações da BDTD (Biblioteca Digital Brasileira de Teses e Dissertações).
    
    A classe integra as funcionalidades de busca, download e análise de textos,
    utilizando agentes de IA para gerar uma revisão de literatura estruturada.
    
    Attributes:
        theme (str): Tema da revisão sistemática
        output_lang (str): Idioma de saída da revisão (default: pt-BR)
        max_pages (int): Número máximo de páginas para busca
        max_title_review (int): Número máximo de títulos para revisão
        download_pdfs (bool): Flag para realizar download dos PDFs
        scrape_text (bool): Flag para extrair texto das páginas
        output_dir (str): Diretório para arquivos de saída
        debug (bool): Flag para modo debug
        openrouter_api_key (str): Chave API do OpenRouter
    """
    
    def __init__(
        self,
        theme: str,
        output_lang: str = "pt-BR",
        max_pages: int = 5,
        max_title_review: int = 5,
        download_pdfs: bool = True,
        scrape_text: bool = True,
        output_dir: str = "output",
        debug: bool = False,
        openrouter_api_key: Optional[str] = None,
        model: Optional[str] = "google/gemini-2.0-pro-exp-02-05:free"
    ):
        """
        Inicializa o BDTDReviewer com os parâmetros fornecidos.
        
        Args:
            theme: Tema da revisão sistemática
            output_lang: Idioma de saída (default: pt-BR)
            max_pages: Limite de páginas para busca (default: 50)
            max_title_review: Limite de títulos para revisão (default: 5)
            download_pdfs: Se True, baixa PDFs encontrados (default: False)
            scrape_text: Se True, extrai texto das páginas (default: True)
            output_dir: Diretório de saída (default: "output")
            debug: Modo debug (default: False)
            openrouter_api_key: Chave API do OpenRouter (opcional)
        """
        self.theme = theme
        self.output_lang = output_lang
        self.max_pages = max_pages
        self.max_title_review = max_title_review
        self.download_pdfs = download_pdfs
        self.scrape_text = scrape_text
        self.output_dir = output_dir
        self.debug = debug
        self.model = model
        
        # Configuração do OpenRouter
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key é necessária")
            
        # Modelos disponíveis ordenados por preferência
        self.available_models = [
            "google/gemini-2.0-pro-exp-02-05:free",
            "anthropic/claude-3.5-sonnet",
            "openai/chatgpt-4o-latest",
            "google/gemini-2.0-flash-thinking-exp:free",
            "cognitivecomputations/dolphin3.0-mistral-24b:free"
        ]
        
        # Prompts do sistema
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
AGENT_DEFINITION:
ROLE: Expert Research Synthesizer specialized in academic, scientific and systematic literature reviews for {theme}
OBJECTIVE: Generate comprehensive, evidence-based literature analysis combining:
- Theoretical frameworks and mathematical models
- Empirical evidence and statistical findings
- Methodological approaches and innovations
- Critical gaps and future directions
- Think as a meta analysis or meta-analysis with holistic approach aboute {theme}
EXPERTISE: Advanced knowledge in research methodology, statistical analysis, and {theme}

OUTPUT_SPECIFICATIONS:
LANGUAGE: {self.output_lang}
LENGTH: 5000-10000 words (CRITICAL)
FORMAT: Academic deep and holistic literature review

MATHEMATICAL_NOTATION:
1. Inline Mathematics:
    - Basic: $x = \beta_0 + \beta_1x_1$
    - Greek letters: $\alpha$, $\beta$, $\gamma$, $\theta$
    - Subscripts/superscripts: $x_{{i,j}}^2$
    - Functions: $f(x)$, $\log(x)$, $\exp(x)$

2. Block Mathematics:
    - Equations: $$y = \beta_0 + \sum_{{i=1}}^n \beta_i x_i + \epsilon$$
    - Matrices: $$\mathbf{{X}} = \begin{{bmatrix}} x_{{11}} & x_{{12}} \\ x_{{21}} & x_{{22}} \end{{bmatrix}}$$
    - Integrals: $$\int_{{a}}^{{b}} f(x) dx$$
    - Statistical notation: $$\hat{{\beta}} = (\mathbf{{X}}'\mathbf{{X}})^{-1}\mathbf{{X}}'\mathbf{{y}}$$

3. Analysis should include:
    - Theoretical frameworks
    - Methods used
    - Empirical evidence
    - Patterns and trends
    - Identified gaps
    - Relationship between all titles and {theme}

4. Output Structure should have:
    - All sections and subsections must be clearly defined in Markdown notation (#, ##, ### - max depth 3)
    - Summary about Literature Review Strategy (single paragraph)
    - Sessions for {theme}:
        - Summary of Literature Review Strategy (itself)
        - Results
        - Discussion
        - Conclusion
        - References: Complete citations (APA with DOI)

QUALITY_PARAMETERS:
1. Analysis Requirements:
   - Full document coverage
   - Evidence-based synthesis
   - Mathematical and academic rigor
   - Methodological assessment

2. Content Integration:
   - Inter-study relationships
   - Theme alignment
   - Gap identification
   - Future directions

3. Quality Control:
   - Source validation
   - Mathematical accuracy
   - Logical coherence
   - Unbiased analysis
"""

    def _get_models_list(self) -> List[str]:
        """
        Retorna a lista de modelos a serem tentados, priorizando o modelo escolhido pelo usuário.
        
        Returns:
            List[str]: Lista ordenada de modelos
        """
        if self.model:
            return [self.model] + [m for m in self.available_models if m != self.model]
        return self.available_models

    def _call_openrouter(self, prompt: str, system_prompt: str) -> str:
        """
        Realiza chamada à API do OpenRouter.
        
        Args:
            prompt: Prompt para o modelo
            system_prompt: Prompt do sistema
            
        Returns:
            str: Resposta do modelo
            
        Raises:
            Exception: Se houver erro na chamada à API
        """
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "http://localhost:8080",
            "Content-Type": "application/json"
        }
        
        # Tenta cada modelo em ordem até um funcionar
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
                        "temperature": 0.0
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
        """
        Extrai metadados do texto usando o agente extrator.
        
        Args:
            text: Texto para extração
            
        Returns:
            Dict: Metadados extraídos
        """
        if self.debug:
            print("    [DEBUG] Texto enviado para extração (primeiros 200 caracteres):")
            print(f"    {text[:200]}...\n")
            
        try:
            response = self._call_openrouter(text, self.SYSTEM_PROMPT_EXTRACTOR)
            if self.debug:
                print("    [DEBUG] Resposta bruta da API:")
                print(f"    {response}\n")
                
            # Remove delimitadores markdown se presentes
            if response.startswith("```"):
                lines = response.splitlines()
                # Remove a linha inicial se ela contém os delimitadores e a indicação de linguagem (ex: ```json)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove a última linha se for um fechamento de bloco
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
        """
        Gera a revisão de literatura usando o agente revisor.
        
        Args:
            texts: Lista de dicionários com metadados extraídos
            
        Returns:
            str: Texto da revisão de literatura
        """
        # Formata os textos para o prompt
        formatted_texts = "\n\n".join([
            f"Title: {t['title']}\nAuthor: {t['author']}\nDate: {t['date']}\nAbstract: {t['abstract']}\nLevel: {t['level']}\n"
            for t in texts
        ])
        
        try:
            return self._call_openrouter(formatted_texts, self.SYSTEM_PROMPT_REVIEWER)
        except Exception as e:
            raise Exception(f"Erro ao gerar revisão: {e}")

    def run(self) -> str:
        """
        Executa o processo completo de revisão sistemática.
        
        Returns:
            str: Caminho do arquivo markdown com a revisão
            
        Raises:
            Exception: Se houver erro em qualquer etapa do processo
        """
        try:
            # 0. Configuração do diretório de saída:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                if self.debug:
                    print(f"    [DEBUG] Diretório '{self.output_dir}' criado.")
            else:
                # Remove todos os arquivos e subdiretórios do diretório de saída
                for filename in os.listdir(self.output_dir):
                    file_path = os.path.join(self.output_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                            if self.debug:
                                print(f"    [DEBUG] Arquivo removido: {file_path}")
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            if self.debug:
                                print(f"    [DEBUG] Diretório removido: {file_path}")
                    except Exception as e:
                        print(f"    [DEBUG] Falha ao remover {file_path}. Motivo: {e}")
            
            # 1. Executa o BDTDAgent
            agent = BDTDAgent(
                subject=self.theme,
                max_pages_limit=self.max_pages,
                download_pdf=self.download_pdfs
            )
            agent.scrape_text = self.scrape_text
            agent.run()
            
            # 2. Lê o CSV com os textos extraídos
            print("\n==> Iniciando extração de metadados dos textos...")
            results_file = os.path.join(self.output_dir, "results_page.csv")
            texts = []
            with open(results_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, 1):
                    # Pula linhas em que a coluna "results" está vazia
                    if not row['results'].strip():
                        print(f"    Linha {i} ignorada: coluna 'results' vazia.")
                        continue
                    if len(texts) >= self.max_title_review:
                        break
                    if self.debug:
                        # Mostra os primeiros 200 caracteres do conteúdo lido do CSV
                        print(f"    [DEBUG] Conteúdo da linha {i} do CSV (primeiros 200 caracteres):")
                        print(f"    {row['results'][:200]}...\n")
                    print(f"    Processando texto {i}...")
                    metadata = self._extract_metadata(row['results'])
                    texts.append(metadata)
                    print(f"    ✓ Metadados extraídos: {metadata['title'][:50]}...\n")
            
            # 3. Gera a revisão de literatura
            print("\n==> Iniciando geração da revisão de literatura...")
            print(f"    Usando modelo: {self.model or 'padrão'}")
            print(f"    Idioma: {self.output_lang}")
            print(f"    Total de textos: {len(texts)}")
            review_text = self._generate_review(texts)
            print("    ✓ Revisão de literatura gerada com sucesso!")
            
            # 4. Salva o resultado
            print("\n==> Salvando resultado...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(
                self.output_dir,
                f"literature_review_{timestamp}.md"
            )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(review_text)
            
            return output_file
            
        except Exception as e:
            raise Exception(f"Erro no processo de revisão: {e}")

    # def run(self) -> str:
    #     """
    #     Executa o processo completo de revisão sistemática.
        
    #     Returns:
    #         str: Caminho do arquivo markdown com a revisão
            
    #     Raises:
    #         Exception: Se houver erro em qualquer etapa do processo
    #     """
    #     try:
    #         # 1. Executa o BDTDAgent
    #         agent = BDTDAgent(
    #             subject=self.theme,
    #             max_pages_limit=self.max_pages,
    #             download_pdf=self.download_pdfs
    #         )
    #         agent.scrape_text = self.scrape_text
    #         agent.run()
            
    #         # 2. Lê o CSV com os textos extraídos
    #         print("\n==> Iniciando extração de metadados dos textos...")
    #         results_file = os.path.join(self.output_dir, "results_page.csv")
    #         texts = []
    #         with open(results_file, 'r', encoding='utf-8') as f:
    #             reader = csv.DictReader(f)
    #             for i, row in enumerate(reader, 1):
    #                 # Pula linhas em que a coluna "results" está vazia
    #                 if not row['results'].strip():
    #                     print(f"    Linha {i} ignorada: coluna 'results' vazia.")
    #                     continue
    #                 if len(texts) >= self.max_title_review:
    #                     break
    #                 if self.debug:
    #                     # Mostra os primeiros 200 caracteres do conteúdo lido do CSV
    #                     print(f"    [DEBUG] Conteúdo da linha {i} do CSV (primeiros 200 caracteres):")
    #                     print(f"    {row['results'][:200]}...\n")
    #                 print(f"    Processando texto {i}...")
    #                 metadata = self._extract_metadata(row['results'])
    #                 texts.append(metadata)
    #                 print(f"    ✓ Metadados extraídos: {metadata['title'][:50]}...\n")
            
    #         # 3. Gera a revisão de literatura
    #         print("\n==> Iniciando geração da revisão de literatura...")
    #         print(f"    Usando modelo: {self.model or 'padrão'}")
    #         print(f"    Idioma: {self.output_lang}")
    #         print(f"    Total de textos: {len(texts)}")
    #         review_text = self._generate_review(texts)
    #         print("    ✓ Revisão de literatura gerada com sucesso!")
            
    #         # 4. Salva o resultado
    #         print("\n==> Salvando resultado...")
    #         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    #         output_file = os.path.join(
    #             self.output_dir,
    #             f"literature_review_{timestamp}.md"
    #         )
            
    #         with open(output_file, 'w', encoding='utf-8') as f:
    #             f.write(review_text)
            
    #         return output_file
            
    #     except Exception as e:
    #         raise Exception(f"Erro no processo de revisão: {e}")

def parse_args():
    """
    Processa argumentos da linha de comando.
    
    Returns:
        argparse.Namespace: Argumentos processados
    """
    parser = argparse.ArgumentParser(
        description="Gerador de revisões sistemáticas da BDTD"
    )
    parser.add_argument(
        "theme",
        type=str,
        help="Tema da revisão sistemática"
    )
    parser.add_argument(
        "--output-lang",
        type=str,
        default="pt-BR",
        help="Língua de retorno da revisão (default: pt-BR)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Número máximo de páginas para busca (default: 50)"
    )
    parser.add_argument(
        "--max-title-review",
        type=int,
        default=5,
        help="Número máximo de títulos para revisão (default: 5)"
    )
    parser.add_argument(
        "--download-pdfs",
        action="store_true",
        help="Realizar download dos PDFs encontrados"
    )
    parser.add_argument(
        "--scrape-text",
        action="store_true",
        help="Extrair texto das páginas"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Diretório para saída (default: output)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativar modo debug"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="google/gemini-2.0-pro-exp-02-05:free",
        help="Modelo específico do OpenRouter a ser usado (opcional)"
    )
    
    return parser.parse_args()

def main():
    """
    Função principal para execução via linha de comando.
    """
    args = parse_args()
    
    try:
        reviewer = BDTDReviewer(
            theme=args.theme,
            output_lang=args.output_lang,
            max_pages=args.max_pages,
            max_title_review=args.max_title_review,
            download_pdfs=args.download_pdfs,
            scrape_text=args.scrape_text,
            output_dir=args.output_dir,
            debug=args.debug,
            model=args.model
        )
        
        output_file = reviewer.run()
        print(f"\nRevisão de literatura salva em: {output_file}")
        
    except Exception as e:
        print(f"\nErro: {e}")
        if args.debug:
            raise

if __name__ == "__main__":
    main()
