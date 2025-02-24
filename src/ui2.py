import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime

from BDTDResearchAgent import BDTDAgent
from BDTDUiReviewer import BDTDUiReviewer

# Configuração da página
st.set_page_config(
    page_title="BDTD Intelligent UI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Lista de modelos Gemini disponíveis
GEMINI_MODELS = [
    "google/gemini-2.0-flash-001",
    "google/gemini-2.0-flash-thinking-exp:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "google/gemini-2.0-pro-exp-02-05:free"
]

# Estilo CSS personalizado
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .sidebar-content {
        padding: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #dff0d8;
        border: 1px solid #d6e9c6;
    }
    .warning-box {
        background-color: #fcf8e3;
        border: 1px solid #faebcc;
    }
    .error-box {
        background-color: #f2dede;
        border: 1px solid #ebccd1;
    }
    </style>
    """, unsafe_allow_html=True)

def create_header():
    """Cria o cabeçalho da aplicação com título e descrição"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📚 BDTD Intelligent UI")
        st.markdown("""
        <p style='font-size: 1.2em; color: #666;'>
        Interface inteligente para revisão de literatura em duas etapas, com tabela 
        interativa e geração automática de revisões a partir dos trabalhos selecionados.
        </p>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='text-align: right; color: #666;'>
        Data: {datetime.now().strftime('%d/%m/%Y')}
        </div>
        """, unsafe_allow_html=True)

def create_sidebar():
    """Configura a barra lateral com parâmetros avançados"""
    with st.sidebar:
        st.markdown("""
        <h2 style='text-align: center; color: #2e7d32;'>
        ⚙️ Configurações
        </h2>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📌 Parâmetros Básicos")
        theme = st.text_input("🔍 Tema de pesquisa", value="Ciência de Dados",
                            help="Digite o tema principal da sua pesquisa")
        
        output_lang = st.selectbox("🌍 Idioma do resultado",
                                 ["pt-BR", "en"],
                                 index=0,
                                 help="Selecione o idioma para a revisão gerada")
        
        max_pages = st.slider("📄 Máximo de páginas",
                            min_value=1,
                            max_value=10,
                            value=1,
                            help="Defina o número máximo de páginas para busca")

        st.markdown("### 🛠️ Configurações Avançadas")
        with st.expander("Expandir opções avançadas"):
            download_pdfs = st.checkbox("📥 Download de PDFs",
                                    value=False,
                                    help="Habilita o download automático dos PDFs")
            
            scrape_text = st.checkbox("📝 Extração de texto",
                                    value=True,
                                    help="Habilita a extração de texto das páginas")
            
            output_dir = st.text_input("📂 Diretório de saída",
                                    value="results",
                                    help="Pasta onde os resultados serão salvos")
            
            debug = st.checkbox("🐛 Modo debug",
                            value=False,
                            help="Ativa logs detalhados para debugging")
            
            # Substituído o text_input por selectbox para os modelos
            model = st.selectbox("🤖 Modelo OpenRouter",
                               options=GEMINI_MODELS,
                               index=3,  # Definindo o modelo pro como padrão
                               help="Selecione o modelo de IA a ser usado")

        return theme, output_lang, max_pages, download_pdfs, scrape_text, output_dir, debug, model

def display_interactive_table(df):
    """Exibe a tabela interativa com estilização aprimorada"""
    st.markdown("### 📋 Resultados da Pesquisa")
    
    # Preparando os dados para exibição
    df_display = df[["selected", "primary_authors", "title", "urls"]].copy()
    df_display = df_display.rename(columns={
        "selected": "✔",
        "primary_authors": "Autor(es)",
        "title": "Título",
        "urls": "Links"
    })
    
    # Adicionando estilo à tabela
    st.markdown("""
    <style>
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 1rem;
    }
    .stDataFrame td {
        font-size: 0.9em;
    }
    .stDataFrame th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Modificado para usar column_config e melhorar a interação com checkboxes
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        key="my_table_editor",
        height=400,
        column_config={
            "✔": st.column_config.CheckboxColumn(
                "Selecionar",
                help="Marque para incluir na revisão",
                default=False
            ),
            "Links": st.column_config.LinkColumn("Links")
        },
        disabled=["Autor(es)", "Título", "Links"]
    )
    
    return edited_df

def execute_search(theme, max_pages, download_pdfs, scrape_text, output_dir):
    """Executa a busca na BDTD"""
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            st.error(f"Erro ao limpar o diretório '{output_dir}': {e}")
            return None
    os.makedirs(output_dir, exist_ok=True)

    with st.spinner("🔍 Realizando busca na BDTD..."):
        agent = BDTDAgent(
            subject=theme,
            max_pages_limit=max_pages,
            download_pdf=False,
            output_dir=output_dir
        )
        agent.scrape_text = scrape_text
        agent.run()

        filtered_csv_path = os.path.join(output_dir, "results_filtered.csv")
        if not os.path.exists(filtered_csv_path):
            st.warning("⚠️ Nenhum resultado encontrado ou CSV filtrado não foi gerado.")
            return None
        
        df_filtered = pd.read_csv(filtered_csv_path, sep=";")
        if df_filtered.empty:
            st.warning("⚠️ Nenhum registro após a filtragem.")
            return None
        
        if "selected" not in df_filtered.columns:
            df_filtered["selected"] = False
        if "id" not in df_filtered.columns:
            df_filtered["id"] = ""
            
        return df_filtered

def generate_review(df_full, theme, max_pages, download_pdfs, scrape_text, output_dir, output_lang, debug, model):
    """Gera a revisão de literatura"""
    df_final = df_full.copy()
    df_selected = df_final[df_final["selected"] == True]
    
    if df_selected.empty:
        st.warning("⚠️ Nenhum trabalho foi selecionado!")
        return
    
    st.write("📑 Trabalhos selecionados (primeiras linhas):", df_selected.head())
    
    if download_pdfs:
        with st.spinner("📥 Baixando PDFs dos trabalhos selecionados..."):
            selected_csv_path = os.path.join(output_dir, "results_selected.csv")
            df_selected.to_csv(selected_csv_path, index=False, encoding="utf-8", sep=";")
            st.write("📊 CSV dos trabalhos selecionados:", df_selected[["id", "urls"]].head())
            
            temp_agent = BDTDAgent(
                subject=theme,
                max_pages_limit=max_pages,
                download_pdf=False,
                output_dir=output_dir
            )
            temp_agent.download_pdfs(selected_csv_path)
            temp_agent.sanity_check_downloads()
            st.success("✅ Download dos PDFs concluído!")
    
    results_page_path = os.path.join(output_dir, "results_page.csv")
    if not os.path.exists(results_page_path):
        st.error("❌ O arquivo results_page.csv não existe. Verifique se 'scrape_text' estava habilitado na Etapa 1.")
        return
    
    df_results_page = pd.read_csv(results_page_path, encoding="utf-8")
    if df_results_page.empty:
        st.error("❌ results_page.csv está vazio. Não há texto para enviar ao revisor.")
        return
    
    selected_ids = set(df_selected["id"].tolist())
    df_selected_pages = df_results_page[df_results_page["id"].isin(selected_ids)]
    if df_selected_pages.empty:
        st.error("❌ Nenhum texto corresponde aos IDs selecionados. Verifique se a raspagem foi realizada.")
        return
    
    df_selected_pages.to_csv(results_page_path, index=False, encoding="utf-8")
    
    with st.spinner("📝 Gerando a revisão..."):
        reviewer = BDTDUiReviewer(
            theme=theme,
            output_lang=output_lang,
            download_pdfs=download_pdfs,
            scrape_text=scrape_text,
            output_dir=output_dir,
            debug=debug,
            openrouter_api_key=None,
            model=model
        )
        try:
            review_file = reviewer.run_ui()
            st.success(f"✅ Revisão concluída! Arquivo gerado em: {review_file}")
            with open(review_file, "r", encoding="utf-8") as f:
                review_text = f.read()
            st.markdown("### 📄 Conteúdo da Revisão Gerada")
            st.markdown(review_text)
        except Exception as e:
            st.error(f"❌ Erro durante geração da revisão: {e}")

def main():
    create_header()
    params = create_sidebar()
    theme, output_lang, max_pages, download_pdfs, scrape_text, output_dir, debug, model = params
    
    # Seção 1: Busca e Listagem
    st.markdown("""
    ## 🔍 Procurar Trabalhos...
    """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        Esta etapa realiza:
        - 📊 Busca sistemática na BDTD
        - 🔍 Filtragem dos resultados
        - 📝 Extração de texto (opcional)
        - 📋 Exibição em tabela interativa
        """)
    
    # Botão de busca estilizado
    st.markdown("""
    <style>
    .search-button {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 24px;
        padding: 0 16px;
        border: none;
        height: 44px;
        min-width: 120px;
        font-size: 16px;
        font-weight: 500;
        letter-spacing: 0.25px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #45a049;
        box-shadow: 0 1px 6px rgba(32,33,36,.28);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="search-button">', unsafe_allow_html=True)
    if st.button("🚀 Buscar", key="search_button"):
        df_filtered = execute_search(theme, max_pages, download_pdfs, scrape_text, output_dir)
        if df_filtered is not None:
            st.session_state["df_full"] = df_filtered
            st.success("✅ Busca concluída com sucesso!")
    
    # Exibição da tabela de resultados com melhor gestão de estado
    if "df_full" in st.session_state:
        df_edited = display_interactive_table(st.session_state["df_full"])
        # Atualizando o estado apenas quando houver mudanças
        if df_edited is not None and "✔" in df_edited.columns:
            st.session_state["df_full"]["selected"] = df_edited["✔"].values
    
    st.markdown("---")
    
    # Seção 2: Geração da Revisão
    st.markdown("""
    ## 📝 Elaboração da Revisão
    """)
    
    if st.button("📊 Gerar Revisão", key="review_button"):
        if "df_full" not in st.session_state:
            st.warning("⚠️ Execute a Etapa 1 primeiro!")
        else:
            generate_review(
                st.session_state["df_full"],
                theme,
                max_pages,
                download_pdfs,
                scrape_text,
                output_dir,
                output_lang,
                debug,
                model
            )

if __name__ == "__main__":
    main()
