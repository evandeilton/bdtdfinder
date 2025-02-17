import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time
import re

class PDFDownloader:
    """
    Classe para localizar e baixar PDFs de páginas web, com suporte a redirecionamentos e timeout.
    """
    
    def __init__(self, output_dir="downloads", timeout=60):
        """
        Inicializa o downloader.
        
        Args:
            output_dir (str): Diretório onde os PDFs serão salvos.
            timeout (int): Tempo máximo (em segundos) para aguardar uma resposta do servidor.
        """
        self.output_dir = output_dir
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Cria o diretório de saída se não existir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def follow_redirects(self, url: str) -> str:
        """
        Segue todos os redirecionamentos e retorna a URL final.
        
        Args:
            url (str): URL inicial
            
        Returns:
            str: URL final após todos os redirecionamentos
        """
        try:
            response = self.session.get(url, allow_redirects=True, stream=True, timeout=self.timeout)
            response.close()
            return response.url
        except requests.exceptions.Timeout:
            print(f"Tempo excedido ao acessar (redirect) {url}. Pulando...")
            return url
        except requests.exceptions.RequestException as e:
            print(f"Erro ao seguir redirecionamento: {e}")
            return url
    
    def get_page_content(self, url: str) -> tuple:
        """
        Obtém o conteúdo HTML da página e retorna um objeto BeautifulSoup e a URL final.
        
        Args:
            url (str): URL da página
            
        Returns:
            tuple: (BeautifulSoup ou None, URL final)
        """
        try:
            final_url = self.follow_redirects(url)
            # Agora obtém o conteúdo da página final
            response = self.session.get(final_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Se a resposta for um PDF, retorna None e a URL
            if 'application/pdf' in response.headers.get('Content-Type', '').lower():
                return None, final_url
                
            return BeautifulSoup(response.text, 'html.parser'), final_url
            
        except requests.exceptions.Timeout:
            print(f"Tempo excedido ao acessar {url}. Pulando página...")
            return None, url
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar a página: {e}")
            return None, url
    
    def is_pdf_url(self, url: str) -> bool:
        """
        Verifica se uma URL provavelmente leva a um PDF.
        
        Args:
            url (str): URL para verificar
            
        Returns:
            bool: True se a URL parecer ser de um PDF
        """
        # Verifica extensão .pdf
        if url.lower().endswith('.pdf'):
            return True
            
        # Verifica padrões comuns de URLs de PDF
        pdf_patterns = [
            r'/pdf/',
            r'download',
            r'arquivo',
            r'document',
            r'bitstream',
            r'view'
        ]
        
        return any(re.search(pattern, url.lower()) for pattern in pdf_patterns)
    
    def find_pdf_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """
        Localiza links para PDFs na página.
        
        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup com o conteúdo da página
            base_url (str): URL base para resolver links relativos
            
        Returns:
            list: Lista de URLs de PDFs encontrados
        """
        pdf_links = set()  # Usando set para evitar duplicatas
        
        if soup is None:
            return list(pdf_links)
        
        # Procura por todos os links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Verifica se é um PDF pelos diferentes critérios
            if self.is_pdf_url(full_url):
                pdf_links.add(full_url)
            
            # Verifica o texto do link
            link_text = link.get_text().lower()
            if any(keyword in link_text for keyword in ['pdf', 'download', 'baixar', 'texto completo', 'full text']):
                pdf_links.add(full_url)
        
        # Procura também por iframes que possam conter PDFs
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            full_url = urljoin(base_url, src)
            if self.is_pdf_url(full_url):
                pdf_links.add(full_url)
        
        return list(pdf_links)
    
    def download_pdf(self, url: str, filename: str = None) -> str:
        """
        Baixa um arquivo PDF (ou supostamente PDF), respeitando timeout.
        
        Args:
            url (str): URL do arquivo
            filename (str, optional): Nome do arquivo para salvar. Se None, tenta extrair do 'Content-Disposition' ou URL.
            
        Returns:
            str: Caminho do arquivo baixado
        """
        try:
            # Segue redirecionamentos para obter a URL final
            final_url = self.follow_redirects(url)
            
            response = self.session.get(final_url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            # Tenta obter o nome do arquivo
            if not filename:
                content_disposition = response.headers.get('content-disposition')
                if content_disposition and 'filename=' in content_disposition:
                    filename_match = re.findall(r'filename=(.+)', content_disposition)
                    if filename_match:
                        filename = filename_match[0].strip('"\'')
                if not filename:
                    # Tenta extrair do path
                    filename = os.path.basename(urlparse(final_url).path).split('?')[0]
                if not filename or not filename.strip():
                    filename = 'document.pdf'
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Baixa o arquivo em chunks
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return filepath
            
        except requests.exceptions.Timeout:
            print(f"Tempo excedido para download de {url}. Pulando este arquivo...")
            return ""  # Retorna vazio indicando falha
        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar o PDF: {e}")
            return ""
    
    def process_page(self, url: str) -> list:
        """
        Processa uma página web para encontrar e baixar PDFs.
        
        Args:
            url (str): URL da página
            
        Returns:
            list: Lista de caminhos dos arquivos baixados
        """
        print(f"Processando página: {url}")
        
        # Obtém o conteúdo da página e a URL final após redirecionamentos
        soup, final_url = self.get_page_content(url)
        
        downloaded_files = []
        
        # Se a URL final já é um PDF, baixa diretamente
        if soup is None and self.is_pdf_url(final_url):
            pdf_path = self.download_pdf(final_url)
            if pdf_path:
                downloaded_files.append(pdf_path)
            return downloaded_files
        
        # Encontra links para PDFs
        pdf_links = self.find_pdf_links(soup, final_url)
        
        if not pdf_links:
            print("Nenhum PDF encontrado na página.")
            return downloaded_files
        
        # Baixa cada PDF encontrado
        for pdf_url in pdf_links:
            print(f"Tentando baixar PDF: {pdf_url}")
            pdf_path = self.download_pdf(pdf_url)
            if pdf_path:
                downloaded_files.append(pdf_path)
            # Pausa leve para evitar bombardeio de requests
            time.sleep(0.5)
        
        return downloaded_files


# import requests
# from bs4 import BeautifulSoup
# import os
# from urllib.parse import urljoin, urlparse
# import time
# import re

# class PDFDownloader:
#     """
#     Classe para localizar e baixar PDFs de páginas web, com suporte a redirecionamentos e timeout.
#     """
    
#     def __init__(self, download_folder="downloads", timeout=60):
#         """
#         Inicializa o downloader.
        
#         Args:
#             download_folder (str): Pasta onde os PDFs serão salvos.
#             timeout (int): Tempo máximo (em segundos) para aguardar uma resposta do servidor.
#         """
#         self.download_folder = download_folder
#         self.timeout = timeout
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         })
        
#         # Cria a pasta de downloads se não existir
#         if not os.path.exists(download_folder):
#             os.makedirs(download_folder)
    
#     def follow_redirects(self, url: str) -> str:
#         """
#         Segue todos os redirecionamentos e retorna a URL final.
        
#         Args:
#             url (str): URL inicial
            
#         Returns:
#             str: URL final após todos os redirecionamentos
#         """
#         try:
#             response = self.session.get(url, allow_redirects=True, stream=True, timeout=self.timeout)
#             response.close()
#             return response.url
#         except requests.exceptions.Timeout:
#             print(f"Tempo excedido ao acessar (redirect) {url}. Pulando...")
#             return url
#         except requests.exceptions.RequestException as e:
#             print(f"Erro ao seguir redirecionamento: {e}")
#             return url
    
#     def get_page_content(self, url: str) -> tuple:
#         """
#         Obtém o conteúdo HTML da página e retorna um objeto BeautifulSoup e a URL final.
        
#         Args:
#             url (str): URL da página
            
#         Returns:
#             tuple: (BeautifulSoup ou None, URL final)
#         """
#         try:
#             final_url = self.follow_redirects(url)
#             # Agora obtém o conteúdo da página final
#             response = self.session.get(final_url, timeout=self.timeout)
#             response.raise_for_status()
            
#             # Se a resposta for um PDF, retorna None e a URL
#             if 'application/pdf' in response.headers.get('Content-Type', '').lower():
#                 return None, final_url
                
#             return BeautifulSoup(response.text, 'html.parser'), final_url
            
#         except requests.exceptions.Timeout:
#             print(f"Tempo excedido ao acessar {url}. Pulando página...")
#             return None, url
#         except requests.exceptions.RequestException as e:
#             print(f"Erro ao acessar a página: {e}")
#             return None, url
    
#     def is_pdf_url(self, url: str) -> bool:
#         """
#         Verifica se uma URL provavelmente leva a um PDF.
        
#         Args:
#             url (str): URL para verificar
            
#         Returns:
#             bool: True se a URL parecer ser de um PDF
#         """
#         # Verifica extensão .pdf
#         if url.lower().endswith('.pdf'):
#             return True
            
#         # Verifica padrões comuns de URLs de PDF
#         pdf_patterns = [
#             r'/pdf/',
#             r'download',
#             r'arquivo',
#             r'document',
#             r'bitstream',
#             r'view'
#         ]
        
#         return any(re.search(pattern, url.lower()) for pattern in pdf_patterns)
    
#     def find_pdf_links(self, soup: BeautifulSoup, base_url: str) -> list:
#         """
#         Localiza links para PDFs na página.
        
#         Args:
#             soup (BeautifulSoup): Objeto BeautifulSoup com o conteúdo da página
#             base_url (str): URL base para resolver links relativos
            
#         Returns:
#             list: Lista de URLs de PDFs encontrados
#         """
#         pdf_links = set()  # Usando set para evitar duplicatas
        
#         if soup is None:
#             return list(pdf_links)
        
#         # Procura por todos os links
#         for link in soup.find_all('a', href=True):
#             href = link['href']
#             full_url = urljoin(base_url, href)
            
#             # Verifica se é um PDF pelos diferentes critérios
#             if self.is_pdf_url(full_url):
#                 pdf_links.add(full_url)
            
#             # Verifica o texto do link
#             link_text = link.get_text().lower()
#             if any(keyword in link_text for keyword in ['pdf', 'download', 'baixar', 'texto completo', 'full text']):
#                 pdf_links.add(full_url)
        
#         # Procura também por iframes que possam conter PDFs
#         for iframe in soup.find_all('iframe', src=True):
#             src = iframe['src']
#             full_url = urljoin(base_url, src)
#             if self.is_pdf_url(full_url):
#                 pdf_links.add(full_url)
        
#         return list(pdf_links)
    
#     def download_pdf(self, url: str, filename: str = None) -> str:
#         """
#         Baixa um arquivo PDF (ou supostamente PDF), respeitando timeout.
        
#         Args:
#             url (str): URL do arquivo
#             filename (str, optional): Nome do arquivo para salvar. Se None, tenta extrair do 'Content-Disposition' ou URL.
            
#         Returns:
#             str: Caminho do arquivo baixado
#         """
#         try:
#             # Segue redirecionamentos para obter a URL final
#             final_url = self.follow_redirects(url)
            
#             response = self.session.get(final_url, stream=True, timeout=self.timeout)
#             response.raise_for_status()
            
#             # Tenta obter o nome do arquivo
#             if not filename:
#                 content_disposition = response.headers.get('content-disposition')
#                 if content_disposition and 'filename=' in content_disposition:
#                     filename_match = re.findall(r'filename=(.+)', content_disposition)
#                     if filename_match:
#                         filename = filename_match[0].strip('"\'')
#                 if not filename:
#                     # Tenta extrair do path
#                     filename = os.path.basename(urlparse(final_url).path).split('?')[0]
#                 if not filename or not filename.strip():
#                     filename = 'document.pdf'
            
#             filepath = os.path.join(self.download_folder, filename)
            
#             # Baixa o arquivo em chunks
#             with open(filepath, 'wb') as f:
#                 for chunk in response.iter_content(chunk_size=8192):
#                     if chunk:
#                         f.write(chunk)
            
#             return filepath
            
#         except requests.exceptions.Timeout:
#             print(f"Tempo excedido para download de {url}. Pulando este arquivo...")
#             return ""  # Retorna vazio indicando falha
#         except requests.exceptions.RequestException as e:
#             print(f"Erro ao baixar o PDF: {e}")
#             return ""
    
#     def process_page(self, url: str) -> list:
#         """
#         Processa uma página web para encontrar e baixar PDFs.
        
#         Args:
#             url (str): URL da página
            
#         Returns:
#             list: Lista de caminhos dos arquivos baixados
#         """
#         print(f"Processando página: {url}")
        
#         # Obtém o conteúdo da página e a URL final após redirecionamentos
#         soup, final_url = self.get_page_content(url)
        
#         downloaded_files = []
        
#         # Se a URL final já é um PDF, baixa diretamente
#         if soup is None and self.is_pdf_url(final_url):
#             pdf_path = self.download_pdf(final_url)
#             if pdf_path:
#                 downloaded_files.append(pdf_path)
#             return downloaded_files
        
#         # Encontra links para PDFs
#         pdf_links = self.find_pdf_links(soup, final_url)
        
#         if not pdf_links:
#             print("Nenhum PDF encontrado na página.")
#             return downloaded_files
        
#         # Baixa cada PDF encontrado
#         for pdf_url in pdf_links:
#             print(f"Tentando baixar PDF: {pdf_url}")
#             pdf_path = self.download_pdf(pdf_url)
#             if pdf_path:
#                 downloaded_files.append(pdf_path)
#             # Pausa leve para evitar bombardeio de requests
#             time.sleep(0.5)
        
#         return downloaded_files
