import os
import re
import csv
import argparse
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Imports dos módulos fornecidos
from BDTDfinder import BDTDCrawler
from BDTDdownloader import PDFDownloader

class BDTDAgent:
    """
    Classe principal que integra a lógica de pesquisa na BDTD, filtragem de resultados,
    download de arquivos e raspagem de texto plain das páginas acadêmicas, armazenando tudo na pasta 'output'.
    """

    def __init__(self, subject: str, max_pages_limit: int = 50, download_pdf: bool = False):
        """
        Inicializa o agente com as configurações necessárias.
        
        Args:
            subject (str): Assunto/keywords para a busca.
            max_pages_limit (int): Número máximo de páginas para percorrer na busca (default=50).
            download_pdf (bool): Se True, faz o download dos arquivos após filtrar (default=False).
        """
        self.subject = subject
        self.max_pages_limit = max_pages_limit
        self.download_pdf = download_pdf
        self.output_dir = "output"  # Make this configurable
        self.scrape_text = False    # Add scrape_text attribute

        # Caminhos para os CSVs gerados
        self.output_csv = os.path.join(self.output_dir, "results.csv")
        self.filtered_csv = os.path.join(self.output_dir, "results_filtered.csv")
        self.page_details_csv = os.path.join(self.output_dir, "results_page.csv")
        
    def run_crawler(self) -> str:
        """
        Executa o BDTDCrawler em múltiplas páginas até o limite definido e salva o resultado consolidado
        em um arquivo CSV final (self.output_csv).
        
        Returns:
            str: Caminho do arquivo CSV resultante ou None se nenhum registro for encontrado.
        """
        crawler = BDTDCrawler()
        all_records = []
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        page_count = 0
        
        for page in range(1, self.max_pages_limit + 1):
            try:
                url = crawler.create_query_url(
                    keywords=self.subject,
                    search_type="AllFields",
                    sort="relevance",
                    page=page,
                    limit=20,
                    language="pt-br"
                )
                results_json = crawler.fetch_results(url)
                records = results_json.get('records', [])
                if not records:
                    # Se não vier nenhum registro nesta página, encerra a busca
                    break
                
                for record in records:
                    processed = crawler.process_record(record)
                    all_records.append(processed)
                
                page_count += 1
                print(f"Página {page} processada com sucesso ({len(records)} registros).")
                
            except Exception as e:
                print(f"Erro na página {page}: {e}")
                break
        
        if not all_records:
            print(f"\nNenhum registro encontrado para o assunto: '{self.subject}'.")
            return None
        
        # Gera dataframe e salva o CSV
        df = pd.DataFrame(all_records)
        df.to_csv(self.output_csv, index=False, encoding="utf-8", sep=";")
        
        print(f"\nTotal de páginas processadas: {page_count}")
        print(f"Arquivo CSV consolidado salvo em: {self.output_csv}")
        return self.output_csv

    def filter_by_subject(self, csv_path: str) -> str:
        """
        Filtra o CSV, mantendo apenas as linhas cujo 'title' contenha ao menos uma das palavras de self.subject.
        
        Args:
            csv_path (str): Caminho do CSV original.
        
        Returns:
            str: Caminho do CSV filtrado (self.filtered_csv).
        """
        try:
            df = pd.read_csv(csv_path, sep=";")
        except pd.errors.EmptyDataError:
            print("O arquivo CSV de resultados está vazio. Encerrando o processo.")
            return None
        
        subject_terms = self.subject.lower().split()
        
        def match_title(title):
            title_lower = str(title).lower()
            return any(re.search(rf"\b{term}\b", title_lower) for term in subject_terms)
        
        filtered_df = df[df["title"].apply(match_title)]
        filtered_df.to_csv(self.filtered_csv, index=False, encoding="utf-8", sep=";")
        
        print(f"Arquivo CSV filtrado salvo em: {self.filtered_csv}")
        return self.filtered_csv

    @staticmethod
    def sanitize_folder_name(foldername: str) -> str:
        """
        Remove caracteres potencialmente problemáticos em nomes de diretórios.
        
        Args:
            foldername (str): Nome do diretório original.
            
        Returns:
            str: Nome sanitizado.
        """
        foldername = foldername.replace('/', '_').replace('\\', '_').replace(':', '-')
        return foldername
    
    @staticmethod
    def is_valid_pdf(filepath: str) -> bool:
        """
        Verifica se um arquivo começa com os bytes típicos de um PDF ('%PDF').
        
        Args:
            filepath (str): Caminho para o arquivo PDF.
        
        Returns:
            bool: True se for PDF válido, False caso contrário.
        """
        if not os.path.isfile(filepath):
            return False
        try:
            with open(filepath, "rb") as f:
                start = f.read(4)
            return start == b"%PDF"
        except Exception:
            return False

    def download_pdfs(self, csv_path: str):
        """
        Faz o download dos arquivos a partir das URLs no CSV filtrado.
        - Cria para cada registro uma pasta de nome '{id}' dentro de 'output'.
        - Baixa todos os arquivos sem renomear (mantendo o nome original do servidor ou da URL).
        
        Obs.: A checagem final de integridade e tamanho é feita na rotina de sanity check.
        
        Args:
            csv_path (str): Caminho do CSV filtrado.
        """
        df = pd.read_csv(csv_path, sep=";")
        
        for idx, row in df.iterrows():
            rec_id = str(row.get("id", "no_id"))
            folder_name = self.sanitize_folder_name(rec_id)
            pdf_subfolder = os.path.join(self.output_dir, folder_name)

            if not os.path.exists(pdf_subfolder):
                os.makedirs(pdf_subfolder)
            
            downloader = PDFDownloader(download_folder=pdf_subfolder)
            # Assume que as URLs estão separadas por '|'
            url_list = [u.strip() for u in str(row.get("urls", "")).split("|") if u.strip()]
            
            for url in url_list:
                try:
                    downloaded_files = downloader.process_page(url)
                    for dfile in downloaded_files:
                        print(f"Arquivo baixado: {dfile}")
                except Exception as e:
                    print(f"Erro ao baixar de {url}: {e}")
                    continue

    def sanity_check_downloads(self):
        """
        Percorre todas as pastas dentro de 'output' e remove:
          1) Qualquer arquivo que não seja PDF;
          2) Qualquer PDF com menos de 100 KB;
          3) Qualquer PDF corrompido (não inicia com '%PDF');
          4) Caso a pasta fique vazia, remove a pasta também.
        
        Exibe logs sobre as remoções realizadas.
        """
        base_output = self.output_dir
        
        for folder_name in os.listdir(base_output):
            folder_path = os.path.join(base_output, folder_name)
            
            if os.path.isdir(folder_path):
                initial_files = os.listdir(folder_path)
                
                for file_name in initial_files:
                    file_path = os.path.join(folder_path, file_name)
                    
                    if not os.path.isfile(file_path):
                        continue
                    
                    # Remove arquivos que não possuem extensão .pdf
                    if not file_name.lower().endswith(".pdf"):
                        print(f"[Sanity Check] Removendo '{file_path}' (não é PDF).")
                        os.remove(file_path)
                        continue

                    if os.path.getsize(file_path) < 100_000:
                        print(f"[Sanity Check] Removendo '{file_path}' (< 100 KB).")
                        os.remove(file_path)
                        continue
                    
                    if not self.is_valid_pdf(file_path):
                        print(f"[Sanity Check] Removendo '{file_path}' (PDF corrompido).")
                        os.remove(file_path)
                
                if not os.listdir(folder_path):
                    print(f"[Sanity Check] Removendo pasta vazia: '{folder_path}'")
                    os.rmdir(folder_path)

    def scrape_all_pages(self, csv_path: str):
        """
        Para cada registro do CSV filtrado, percorre os links contidos no campo 'urls'
        e extrai o texto plain (sem HTML) de cada página. Os resultados são salvos
        no arquivo results_page.csv com duas colunas: 'id' e 'results', onde 'id' é obtido
        do campo {id} do CSV filtrado e 'results' contém o texto extraído da página.
        
        Args:
            csv_path (str): Caminho do CSV filtrado.
        """
        try:
            df = pd.read_csv(csv_path, sep=";")
        except Exception as e:
            print(f"Erro ao ler o CSV filtrado para raspagem: {e}")
            return

        # Prepara o CSV de saída sobrescrevendo qualquer arquivo existente
        csv_out = self.page_details_csv
        with open(csv_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "results"])
            writer.writeheader()

        for idx, row in df.iterrows():
            record_id = str(row.get("id", "no_id"))
            urls_str = str(row.get("urls", ""))
            url_list = [u.strip() for u in urls_str.split("|") if u.strip()]
            for url in url_list:
                print(f"Raspando texto da página: {url}")
                try:
                    response = requests.get(url, timeout=60)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    plain_text = soup.get_text(separator=" ", strip=True)
                except Exception as e:
                    print(f"Erro ao acessar ou processar {url}: {e}")
                    plain_text = ""
                # Anexa o resultado ao CSV
                with open(csv_out, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["id", "results"])
                    writer.writerow({"id": record_id, "results": plain_text})
        print(f"Transcrições salvas em: {csv_out}")

    def run(self):
        """
        Executa todo o fluxo:
          1) Busca com BDTDCrawler (multi-páginas) e salva em 'output/results.csv'.
          2) Filtra o CSV em 'output/results_filtered.csv' pelas palavras de self.subject.
          3) Raspagem do texto plain de cada link visitado (se o argumento --scrape_text for utilizado).
          4) (Opcional) Faz download dos arquivos em pastas separadas.
          5) (Opcional) Ao final, executa o sanity check para remover PDFs indesejados.
        """
        print(f"==> Iniciando busca para o assunto: '{self.subject}'")
        print(f"==> Número máximo de páginas: {self.max_pages_limit}")
        print(f"==> Download de PDFs ativado? {self.download_pdf}")
        
        csv_path = self.run_crawler()
        if csv_path is None or os.path.getsize(csv_path) == 0:
            print("Nenhum registro foi encontrado na busca. Encerrando o processo.")
            return
        
        filtered_csv = self.filter_by_subject(csv_path)
        if filtered_csv is None or os.path.getsize(filtered_csv) == 0:
            print("Nenhum registro após a filtragem. Encerrando o processo.")
            return
        
        # Se o usuário optar por raspar o texto das páginas, executa scrape_all_pages
        if hasattr(self, 'scrape_text') and self.scrape_text:
            self.scrape_all_pages(filtered_csv)
        
        if self.download_pdf:
            self.download_pdfs(filtered_csv)
            print("==> Download de arquivos concluído.")
            self.sanity_check_downloads()
        
        print("==> Processo finalizado com sucesso!")

def parse_arguments():
    """
    Faz o parsing dos argumentos de linha de comando e retorna-os.
    
    Returns:
        argparse.Namespace: Objeto contendo os argumentos parseados.
    """
    parser = argparse.ArgumentParser(
        description="Agente para busca na BDTD, download de PDFs e raspagem de texto de páginas acadêmicas."
    )
    parser.add_argument(
        "subject",
        type=str,
        help="Assunto de pesquisa (keywords)."
    )
    parser.add_argument(
        "--max_pages_limit",
        type=int,
        default=50,
        help="Número máximo de páginas para percorrer na busca (default=50)."
    )
    parser.add_argument(
        "--download_pdf",
        action="store_true",
        help="Se presente, faz o download dos arquivos encontrados no CSV filtrado."
    )
    parser.add_argument(
        "--scrape_text",
        action="store_true",
        help="Se presente, raspa o texto plain de cada página e salva em results_page.csv."
    )
    
    return parser.parse_args()

def main():
    """
    Ponto de entrada quando executado via linha de comando.
    - Lê os argumentos,
    - Cria a instância de BDTDAgent,
    - Executa o método 'run()'.
    """
    args = parse_arguments()
    agent = BDTDAgent(
        subject=args.subject,
        max_pages_limit=args.max_pages_limit,
        download_pdf=args.download_pdf
    )
    # Define o atributo scrape_text conforme o argumento
    agent.scrape_text = args.scrape_text
    agent.run()

if __name__ == "__main__":
    main()



