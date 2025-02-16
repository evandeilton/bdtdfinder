import requests
import pandas as pd
from typing import List, Dict, Optional
import urllib.parse
import json
from datetime import datetime

class BDTDCrawler:
    """
    Classe para realizar buscas na Base Digital de Teses e Dissertações (BDTD)
    e processar os resultados em formato CSV, incluindo todos os campos do JSON.
    API Link Swagger: https://bdtd.ibict.br/vufind/swagger-ui/
    API De fato: https://bdtd.ibict.br/vufind/api/v1/search
    """
    
    def __init__(self):
        """
        Inicializa o crawler com a URL base da API da BDTD.
        """
        self.base_url = "https://bdtd.ibict.br/vufind/api/v1/search"
        
    def create_query_url(
        self,
        keywords: str,
        search_type: str = "AllFields",
        sort: str = "relevance",
        page: int = 1,
        limit: int = 20,
        language: str = "pt-br"
    ) -> str:
        """
        Cria a URL de consulta com os parâmetros fornecidos.
        
        Args:
            keywords (str): Termos de busca
            search_type (str): Tipo de busca (AllFields, Title, Author, etc)
            sort (str): Método de ordenação
            page (int): Número da página
            limit (int): Limite de registros por página
            language (str): Idioma das strings traduzidas
            
        Returns:
            str: URL formatada para a consulta
        """
        params = {
            'lookfor': keywords,
            'type': search_type,
            'sort': sort,
            'page': page,
            'limit': limit,
            'prettyPrint': 'false',
            'lng': language
        }
        
        return f"{self.base_url}?{urllib.parse.urlencode(params)}"
    
    def fetch_results(self, url: str) -> Dict:
        """
        Realiza a requisição HTTP e retorna os resultados.
        
        Args:
            url (str): URL de consulta
            
        Returns:
            Dict: Resposta JSON da API
            
        Raises:
            requests.exceptions.RequestException: Se houver erro na requisição
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {e}")
            raise

    def process_authors(self, authors: Dict) -> Dict:
        """
        Processa a estrutura de autores do registro.
        
        Args:
            authors (Dict): Dicionário contendo autores primários, secundários e corporativos
            
        Returns:
            Dict: Dicionário com autores processados
        """
        result = {
            'primary_authors': [],
            'primary_authors_profiles': [],
            'secondary_authors': [],
            'corporate_authors': []
        }
        
        # Processa autores primários e seus perfis
        for author, details in authors.get('primary', {}).items():
            result['primary_authors'].append(author)
            if isinstance(details, dict) and 'profile' in details:
                result['primary_authors_profiles'].extend(details['profile'])
        
        # Processa autores secundários
        result['secondary_authors'].extend(authors.get('secondary', []))
        
        # Processa autores corporativos
        result['corporate_authors'].extend(authors.get('corporate', []))
        
        return result

    def process_record(self, record: Dict) -> Dict:
        """
        Processa um registro individual extraindo todos os campos.
        
        Args:
            record (Dict): Registro individual do resultado
            
        Returns:
            Dict: Registro processado com todos os campos normalizados
        """
        # Processa autores
        authors_info = self.process_authors(record.get('authors', {}))
        
        # Processa URLs
        urls = record.get('urls', [])
        urls_list = [url.get('url', '') for url in urls]
        urls_desc = [url.get('desc', '') for url in urls]
        
        # Processa subjects (mantendo a estrutura hierárquica)
        subjects = record.get('subjects', [])
        subjects_flat = [item for sublist in subjects for item in sublist]
        
        # Cria o dicionário com todos os campos
        processed = {
            'id': record.get('id', ''),
            'title': record.get('title', ''),
            
            # Campos de autores
            'primary_authors': '; '.join(authors_info['primary_authors']),
            'primary_authors_profiles': '; '.join(authors_info['primary_authors_profiles']),
            'secondary_authors': '; '.join(authors_info['secondary_authors']),
            'corporate_authors': '; '.join(authors_info['corporate_authors']),
            
            # Campos de formato e idioma
            'formats': '; '.join(record.get('formats', [])),
            'languages': '; '.join(record.get('languages', [])),
            
            # Campos de séries
            'series': '; '.join(record.get('series', [])),
            
            # Campos de assunto
            'subjects': '; '.join(subjects_flat),
            
            # Campos de URL
            'urls': '; '.join(urls_list),
            'urls_descriptions': '; '.join(urls_desc)
        }
        
        return processed
    
    def save_to_csv(self, records: List[Dict], filename: Optional[str] = None) -> str:
        """
        Salva os registros processados em um arquivo CSV.
        
        Args:
            records (List[Dict]): Lista de registros processados
            filename (Optional[str]): Nome do arquivo de saída
            
        Returns:
            str: Nome do arquivo CSV gerado
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'bdtd_results_{timestamp}.csv'
        
        # Cria DataFrame e salva com encoding UTF-8 e separador ponto e vírgula
        df = pd.DataFrame(records)

        df['urls'] = df['urls'].astype(str).str.replace(';', '|')

        df.to_csv(filename, index=False, encoding='utf-8', sep=';')
        return filename
    
    def search_and_save(
        self,
        keywords: str,
        filename: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Realiza uma busca completa e salva os resultados em CSV.
        
        Args:
            keywords (str): Termos de busca
            filename (Optional[str]): Nome do arquivo de saída
            **kwargs: Parâmetros adicionais para a busca
            
        Returns:
            str: Nome do arquivo CSV gerado
        """
        url = self.create_query_url(keywords, **kwargs)
        results = self.fetch_results(url)
        
        processed_records = []
        for record in results.get('records', []):
            processed_record = self.process_record(record)
            processed_records.append(processed_record)
            
        filename = self.save_to_csv(processed_records, filename)
        
        # Adiciona informações sobre a busca
        print(f"Total de registros encontrados: {results.get('resultCount', 0)}")
        print(f"Registros processados: {len(processed_records)}")
        print(f"Status da busca: {results.get('status', 'N/A')}")
        
        return filename

# Exemplo de uso
if __name__ == "__main__":
    crawler = BDTDCrawler()
    
    try:
        output_file = crawler.search_and_save(
            keywords=["regressão beta"],
            search_type="AllFields",
            limit=50
        )
        print(f"Resultados salvos em: {output_file}")
    except Exception as e:
        print(f"Erro durante a execução: {e}")
