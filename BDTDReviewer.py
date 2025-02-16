import os
import logging
import argparse
import json
from typing import Optional, List, Dict
from dataclasses import dataclass
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob

# Constantes dos prompts de sistema
SYSTEM_PROMPT_REVIEWER = """
<role>
    You are a researcher specialized in systematic literature reviews about {theme}. 
    Your task is to analyze all articles provided by the user, extracting and synthesizing 
    relevant information for the theme "{theme}".
</role>

<important>
    - Use ALL content from the provided articles. Do not ignore any relevant information.
    - Read and process all provided articles carefully and extract relevant information.
    - Identify connections with the theme "{theme}".
    - Extract relevant evidence, methods, and results.
    - Synthesize findings while maintaining focus on the theme.
    - Write a comprehensive literature review with near 4000 words about the theme "{theme}".
</important>

<guidelines>
    "Analysis": [
        Theoretical frameworks,
        Methods used,
        Empirical evidence,
        Patterns and trends,
        Identified gaps,
        Relationship between papers and theme
    ]
    
    "Structure": [
        Summary,
        Methodology,
        Results,
        Discussion,
        Conclusion
    ]
</guidelines>

<output>
    - Literature Review
    - Methodology
    - Results
    - References
</output>
"""

SYSTEM_PROMPT_EXTRACTOR = """You are tasked with extracting metadata from academic thesis/dissertation repository text and structuring it into a standardized JSON format. The input will be a long string containing webpage content from academic repositories.

Expected JSON structure:
{
  "title": <string>,
  "abstract": <string>,
  "author": <string>,
  "date": <string>
}

Look for these common identifiers in the text:
- Title: "Título", "Title"
- Date/Year: "Data de defesa", "Date", "Ano"
- Author: "Autor", "Author", "Nome completo"
- Abstract: "Resumo", "Abstract"

When information is not found, use "Not informed" as default value.
Maintain the original language for abstract and other text."""

# Imports dos módulos existentes
from bdtdfinder import BDTDCrawler
from bdtddownloader import PDFDownloader
from BDTDResearchAgent import BDTDAgent

# Download recursos NLTK necessários
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
except Exception as e:
    print(f"Erro ao baixar recursos NLTK: {e}")

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("bdtd_reviewer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ReviewMetrics:
    """Classe para armazenar métricas da revisão sistemática."""
    total_documents: int
    temporal_range: Dict[str, str]
    quality_score: float
    sentiment_score: float
    top_keywords: List[str]
    cluster_info: Dict[str, List[str]]

class EnhancedBDTDReviewer:
    """
    Versão aprimorada do BDTDReviewer que integra análise avançada e visualização.
    
    Funcionalidades:
    1. Integração com BDTDAgent para busca e download
    2. Análise estatística avançada
    3. Processamento de linguagem natural
    4. Visualizações interativas
    5. Métricas de qualidade
    """
    
    def __init__(
        self,
        theme: str,
        api_provider,
        max_pages: int = 50,
        download_pdfs: bool = False,
        output_dir: str = "output"
    ):
        """
        Inicializa o revisor aprimorado.
        
        Args:
            theme (str): Tema da revisão
            api_provider: Provedor de API para geração de conteúdo
            max_pages (int): Limite de páginas para busca
            download_pdfs (bool): Se deve baixar PDFs
            output_dir (str): Diretório de saída
        """
        self.theme = theme
        self.api_provider = api_provider
        self.max_pages = max_pages
        self.download_pdfs = download_pdfs
        self.output_dir = output_dir
        
        # Inicializa componentes de análise
        try:
            self.vectorizer = TfidfVectorizer(
                stop_words='portuguese',
                max_features=1000,  # Limit features to prevent memory issues
                min_df=2  # Minimum document frequency
            )
        except Exception as e:
            logger.error(f"Error initializing TfidfVectorizer: {e}")
            raise
            
        self.metrics = None
        
        # Create output directory with parents if needed
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Initialized reviewer for theme: {theme}")
        logger.debug(f"Configuration: max_pages={max_pages}, download_pdfs={download_pdfs}")
    
    def search_and_download(self) -> bool:
        """
        Executa busca e download usando BDTDAgent.
        """
        try:
            # Create output directory first
            os.makedirs(self.output_dir, exist_ok=True)
            
            agent = BDTDAgent(
                subject=self.theme,
                max_pages_limit=self.max_pages,
                download_pdf=self.download_pdfs
            )
            
            # Set output directory for the agent
            agent.output_dir = self.output_dir
            
            # Set scrape_text attribute
            agent.scrape_text = True
            
            logger.info(f"Starting agent with theme: {self.theme}")
            agent.run()
            
            # Verify if results files were created
            expected_files = [
                os.path.join(self.output_dir, "results.csv"),
                os.path.join(self.output_dir, "results_filtered.csv"),
                os.path.join(self.output_dir, "results_page.csv")
            ]
            
            for file_path in expected_files:
                if not os.path.exists(file_path):
                    logger.error(f"Expected file not found: {file_path}")
                    return False
            
            logger.info("All expected files were created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during search and download: {e}", exc_info=True)
            return False
    
    def extract_keywords(self, text: str, n: int = 10) -> List[str]:
        """
        Extrai palavras-chave do texto usando TF-IDF.
        
        Args:
            text (str): Texto para análise
            n (int): Número de palavras-chave
            
        Returns:
            List[str]: Lista de palavras-chave
        """
        try:
            # Tokenização e remoção de stopwords
            tokens = word_tokenize(text.lower())
            stop_words = set(stopwords.words('portuguese'))
            tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
            
            # Contagem de frequência
            freq = Counter(tokens)
            return [word for word, _ in freq.most_common(n)]
        except Exception as e:
            logger.error(f"Erro na extração de palavras-chave: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analisa o sentimento do texto.
        
        Args:
            text (str): Texto para análise
            
        Returns:
            float: Score de sentimento (-1 a 1)
        """
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            return 0.0
    
    def cluster_documents(self, texts: List[str], n_clusters: int = 5) -> Dict:
        """
        Agrupa documentos em clusters temáticos.
        
        Args:
            texts (List[str]): Lista de textos
            n_clusters (int): Número de clusters
            
        Returns:
            Dict: Informações dos clusters
        """
        try:
            # Vetorização TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(tfidf_matrix)
            
            # Extrai termos mais relevantes por cluster
            cluster_terms = {}
            feature_names = self.vectorizer.get_feature_names_out()
            
            for i in range(n_clusters):
                cluster_docs = tfidf_matrix[clusters == i]
                if cluster_docs.shape[0] > 0:
                    centroid = cluster_docs.mean(axis=0).A1
                    top_indices = centroid.argsort()[-5:][::-1]
                    cluster_terms[f"cluster_{i}"] = [
                        feature_names[idx] for idx in top_indices
                    ]
            
            return cluster_terms
        except Exception as e:
            logger.error(f"Erro no clustering: {e}")
            return {}
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Helper function to parse dates with multiple formats."""
        if not date_str or date_str == "Not informed":
            return None
            
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def calculate_metrics(self, texts: List[str], dates: List[str]) -> ReviewMetrics:
        """
        Calcula métricas da revisão com melhor tratamento de erros.
        """
        try:
            if not texts:
                logger.error("No texts provided for analysis")
                raise ValueError("Empty text list")

            # Parse dates with better error handling
            parsed_dates = []
            for date in dates:
                parsed_date = self.parse_date(date)
                if parsed_date:
                    parsed_dates.append(parsed_date)
            
            temporal_range = {
                "start": min(parsed_dates).strftime("%Y-%m-%d") if parsed_dates else "N/A",
                "end": max(parsed_dates).strftime("%Y-%m-%d") if parsed_dates else "N/A"
            }
            
            # Concatenate texts with length validation
            valid_texts = [text for text in texts if isinstance(text, str) and text.strip()]
            if not valid_texts:
                logger.error("No valid texts found after filtering")
                raise ValueError("No valid texts for analysis")
                
            full_text = " ".join(valid_texts)
            
            # Calculate metrics with proper validation
            metrics = ReviewMetrics(
                total_documents=len(valid_texts),
                temporal_range=temporal_range,
                quality_score=len(valid_texts) / self.max_pages,
                sentiment_score=self.analyze_sentiment(full_text),
                top_keywords=self.extract_keywords(full_text),
                cluster_info=self.cluster_documents(valid_texts, n_clusters=min(5, len(valid_texts)))
            )
            
            logger.info(f"Successfully calculated metrics for {len(valid_texts)} documents")
            logger.debug(f"Metrics: {metrics}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}", exc_info=True)
            # Return default metrics instead of None
            return ReviewMetrics(
                total_documents=0,
                temporal_range={"start": "N/A", "end": "N/A"},
                quality_score=0.0,
                sentiment_score=0.0,
                top_keywords=[],
                cluster_info={}
            )
    
    def generate_visualizations(self):
        """Gera visualizações dos dados analisados."""
        try:
            if not self.metrics:
                return
            
            # Timeline plot
            plt.figure(figsize=(12, 6))
            dates = [
                datetime.strptime(d, "%Y-%m-%d") 
                for d in [self.metrics.temporal_range["start"], self.metrics.temporal_range["end"]]
                if d != "N/A"
            ]
            if dates:
                plt.hist(dates, bins=20)
                plt.title("Distribuição Temporal das Publicações")
                plt.xlabel("Data")
                plt.ylabel("Quantidade")
                plt.savefig(os.path.join(self.output_dir, "temporal_distribution.png"))
            
            # Cluster visualization
            if self.metrics.cluster_info:
                plt.figure(figsize=(10, 10))
                cluster_data = pd.DataFrame.from_dict(
                    self.metrics.cluster_info, 
                    orient='index'
                )
                sns.heatmap(
                    cluster_data.notnull(), 
                    cmap='YlOrRd',
                    cbar_kws={'label': 'Presença de Termos'}
                )
                plt.title("Distribuição de Termos por Cluster")
                plt.savefig(os.path.join(self.output_dir, "cluster_heatmap.png"))
            
        except Exception as e:
            logger.error(f"Erro na geração de visualizações: {e}")
    
    def run(self) -> Optional[str]:
        """
        Executa o processo completo de revisão.
        
        Returns:
            Optional[str]: Texto da revisão gerada ou None em caso de erro
        """
        try:
            logger.info(f"Starting review process for theme: {self.theme}")
            
            # Execute search and download
            if not self.search_and_download():
                logger.error("Failed to search and download content")
                return None
            
            # Read CSV data with validation
            results_page_csv = os.path.join(self.output_dir, "results_page.csv")
            if not os.path.exists(results_page_csv):
                logger.error(f"Results file not found: {results_page_csv}")
                return None
            
            try:
                df = pd.read_csv(results_page_csv)
                logger.info(f"Successfully loaded {len(df)} records from CSV")
            except Exception as e:
                logger.error(f"Error reading CSV file: {e}")
                return None
            
            # Validate DataFrame content
            if df.empty:
                logger.error("Empty DataFrame loaded from CSV")
                return None
            
            if 'results' not in df.columns:
                logger.error("Required 'results' column not found in CSV")
                return None
            
            # Calculate metrics with proper data validation
            self.metrics = self.calculate_metrics(
                texts=df["results"].fillna("").tolist(),
                dates=df.get("date", ["Not informed"] * len(df)).fillna("Not informed").tolist()
            )
            
            if not self.metrics:
                logger.error("Failed to calculate metrics")
                return None
            
            # Generate visualizations with error handling
            try:
                self.generate_visualizations()
            except Exception as e:
                logger.error(f"Error generating visualizations: {e}")
                # Continue execution even if visualizations fail
            
            # Gera revisão usando a API
            system_prompt = SYSTEM_PROMPT_REVIEWER.replace("{theme}", self.theme)
            user_prompt = f"""
            Tema: {self.theme}
            
            Métricas da Revisão:
            - Total de documentos: {self.metrics.total_documents}
            - Período: {self.metrics.temporal_range['start']} a {self.metrics.temporal_range['end']}
            - Score de qualidade: {self.metrics.quality_score:.2f}
            - Sentimento geral: {self.metrics.sentiment_score:.2f}
            
            Palavras-chave principais:
            {', '.join(self.metrics.top_keywords)}
            
            Clusters temáticos:
            {json.dumps(self.metrics.cluster_info, indent=2)}
            
            Documentos analisados:
            {df['results'].str.cat(sep='\n\n')}
            """
            
            literature_review = self.api_provider.generate_content(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0
            )
            
            # Salva revisão
            output_file = os.path.join(self.output_dir, "literature_review.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(literature_review)
            
            logger.info("Review process completed successfully")
            return literature_review
            
        except Exception as e:
            logger.error(f"Error during review process: {e}", exc_info=True)
            return None

def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gerador de revisão sistemática de literatura da BDTD"
    )
    parser.add_argument(
        "theme",
        type=str,
        help="Tema da revisão sistemática"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Número máximo de páginas para busca (default: 50)"
    )
    parser.add_argument(
        "--download-pdfs",
        action="store_true",
        help="Realizar download dos PDFs encontrados"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Diretório para saída dos arquivos (default: output)"
    )
    return parser.parse_args()

# Continuação do arquivo anterior...

def main():
    """
    Função principal do programa.
    
    Fluxo de execução:
    1. Parse dos argumentos da linha de comando
    2. Inicialização do revisor
    3. Execução da revisão
    4. Geração de relatório de resultados
    """
    args = parse_arguments()
    
    # Configuração do logger para o arquivo de execução
    execution_log = os.path.join(args.output_dir, "execution.log")
    file_handler = logging.FileHandler(execution_log)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s'
    ))
    logger.addHandler(file_handler)
    
    logger.info(f"Iniciando revisão sistemática sobre: {args.theme}")
    logger.info(f"Configurações: max_pages={args.max_pages}, download_pdfs={args.download_pdfs}")
    
    # Mock API Provider para exemplo
    class MockAPIProvider:
        def generate_content(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
            """
            Simula a geração de conteúdo para exemplo.
            Na implementação real, este seria substituído pelo provedor real da API.
            
            Args:
                system_prompt (str): Prompt do sistema
                user_prompt (str): Prompt do usuário
                temperature (float): Temperatura para geração
            
            Returns:
                str: Conteúdo gerado
            """
            return f"""
            # Revisão Sistemática: {args.theme}
            
            ## Introdução
            Esta revisão sistemática aborda o tema "{args.theme}" através da análise 
            da literatura disponível na Base Digital de Teses e Dissertações (BDTD).
            
            ## Metodologia
            A busca foi realizada utilizando critérios específicos, incluindo...
            
            ## Resultados
            Os principais achados desta revisão incluem...
            
            ## Conclusão
            Com base na análise realizada, podemos concluir que...
            """
    
    try:
        # Inicializa o revisor com as configurações
        reviewer = EnhancedBDTDReviewer(
            theme=args.theme,
            api_provider=MockAPIProvider(),
            max_pages=args.max_pages,
            download_pdfs=args.download_pdfs,
            output_dir=args.output_dir
        )
        
        # Executa a revisão
        review_text = reviewer.run()
        
        if review_text:
            # Gera relatório de execução
            report_path = os.path.join(args.output_dir, "execution_report.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"""
                Relatório de Execução - Revisão Sistemática
                ==========================================
                
                Tema: {args.theme}
                Data de execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                Configurações
                ------------
                - Máximo de páginas: {args.max_pages}
                - Download de PDFs: {args.download_pdfs}
                - Diretório de saída: {args.output_dir}
                
                Métricas da Revisão
                ------------------
                - Total de documentos: {reviewer.metrics.total_documents}
                - Período: {reviewer.metrics.temporal_range['start']} a {reviewer.metrics.temporal_range['end']}
                - Score de qualidade: {reviewer.metrics.quality_score:.2f}
                - Sentimento geral: {reviewer.metrics.sentiment_score:.2f}
                
                Palavras-chave principais
                -----------------------
                {', '.join(reviewer.metrics.top_keywords)}
                
                Clusters Temáticos
                ----------------
                {json.dumps(reviewer.metrics.cluster_info, indent=2)}
                
                Arquivos Gerados
                --------------
                - Revisão: literature_review.txt
                - Visualizações: temporal_distribution.png, cluster_heatmap.png
                - Logs: execution.log
                """)
            
            logger.info(f"Revisão concluída com sucesso. Relatório salvo em {report_path}")
            print(f"\nRevisão concluída com sucesso!")
            print(f"Arquivos gerados no diretório: {args.output_dir}")
            print(f"Para mais detalhes, consulte o relatório: {report_path}")
            
        else:
            logger.error("Falha na geração da revisão")
            print("\nErro: Falha na geração da revisão. Verifique os logs para mais detalhes.")
            return 1
            
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        print(f"\nErro durante execução: {e}")
        print("Verifique os logs para mais detalhes.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())