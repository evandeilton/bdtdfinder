# BDTD Research Agent & Reviewer

BDTD Research Agent & Reviewer é uma biblioteca Python que automatiza revisões sistemáticas de literatura utilizando a Biblioteca Digital de Teses e Dissertações (BDTD). Ela realiza a busca, filtragem, download e análise de documentos acadêmicos e, através da OpenRouter API com LLMs avançados, gera revisões completas.

---

## Principais Funcionalidades

- **Pesquisa Automatizada:**  
  - Crawling inteligente e multi-página na BDTD.

- **Processamento de Conteúdo:**  
  - Extração de metadados e texto de páginas acadêmicas.  
  - Download e organização de arquivos PDF.

- **Geração de Revisões:**  
  - Criação de revisões detalhadas e baseadas em evidências com o auxílio de LLMs.

- **Configuração Personalizável:**  
  - Definição de diretório de saída e parâmetros de pesquisa.

- **Interface de Usuário:**  
  - UI dedicada (executada via Streamlit) para facilitar o uso.

---

## Instalação e Configuração

**Instalação:**

1. Clone o repositório e instale o pacote:
   ```bash
   git clone https://github.com/evandeilton/bdtdfinder.git
   cd bdtdfinder
   pip install .
   ```
   
**Configuração da OpenRouter API:**

- **Obtenha sua API Key:**  
  Crie uma conta em [OpenRouter](https://openrouter.ai/) e obtenha sua chave.

- **Defina a variável de ambiente:**  
  Adicione em um arquivo `.env` (ou diretamente no ambiente):
  ```
  OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
  ```
  
- **Seleção de Modelo:**  
  O modelo padrão é `google/gemini-2.0-pro-exp-02-05:free`, mas pode ser substituído via argumento `model`.

---

## Exemplo de Uso

Antes de executar, certifique-se de que a variável `OPENROUTER_API_KEY` está definida. Segue um exemplo para realizar uma revisão sistemática:

```python
import os
from bdtdfinder.BDTDReviewer import BDTDReviewer

# Verifica se a chave da API está definida
if not os.environ.get("OPENROUTER_API_KEY"):
    raise EnvironmentError("A variável de ambiente OPENROUTER_API_KEY não está definida.")

# Cria a instância do revisor com os parâmetros desejados
reviewer = BDTDReviewer(
    theme="regressão beta",
    output_lang="pt-BR",
    max_pages=1,              # Máximo de páginas a serem analisadas
    max_title_review=2,       # Máximo de títulos a processar
    download_pdfs=False,      # True para baixar PDFs
    scrape_text=True,         # Habilita a extração de texto das páginas
    output_dir="results",     # Diretório de saída
    debug=True,               # Modo debug para logs detalhados
    model="google/gemini-2.0-pro-exp-02-05:free"
)

# Executa o processo de revisão
output_file = reviewer.run()
print(f"Revisão salva em: {output_file}")
```

**Nota sobre a UI:**  
A interface não funciona em notebooks. Para executá-la, use:
```bash
streamlit run /bdtdfinder/src/bdtdfinder/BDTDUi.py
```

---

## Estrutura de Saída e Componentes Principais

**Saída:**  
Após a execução, o diretório de saída (por exemplo, `results/`) conterá:
- Pastas com PDFs (se o download estiver habilitado)
- Arquivos CSV com os resultados brutos e filtrados
- Arquivo Markdown com a revisão gerada (nomeado com timestamp)

**Componentes Principais:**

- **BDTDReviewer:**  
  Coordena todo o processo, desde a pesquisa na BDTD até a geração final da revisão.

- **BDTDCrawler:**  
  Responsável pela busca de teses e dissertações na BDTD.

- **BDTDAgent:**  
  Integra as etapas de crawling, filtragem, download de PDFs e extração de texto.

- **PDFDownloader:**  
  Gerencia o download e a organização dos arquivos PDF.

---

## Dependências e Testes

**Dependências Necessárias:**
- beautifulsoup4
- requests
- openai
- python-dotenv
- tiktoken
- pandas

Instale-as via pip, se necessário.

**Executando o Script de Teste:**
```bash
python test.py
```

---

## Contribuição e Licença

Contribuições são bem-vindas! Envie pull requests ou abra issues para sugestões e correções.  
Este projeto é licenciado sob a MIT License. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

Aproveite para automatizar sua pesquisa e gerar revisões sistemáticas de maneira prática e eficiente!
