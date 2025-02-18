import streamlit as st
import os
import sys
import json
import glob
from pathlib import Path
import base64
import subprocess
import platform
import shutil
import time
import random

# Adiciona o diretório pai ao sys.path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from bdtdfinder.BDTDReviewer import BDTDReviewer


def load_markdown_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading markdown file: {str(e)}"


def get_pdf_download_link(pdf_path):
    with open(pdf_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    filename = os.path.basename(pdf_path)
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download {filename}</a>'


def find_pdfs(directory):
    pdfs = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                pdfs.append({
                    'path': full_path,
                    'name': file,
                    'size': os.path.getsize(full_path) / (1024 * 1024),  # Tamanho em MB
                    'folder': os.path.basename(root)
                })
    return pdfs


def main():
    st.set_page_config(
        page_title="BDTD - Agente de Revisão",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # --- CSS customizado para background gradiente e melhorias ---
    st.markdown("""
    <style>
    /* Gradiente no fundo da aplicação */
    .stApp {
        background: linear-gradient(to bottom right, #ffe2e2, #fafafa);
    }
    /* Ajusta contêiner principal */
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 1rem;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 12px;
        box-shadow: 2px 2px 20px rgba(0, 0, 0, 0.1);
    }
    /* Título estilizado */
    h1 {
        color: #B12A2A !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    /* Centraliza alguns elementos */
    .centered-search {
        display: flex; 
        justify-content: center; 
        margin-top: 3rem; 
        margin-bottom: 2rem;
    }
    .centered-search > div { width: 80%; }
    /* Inputs de texto personalizados */
    div[data-baseweb="input"] > div > input {
        width: 100% !important;
        padding: 0.75rem;
        font-size: 1.1rem;
        border-radius: 8px;
        border: 1px solid #ccc;
        transition: border 0.3s ease;
    }
    div[data-baseweb="input"] > div > input:focus {
        border: 1px solid #E91E63;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Dicionário de idiomas com emojis ---
    idiomas = {
        "pt-BR": "🇧🇷 Português (Brasil)",
        "en-US": "🇺🇸 Inglês (EUA)",
        "es-ES": "🇪🇸 Espanhol (Espanha)",
        "fr-FR": "🇫🇷 Francês (França)",
        "it-IT": "🇮🇹 Italiano (Itália)",
        "ru-RU": "🇷🇺 Russo (Rússia)"
        # "ar-AE": "🇦🇪 Árabe (Emirados)",
        # "zh-HK": "🇭🇰 Chinês (Hong Kong)"
    }

    # --- Dicionário de modelos ---
    modelos = {
        "google/gemini-2.0-pro-exp-02-05:free": {
            "nome": "Gemini Pro",
            "desc": "Modelo mais recente do Google, excelente para análise acadêmica"
        },
        "cognitivecomputations/dolphin3.0-r1-mistral-24b:free": {
            "nome": "Dolphin Mistral 24B R1",
            "desc": ""
        },
        "openai/o3-mini-high": {
            "nome": "OpenAI O3 Mini High",
            "desc": ""
        },
        "openai/o3-mini": {
            "nome": "OpenAI O3 Mini",
            "desc": ""
        },
        "openai/chatgpt-4o-latest": {
            "nome": "GPT-4 Turbo",
            "desc": "Versão mais atual do GPT-4, com excelente compreensão contextual"
        },
        "openai/gpt-4o-mini": {
            "nome": "GPT-4O Mini",
            "desc": ""
        },
        "google/gemini-2.0-flash-001": {
            "nome": "Google Gemini Flash 001",
            "desc": ""
        },
        "google/gemini-2.0-flash-thinking-exp:free": {
            "nome": "Gemini Pro Flash",
            "desc": "Versão otimizada do Gemini Pro, mais rápida mas menos detalhada"
        },
        "google/gemini-2.0-flash-lite-preview-02-05:free": {
            "nome": "Google Gemini Flash Lite Preview",
            "desc": ""
        },
        "deepseek/deepseek-r1-distill-llama-70b:free": {
            "nome": "DeepSeek R1 Distill Llama 70B",
            "desc": ""
        },
        "deepseek/deepseek-r1-distill-qwen-32b": {
            "nome": "DeepSeek R1 Distill Qwen 32B",
            "desc": ""
        },
        "deepseek/deepseek-r1:free": {
            "nome": "DeepSeek R1",
            "desc": ""
        },
        "qwen/qwen-plus": {
            "nome": "Qwen Plus",
            "desc": ""
        },
        "qwen/qwen-max": {
            "nome": "Qwen Max",
            "desc": ""
        },
        "qwen/qwen-turbo": {
            "nome": "Qwen Turbo",
            "desc": ""
        },
        "mistralai/codestral-2501": {
            "nome": "Mistralai Codestral 2501",
            "desc": ""
        },
        "mistralai/mistral-small-24b-instruct-2501:free": {
            "nome": "Mistralai Mistral Small 24B Instruct 2501",
            "desc": ""
        },
        "anthropic/claude-3.5-haiku-20241022:beta": {
            "nome": "Claude 3.5 Haiku Beta",
            "desc": ""
        },
        "anthropic/claude-3.5-sonnet": {
            "nome": "Claude 3.5 Sonnet",
            "desc": ""
        },
        "perplexity/sonar-reasoning": {
            "nome": "Perplexity Sonar Reasoning",
            "desc": ""
        },
        "perplexity/sonar": {
            "nome": "Perplexity Sonar",
            "desc": ""
        },
        "perplexity/llama-3.1-sonar-large-128k-online": {
            "nome": "Perplexity Llama 3.1 Sonar Large 128k Online",
            "desc": ""
        }
    }

    # --- Função para formatar exibição do modelo (opcional) ---
    def modelo_display(model_id):
        status = "Grátis" if model_id.endswith(":free") else "Pago"
        return f"{modelos[model_id]['nome']} - {status}"

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("## ⚙️ Configurações")
        with st.expander("🔍 Pesquisa", expanded=True):
            output_lang = st.selectbox(
                "Idioma da Revisão",
                options=list(idiomas.keys()),
                format_func=lambda x: idiomas[x],
                help="Selecione o idioma para a revisão"
            )
            col_pages, col_titles = st.columns(2)
            with col_pages:
                max_pages = st.number_input(
                    "Máx. Páginas BDTD",
                    min_value=1,
                    value=1,
                    help="Número máximo de páginas para buscar na BDTD.\nCada página reorna antre 1 e 20 resultados"
                )
            with col_titles:
                max_titles = st.number_input(
                    "Máx. Títulos",
                    min_value=1,
                    value=5,
                    help="Número máximo de títulos para incluir na revisão.\nCuidado com muitos títulos, pois isso consome muitos tokens!"
                )
        with st.expander("📥 Download"):
            download_pdfs = st.checkbox(
                "Baixar PDFs",
                value=True,
                help="Baixar arquivos PDF"
            )
            scrape_text = st.checkbox(
                "Extrair Texto",
                value=True,
                help="Extrair conteúdo textual das páginas web"
            )
            debug = st.checkbox(
                "Modo Debug",
                value=False,
                help="Mostrar informações detalhadas"
            )
            output_dir = st.text_input(
                "Diretório de Saída",
                value="results",
                help="Diretório onde os resultados serão salvos"
            )
            st.info("Atenção: se a pasta existir, ela será limpa e reutilizada.")
        with st.expander("🤖 API e Modelo"):
            st.markdown("""
                Para usar o agente de revisão, você precisa de uma chave da **API OpenRouter**.
                
                - [Criar conta na OpenRouter](https://openrouter.ai/signup)
                - [Ver preços e créditos](https://openrouter.ai/pricing)
            """)
            api_key = st.text_input(
                "Chave da OpenRouter",
                type="password",
                value=os.environ.get("OPENROUTER_API_KEY", ""),
                help="Sua chave de API da OpenRouter"
            )
            modelo_selecionado = st.selectbox(
                "Modelo de IA",
                options=list(modelos.keys()),
                format_func=modelo_display,
                help="Selecione o modelo de IA que deseja usar"
            )

    # --- ÁREA CENTRAL ---
    with st.container():
        st.markdown("""
            <div class="centered-search">
                <div>
                    <h1 style="text-align: center;">
                        Agente de Revisão Sistemática de Literatura
                    </h1>
                    <p style="text-align: center; font-size: 1.1rem;">
                        O sistema realiza buscas automáticas na Biblioteca Digital Brasileira de Teses e Dissertações (BDTD), processa os resultados usando Inteligência Artificial (AI) e gera uma revisão de literatura estruturada sobre o tema pesquisado.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_left, col_center, col_right = st.columns([1, 3, 1])
        with col_center:
            research_theme = st.text_input(
                label="Tema de Pesquisa (Uso Interno)",
                placeholder="Insira o Tema de Pesquisa",
                label_visibility="collapsed"
            )
            iniciar = st.button("🚀 Iniciar Revisão", type="primary", use_container_width=True)
            if iniciar:
                if not research_theme:
                    st.error("Por favor, insira um tema de pesquisa")
                elif not api_key:
                    st.error("Por favor, insira sua chave da API OpenRouter")
                else:
                    # Se o diretório existir, limpar
                    if os.path.exists(output_dir):
                        try:
                            shutil.rmtree(output_dir)
                            os.makedirs(output_dir)
                            st.success(f"Pasta '{output_dir}' limpa e reusada.")
                        except Exception as e:
                            st.error(f"Erro ao limpar a pasta: {str(e)}")
                            st.stop()

                    curiosidades = [
                        "Você sabia que o primeiro periódico científico surgiu em 1665?",
                        "Atualmente, estima-se que sejam publicados mais de 4 mil artigos científicos por dia.",
                        "A revisão sistemática ajuda a evitar vieses e a organizar melhor as evidências disponíveis.",
                        "Técnicas de IA aceleram muito o processo de triagem de artigos em revisões sistemáticas.",
                        "O número e (2,71828...) foi descoberto ao estudar juros compostos continuamente.",
                        "A conjectura de Goldbach, que todo número par maior que 2 é soma de dois primos, ainda não foi provada.",
                        "O teorema de Fermat ficou sem prova por mais de 350 anos até ser demonstrado em 1995.",
                        "A sequência de Fibonacci aparece naturalmente em diversos padrões da natureza.",
                        "O zero como número só foi aceito na matemática ocidental no século XII.",
                        "A constante π já foi calculada com mais de 31 trilhões de dígitos.",
                        "A teoria do caos começou com o estudo do clima por Edward Lorenz em 1961.",
                        "Existem números que são normais, onde todos os dígitos aparecem com igual frequência.",
                        "A transformada de Fourier permite decompor qualquer som em ondas senoidais puras.",
                        "O princípio da incerteza de Heisenberg estabelece limites fundamentais para medições.",
                        "A teoria dos grafos começou com um problema sobre pontes na cidade de Königsberg.",
                        "O paradoxo dos gêmeos da relatividade especial foi confirmado experimentalmente.",
                        "O método de Monte Carlo foi desenvolvido durante o Projeto Manhattan.",
                        "A criptografia RSA se baseia na dificuldade de fatorar números grandes.",
                        "O algoritmo PageRank do Google é baseado em álgebra linear.",
                        "A dimensão fractal pode ser um número não inteiro.",
                        "A demonstração das quatro cores levou 1936 configurações testadas por computador.",
                        "O teorema fundamental do cálculo unifica derivadas e integrais.",
                        "A teoria das categorias unifica diferentes áreas da matemática.",
                        "A conjectura de Poincaré só foi provada em 2003 por Grigori Perelman."
                    ]
                    random.shuffle(curiosidades)

                    # Começa o processo de revisão
                    with st.spinner("Preparando o ambiente..."):
                        # Exibimos “curiosidades” antes (ou durante) — mas só veremos tudo ao final
                        for fact in curiosidades[:1]:
                            st.write(f"**Curiosidade:** {fact}")
                            time.sleep(0.5)

                        try:
                            reviewer = BDTDReviewer(
                                theme=research_theme,
                                output_lang=output_lang,
                                max_pages=max_pages,
                                max_title_review=max_titles,
                                download_pdfs=download_pdfs,
                                scrape_text=scrape_text,
                                output_dir=output_dir,
                                debug=debug,
                                openrouter_api_key=api_key,
                                model=modelo_selecionado
                            )

                            # Agora sim chamamos a lógica de revisão
                            with st.spinner("Executando a Revisão..."):
                                output_file = reviewer.run()

                            # Concluído
                            st.session_state.last_review = output_file
                            st.success("Revisão concluída com sucesso!")
                            st.balloons()  # Efeito de balões para dar feedback
                            st.rerun()

                        except Exception as e:
                            st.error(f"Erro durante a revisão: {str(e)}")

    # --- ABAS DE RESULTADO ---
    main_container = st.container()
    with main_container:
        tabs = st.tabs(["📝 Revisão", "📚 PDFs Baixados"])
        
        # Aba 1: Revisão
        with tabs[0]:
            if 'last_review' in st.session_state:
                md_content = load_markdown_file(st.session_state.last_review)
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(md_content, unsafe_allow_html=True)
                with col2:
                    with open(st.session_state.last_review, 'rb') as f:
                        st.download_button(
                            label="📥 Baixar MD",
                            data=f.read(),
                            file_name="revisao_literatura.md",
                            mime="text/markdown"
                        )
            else:
                # Tenta carregar a revisão existente, se houver
                latest_md = sorted(glob.glob(os.path.join(output_dir, "literature_review_*.md")))
                if latest_md:
                    md_content = load_markdown_file(latest_md[-1])
                    col1, col2 = st.columns([6, 1])
                    with col1:
                        st.markdown(md_content, unsafe_allow_html=True)
                    with col2:
                        with open(latest_md[-1], 'rb') as f:
                            st.download_button(
                                "📥 Baixar MD",
                                f.read(),
                                file_name="revisao_literatura.md",
                                mime="text/markdown"
                            )
                else:
                    st.info("👈 Configure sua revisão na área central e clique em 'Iniciar Revisão' para começar!")
                    st.markdown("""
                        ### Como utilizar?
                        1. Digite o tema da sua pesquisa na barra central.
                        2. Ajuste as opções no painel lateral, se desejar.
                        3. Forneça sua chave de API da OpenRouter e escolha seu modelo favorito.
                        4. Clique em **Iniciar Revisão** para começar o processo.
                    """)

        # Aba 2: PDFs Baixados
        with tabs[1]:
            if os.path.exists(output_dir):
                pdfs = find_pdfs(output_dir)
                if pdfs:
                    import pandas as pd
                    df = pd.DataFrame(pdfs)
                    df['size'] = df['size'].round(2)
                    df = df.rename(columns={
                        'name': 'Nome do Arquivo',
                        'size': 'Tamanho (MB)',
                        'folder': 'Fonte'
                    })

                    st.markdown("### 📊 Estatísticas Gerais")
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("📚 Total de PDFs", len(pdfs))
                    with cols[1]:
                        st.metric("💾 Tamanho Total", f"{df['Tamanho (MB)'].sum():.2f} MB")
                    with cols[2]:
                        st.metric("🏛️ Fontes únicas", df['Fonte'].nunique())

                    st.markdown("### 📂 Arquivos por Pasta")
                    folders = {}
                    for pdf in pdfs:
                        folder_path = os.path.dirname(pdf['path'])
                        folder_name = os.path.basename(folder_path)
                        if folder_name not in folders:
                            folders[folder_name] = {
                                'pdfs': [],
                                'total_size': 0,
                                'path': folder_path
                            }
                        folders[folder_name]['pdfs'].append(pdf)
                        folders[folder_name]['total_size'] += pdf['size']
                    
                    for folder_name, folder_info in sorted(folders.items()):
                        with st.expander(f"📁 {folder_name} ({len(folder_info['pdfs'])} arquivos, {folder_info['total_size']:.2f} MB)"):
                            folder_df = pd.DataFrame(folder_info['pdfs'])
                            folder_df['size'] = folder_df['size'].round(2)
                            folder_df = folder_df.rename(columns={
                                'name': 'Nome do Arquivo',
                                'size': 'Tamanho (MB)'
                            })
                            st.dataframe(folder_df[['Nome do Arquivo', 'Tamanho (MB)']], hide_index=True)
                            st.markdown("#### Downloads")
                            for pdf_info in folder_info['pdfs']:
                                st.markdown(
                                    f"- {get_pdf_download_link(pdf_info['path'])} ({pdf_info['size']:.2f} MB)",
                                    unsafe_allow_html=True
                                )
                            if st.button(f"🔍 Abrir Pasta no Explorador", key=f"open_{folder_name}"):
                                try:
                                    if os.name == 'nt':
                                        subprocess.run(['explorer', folder_info['path']])
                                    elif platform.system() == 'Darwin':
                                        subprocess.run(['open', folder_info['path']])
                                    else:
                                        subprocess.run(['xdg-open', folder_info['path']])
                                except Exception as e:
                                    st.error("Não foi possível abrir a pasta")
                else:
                    st.info("Nenhum PDF baixado ainda. Habilite o download de PDFs nas configurações e inicie uma revisão.")
            else:
                st.info("O diretório de saída ainda não existe. Inicie uma revisão para criá-lo.")


if __name__ == "__main__":
    main()
