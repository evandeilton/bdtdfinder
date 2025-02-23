# import streamlit as st
# import os
# import sys
# import json
# import glob
# import shutil
# import time
# import random
# import base64
# import subprocess
# import platform
# import csv
# from datetime import datetime
# from pathlib import Path

# # Adiciona o diretório pai ao sys.path para permitir importações
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# from BDTDReviewer import BDTDReviewer
# from BDTDResearchAgent import BDTDAgent  # Usado para a busca

# # --- Funções auxiliares ---
# def load_markdown_file(file_path):
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             return f.read()
#     except Exception as e:
#         return f"Error loading markdown file: {str(e)}"

# def get_pdf_download_link(pdf_path):
#     with open(pdf_path, "rb") as f:
#         bytes_data = f.read()
#     b64 = base64.b64encode(bytes_data).decode()
#     filename = os.path.basename(pdf_path)
#     return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download {filename}</a>'

# def find_pdfs(directory):
#     pdfs = []
#     for root, dirs, files in os.walk(directory):
#         for file in files:
#             if file.lower().endswith('.pdf'):
#                 full_path = os.path.join(root, file)
#                 pdfs.append({
#                     'path': full_path,
#                     'name': file,
#                     'size': os.path.getsize(full_path) / (1024 * 1024),  # Tamanho em MB
#                     'folder': os.path.basename(root)
#                 })
#     return pdfs

# # --- Subclasse para gerar a revisão sem reexecutar a busca ---
# class SelectedBDTDReviewer(BDTDReviewer):
#     """
#     Subclasse de BDTDReviewer que ignora a etapa de busca e utiliza o CSV já existente.
#     O método run() é sobrescrito para utilizar o arquivo filtrado.
#     """
#     def run(self) -> str:
#         try:
#             # Utiliza o arquivo de resultados já filtrado
#             results_file = os.path.join(self.output_dir, "results_page.csv")
#             if not os.path.exists(results_file):
#                 raise Exception("Arquivo de resultados não encontrado. Execute a busca e a filtragem antes.")
                
#             # Lê o CSV com os textos extraídos
#             st.write("Usando arquivo de resultados filtrado:", results_file)  # Debug
#             texts = []
#             with open(results_file, 'r', encoding='utf-8') as f:
#                 reader = csv.DictReader(f)
#                 for i, row in enumerate(reader, 1):
#                     if not row.get('results', "").strip():
#                         continue
#                     if len(texts) >= self.max_title_review:
#                         break
#                     metadata = self._extract_metadata(row['results'])
#                     texts.append(metadata)
#                     if self.debug:
#                         st.write(f"Processado texto {i}: {metadata['title'][:50]}...")
                        
#             # Gera a revisão de literatura
#             review_text = self._generate_review(texts)
#             if self.debug:
#                 st.write("Revisão gerada com sucesso.")
#             # Salva o resultado
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             output_file = os.path.join(self.output_dir, f"literature_review_{timestamp}.md")
#             with open(output_file, 'w', encoding='utf-8') as f:
#                 f.write(review_text)
#             return output_file
                
#         except Exception as e:
#             raise Exception(f"Erro no SelectedBDTDReviewer: {e}")

# # --- UI Principal ---
# def create_ui():
#     st.set_page_config(
#         page_title="BDTD - Agente de Revisão",
#         page_icon="📚",
#         layout="wide",
#         initial_sidebar_state="collapsed"
#     )

#     # --- CSS customizado ---
#     st.markdown("""
#     <style>
#     .stApp {
#         background: linear-gradient(to bottom right, #ffe2e2, #fafafa);
#     }
#     .main {
#         max-width: 1200px;
#         margin: 0 auto;
#         padding: 1rem;
#         background-color: rgba(255, 255, 255, 0.8);
#         border-radius: 12px;
#         box-shadow: 2px 2px 20px rgba(0, 0, 0, 0.1);
#     }
#     h1 {
#         color: #B12A2A !important;
#         font-weight: 700 !important;
#         text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
#     }
#     .centered-search {
#         display: flex; 
#         justify-content: center; 
#         margin-top: 3rem; 
#         margin-bottom: 2rem;
#     }
#     .centered-search > div { width: 80%; }
#     </style>
#     """, unsafe_allow_html=True)

#     # --- Dicionários de idiomas e modelos ---
#     idiomas = {
#         "pt-BR": "🇧🇷 Português (Brasil)",
#         "en-US": "🇺🇸 Inglês (EUA)",
#         "es-ES": "🇪🇸 Espanhol (Espanha)",
#         "fr-FR": "🇫🇷 Francês (França)",
#         "it-IT": "🇮🇹 Italiano (Itália)",
#         "ru-RU": "🇷🇺 Russo (Rússia)"
#     }
#     modelos = {
#         "google/gemini-2.0-pro-exp-02-05:free": {
#             "nome": "Gemini Pro",
#             "desc": "Modelo mais recente do Google, excelente para análise acadêmica"
#         },
#         "openai/chatgpt-4o-latest": {
#             "nome": "GPT-4 Turbo",
#             "desc": "Versão mais atual do GPT-4, com excelente compreensão contextual"
#         }
#     }
#     def modelo_display(model_id):
#         status = "Grátis" if model_id.endswith(":free") else "Pago"
#         return f"{modelos[model_id]['nome']} - {status}"

#     # --- SIDEBAR ---
#     with st.sidebar:
#         st.markdown("## ⚙️ Configurações")
#         with st.expander("🔍 Pesquisa", expanded=True):
#             output_lang = st.selectbox(
#                 "Idioma da Revisão",
#                 options=list(idiomas.keys()),
#                 format_func=lambda x: idiomas[x],
#                 help="Selecione o idioma para a revisão"
#             )
#             col_pages, col_titles = st.columns(2)
#             with col_pages:
#                 max_pages = st.number_input("Máx. Páginas BDTD", min_value=1, value=1)
#             with col_titles:
#                 max_titles = st.number_input("Máx. Títulos", min_value=1, value=5)
#         with st.expander("📥 Download"):
#             download_pdfs = st.checkbox("Baixar PDFs", value=True)
#             scrape_text = st.checkbox("Extrair Texto", value=True)
#             debug = st.checkbox("Modo Debug", value=False)
#             output_dir = st.text_input("Diretório de Saída", value="results")
#             st.info("Atenção: se a pasta existir, ela será limpa e reusada.")
#         with st.expander("🤖 API e Modelo"):
#             st.markdown("""
#                 Para usar o agente de revisão, você precisa de uma chave da **API OpenRouter**.
#                 - [Criar conta na OpenRouter](https://openrouter.ai/signup)
#                 - [Ver preços e créditos](https://openrouter.ai/pricing)
#             """)
#             api_key = st.text_input("Chave da OpenRouter", type="password", value=os.environ.get("OPENROUTER_API_KEY", ""))
#             modelo_selecionado = st.selectbox("Modelo de IA", options=list(modelos.keys()), format_func=modelo_display)

#     # --- ÁREA CENTRAL ---
#     with st.container():
#         st.markdown("""
#             <div class="centered-search">
#                 <div>
#                     <h1 style="text-align: center;">Agente de Revisão Sistemática de Literatura</h1>
#                     <p style="text-align: center; font-size: 1.1rem;">
#                         O sistema busca documentos na BDTD, permite a seleção dos trabalhos desejados e gera uma revisão de literatura.
#                     </p>
#                 </div>
#             </div>
#         """, unsafe_allow_html=True)

#         col_left, col_center, col_right = st.columns([1, 3, 1])
#         with col_center:
#             research_theme = st.text_input("Tema de Pesquisa (Uso Interno)", placeholder="Insira o Tema de Pesquisa", label_visibility="collapsed")
            
#             # Inicializa o estágio se ainda não estiver definido
#             if "stage" not in st.session_state:
#                 st.session_state.stage = "search"
            
#             # --- ETAPA 1: BUSCA DE DOCUMENTOS ---
#             if st.session_state.stage == "search":
#                 if st.button("🔍 Buscar Documentos", type="primary", use_container_width=True):
#                     if not research_theme:
#                         st.error("Por favor, insira um tema de pesquisa")
#                     elif not api_key:
#                         st.error("Por favor, insira sua chave da API OpenRouter")
#                     else:
#                         # Limpa o diretório de saída (se existir) e cria-o novamente
#                         if os.path.exists(output_dir):
#                             try:
#                                 shutil.rmtree(output_dir)
#                                 os.makedirs(output_dir)
#                                 st.success(f"Pasta '{output_dir}' limpa e reusada.")
#                             except Exception as e:
#                                 st.error(f"Erro ao limpar a pasta: {e}")
#                                 st.stop()
#                         else:
#                             os.makedirs(output_dir, exist_ok=True)
#                         try:
#                             # Executa a busca usando BDTDAgent
#                             agent = BDTDAgent(
#                                 subject=research_theme,
#                                 max_pages_limit=max_pages,
#                                 download_pdf=download_pdfs,
#                                 output_dir=output_dir
#                             )
#                             agent.scrape_text = scrape_text
#                             with st.spinner("Buscando documentos..."):
#                                 agent.run()
#                             st.success("Busca concluída!")
#                             results_csv_path = os.path.join(output_dir, "results_page.csv")
#                             if os.path.exists(results_csv_path):
#                                 import pandas as pd
#                                 df_results = pd.read_csv(results_csv_path, sep=";")
#                                 # Se não existir coluna "id", cria-a usando o índice
#                                 if "id" not in df_results.columns:
#                                     df_results.insert(0, "id", range(1, len(df_results) + 1))
#                                 # Adiciona a coluna de seleção
#                                 if "Selecionar" not in df_results.columns:
#                                     df_results.insert(0, "Selecionar", False)
#                                 st.session_state.df_results = df_results
#                                 st.session_state.stage = "selection"
#                             else:
#                                 st.error("Arquivo de resultados não encontrado.")
#                         except Exception as e:
#                             st.error(f"Erro na busca: {e}")

#             # --- ETAPA 2: SELEÇÃO DOS DOCUMENTOS ---
#             if st.session_state.stage == "selection":
#                 st.markdown("### 📚 Documentos Encontrados")
#                 if "df_results" in st.session_state:
#                     # Exibe a tabela com checkboxes para seleção
#                     df = st.session_state.df_results.copy()
#                     edited_df = st.data_editor(
#                         df,
#                         column_config={
#                             "Selecionar": st.column_config.CheckboxColumn("Selecionar", help="Marque para enviar à revisão", default=False),
#                             "id": st.column_config.TextColumn("ID", help="Identificador único"),
#                             "title": st.column_config.TextColumn("Título", help="Título do trabalho"),
#                             "primary_authors": st.column_config.TextColumn("Autor", help="Autor principal"),
#                             "formats": st.column_config.TextColumn("Tipo", help="Tipo do documento"),
#                             "subjects": st.column_config.TextColumn("Assuntos", help="Palavras-chave"),
#                             "urls": st.column_config.LinkColumn("Link", help="URL do documento", display_text="Acessar")
#                         },
#                         hide_index=True
#                     )
#                     # Atualiza o DataFrame no session_state com as possíveis alterações do usuário
#                     st.session_state.df_results = edited_df.copy()
#                     selected_ids = edited_df.loc[edited_df["Selecionar"], "id"].tolist()
#                     st.session_state.selected_docs = selected_ids
#                     n_selected = len(selected_ids)
#                     st.markdown(f"✨ {n_selected} documento{'s' if n_selected != 1 else ''} selecionado{'s' if n_selected != 1 else ''}.")
#                     # Se houver pelo menos um documento selecionado, exibe o botão para enviar a seleção
#                     if n_selected > 0:
#                         if st.button("📝 Enviar Seleção para Revisão", type="primary"):
#                             import pandas as pd
#                             # Filtra os documentos marcados
#                             filtered_df = edited_df[edited_df["Selecionar"] == True]
#                             filtered_csv_path = os.path.join(output_dir, "results_page.csv")
#                             filtered_df.to_csv(filtered_csv_path, sep=";", index=False)
#                             st.success("Seleção salva. Iniciando revisão...")
#                             try:
#                                 reviewer = SelectedBDTDReviewer(
#                                     theme=research_theme,
#                                     output_lang=output_lang,
#                                     max_pages=max_pages,
#                                     max_title_review=n_selected,
#                                     download_pdfs=download_pdfs,
#                                     scrape_text=scrape_text,
#                                     output_dir=output_dir,
#                                     debug=debug,
#                                     openrouter_api_key=api_key,
#                                     model=modelo_selecionado
#                                 )
#                                 with st.spinner("Executando a Revisão..."):
#                                     output_file = reviewer.run()
#                                 st.success("Revisão concluída com sucesso!")
#                                 st.session_state.last_review = output_file
#                                 st.session_state.stage = "finished"
#                                 st.experimental_rerun()
#                             except Exception as e:
#                                 st.error(f"Erro durante a revisão: {e}")
#                 else:
#                     st.info("Nenhum documento encontrado para seleção.")

#             # --- ETAPA 3: FINALIZAÇÃO ---
#             if st.session_state.stage == "finished":
#                 st.success("Processo de revisão finalizado.")
#                 if st.button("🔄 Reiniciar"):
#                     for key in ["stage", "df_results", "selected_docs", "last_review"]:
#                         if key in st.session_state:
#                             del st.session_state[key]
#                     st.experimental_rerun()

#         # --- ABAS DE RESULTADO ---
#         main_container = st.container()
#         with main_container:
#             tabs = st.tabs(["📝 Revisão", "📚 PDFs Baixados"])
#             with tabs[0]:
#                 if "last_review" in st.session_state:
#                     md_content = load_markdown_file(st.session_state.last_review)
#                     col1, col2 = st.columns([6, 1])
#                     with col1:
#                         st.markdown(md_content, unsafe_allow_html=True)
#                     with col2:
#                         with open(st.session_state.last_review, 'rb') as f:
#                             st.download_button(label="📥 Baixar MD", data=f.read(), file_name="revisao_literatura.md", mime="text/markdown")
#                 else:
#                     st.info("Configure sua revisão na área central e clique em 'Buscar Documentos' para começar!")
#                     st.markdown("""
#                         ### Como utilizar?
#                         1. Digite o tema da sua pesquisa.
#                         2. Ajuste as opções no painel lateral, se desejar.
#                         3. Forneça sua chave de API da OpenRouter e escolha seu modelo.
#                         4. Clique em **Buscar Documentos**.
#                         5. Selecione os documentos desejados e clique em **Enviar Seleção para Revisão**.
#                     """)
#             with tabs[1]:
#                 if os.path.exists(output_dir):
#                     pdfs = find_pdfs(output_dir)
#                     if pdfs:
#                         import pandas as pd
#                         df = pd.DataFrame(pdfs)
#                         df['size'] = df['size'].round(2)
#                         df = df.rename(columns={
#                             'name': 'Nome do Arquivo',
#                             'size': 'Tamanho (MB)',
#                             'folder': 'Fonte'
#                         })
#                         st.markdown("### 📊 Estatísticas Gerais")
#                         cols = st.columns(3)
#                         with cols[0]:
#                             st.metric("📚 Total de PDFs", len(pdfs))
#                         with cols[1]:
#                             st.metric("💾 Tamanho Total", f"{df['Tamanho (MB)'].sum():.2f} MB")
#                         with cols[2]:
#                             st.metric("🏛️ Fontes únicas", df['Fonte'].nunique())
#                         st.markdown("### 📂 Arquivos por Pasta")
#                         folders = {}
#                         for pdf in pdfs:
#                             folder_path = os.path.dirname(pdf['path'])
#                             folder_name = os.path.basename(folder_path)
#                             if folder_name not in folders:
#                                 folders[folder_name] = {'pdfs': [], 'total_size': 0, 'path': folder_path}
#                             folders[folder_name]['pdfs'].append(pdf)
#                             folders[folder_name]['total_size'] += pdf['size']
#                         for folder_name, folder_info in sorted(folders.items()):
#                             with st.expander(f"📁 {folder_name} ({len(folder_info['pdfs'])} arquivos, {folder_info['total_size']:.2f} MB)"):
#                                 folder_df = pd.DataFrame(folder_info['pdfs'])
#                                 folder_df['size'] = folder_df['size'].round(2)
#                                 folder_df = folder_df.rename(columns={'name': 'Nome do Arquivo','size': 'Tamanho (MB)'})
#                                 st.dataframe(folder_df[['Nome do Arquivo', 'Tamanho (MB)']], hide_index=True)
#                                 st.markdown("#### Downloads")
#                                 for pdf_info in folder_info['pdfs']:
#                                     st.markdown(f"- {get_pdf_download_link(pdf_info['path'])} ({pdf_info['size']:.2f} MB)", unsafe_allow_html=True)
#                                 if st.button(f"🔍 Abrir Pasta no Explorador", key=f"open_{folder_name}"):
#                                     try:
#                                         if os.name == 'nt':
#                                             subprocess.run(['explorer', folder_info['path']])
#                                         elif platform.system() == 'Darwin':
#                                             subprocess.run(['open', folder_info['path']])
#                                         else:
#                                             subprocess.run(['xdg-open', folder_info['path']])
#                                     except Exception as e:
#                                         st.error("Não foi possível abrir a pasta")
#                     else:
#                         st.info("Nenhum PDF baixado ainda. Habilite o download de PDFs nas configurações e inicie uma revisão.")
#                 else:
#                     st.info("O diretório de saída ainda não existe. Inicie uma revisão para criá-lo.")

# def main():
#     create_ui()

# if __name__ == "__main__":
#     main()
