# novos_relatorios.py
# Requerimentos: pandas, matplotlib, seaborn, numpy, sqlite3, scipy, fpdf

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from fpdf import FPDF
import os


def gerar_todos_relatorios_integrado(sqlite_database, general_entries_table, dir_file_out):
    # Verifica se o caminho de saída existe, se não cria
    if not os.path.exists(dir_file_out):
        os.makedirs(dir_file_out)

    output_dir = os.path.join(dir_file_out, 'relatorios_gerados')
    os.makedirs(output_dir, exist_ok=True)

    def load_general_entries(db_path, table_name):
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()

        # Normalizações para evitar sustos
        if 'Debito' in df.columns:
            df['Debito'] = pd.to_numeric(df['Debito'], errors='coerce').fillna(0.0)
        if 'Credito' in df.columns:
            df['Credito'] = pd.to_numeric(df['Credito'], errors='coerce').fillna(0.0)
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

        # Garante 'AnoMes'
        if 'AnoMes' not in df.columns:
            if 'Data' in df.columns:
                df['AnoMes'] = df['Data'].dt.strftime('%Y-%m')
            else:
                raise ValueError("Coluna 'AnoMes' ausente e não foi possível derivá-la por falta de 'Data'.")

        return df

    def gerar_relatorio_tendencia(df, output_dir):
        tendencia = (
            df.groupby(['AnoMes', 'TIPO'], dropna=False)['Debito']
              .sum()
              .reset_index()
        )
        pivot = tendencia.pivot(index='AnoMes', columns='TIPO', values='Debito').fillna(0)

        fig, ax = plt.subplots(figsize=(15, 6), constrained_layout=True)
        pivot.plot(ax=ax, marker='o')
        ax.set_title("Tendência de Gastos por Categoria")
        ax.set_ylabel("Total Debitado")
        ax.set_xlabel("AnoMes")
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        file_path = os.path.join(output_dir, 'tendencia_gastos_por_categoria.png')
        fig.savefig(file_path)
        plt.close(fig)
        return file_path

    def prever_gastos(df, output_dir):
        tipos = df['TIPO'].dropna().unique()

        # Índice ordinal por mês (YYYY-MM-01)
        df = df.copy()
        df['AnoMesIndex'] = pd.to_datetime(df['AnoMes'] + '-01', errors='coerce').map(pd.Timestamp.toordinal)

        arquivos = []
        for tipo in tipos:
            df_tipo = (
                df.loc[df['TIPO'] == tipo, ['AnoMesIndex', 'Debito']]
                  .dropna()
                  .groupby('AnoMesIndex', as_index=False)['Debito']
                  .sum()
                  .sort_values('AnoMesIndex')
            )
            if len(df_tipo) < 4:
                continue

            x_series = df_tipo['AnoMesIndex']
            y_series = df_tipo['Debito']

            slope, intercept, _, _, _ = stats.linregress(x_series.values, y_series.values)

            # Próximos 3 pontos (aprox. mensal a cada ~30 dias)
            future_x = np.array([x_series.max() + 30, x_series.max() + 60, x_series.max() + 90], dtype=int)
            future_y = intercept + slope * future_x

            fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
            ax.plot(x_series.map(pd.Timestamp.fromordinal), y_series, label='Real')
            ax.plot([pd.Timestamp.fromordinal(val) for val in future_x], future_y, label='Previsto', linestyle='--')
            ax.set_title(f'Previsão de Gastos - {tipo}')
            ax.legend()
            ax.grid(True)
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

            file_path = os.path.join(output_dir, f'forecast_{tipo}.png')
            fig.savefig(file_path)
            arquivos.append(file_path)
            plt.close(fig)

        return arquivos

    def gerar_ranking(df, output_dir):
        arquivos = []
        ranking_origem = (
            df.groupby('Origem', dropna=False)['Debito']
              .sum()
              .sort_values(ascending=False)
              .head(10)
        )
        ranking_tipo = (
            df.groupby('TIPO', dropna=False)['Debito']
              .sum()
              .sort_values(ascending=False)
              .head(10)
        )

        fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
        sns.barplot(x=ranking_origem.values, y=ranking_origem.index, ax=ax)
        ax.set_title("Top 10 Origens por Gastos")
        path1 = os.path.join(output_dir, 'ranking_origem.png')
        fig.savefig(path1)
        arquivos.append(path1)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
        sns.barplot(x=ranking_tipo.values, y=ranking_tipo.index, ax=ax)
        ax.set_title("Top 10 Tipos por Gastos")
        path2 = os.path.join(output_dir, 'ranking_tipo.png')
        fig.savefig(path2)
        arquivos.append(path2)
        plt.close(fig)

        return arquivos

    def verificar_consistencia(df, output_dir):
        inconsistencias = {
            'data_nula': df[df['Data'].isnull()] if 'Data' in df.columns else pd.DataFrame(),
            'tipo_nulo': df[df['TIPO'].isnull()] if 'TIPO' in df.columns else pd.DataFrame(),
            'credito_negativo': df[df['Credito'] < 0] if 'Credito' in df.columns else pd.DataFrame(),
            'debito_negativo': df[df['Debito'] < 0] if 'Debito' in df.columns else pd.DataFrame(),
        }
        output_file = os.path.join(output_dir, 'relatorio_consistencia.txt')
        # Grava sempre em UTF-8 para padronizar
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            for nome, subset in inconsistencias.items():
                f.write(f"\n### {nome.upper()} - {len(subset)} ocorrencias\n")
                if not subset.empty:
                    f.write(subset.head(5).to_string())
                else:
                    f.write("(sem ocorrencias)")
                f.write("\n---\n")
        return output_file

    class PDFReport(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Relatórios PDW', ln=True, align='C')

        def add_image(self, image_path):
            self.add_page()
            self.image(image_path, x=10, y=25, w=180)

        def add_text(self, text_file):
            self.add_page()
            self.set_auto_page_break(auto=True, margin=15)
            # Lê preferindo UTF-8; se vier lixo legado, tenta cp1252
            try:
                with open(text_file, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
            except UnicodeDecodeError:
                with open(text_file, 'r', encoding='cp1252', errors='replace') as file:
                    lines = file.readlines()

            self.set_font('Courier', '', 10)
            for line in lines:
                self.multi_cell(0, 5, line.rstrip('\n'))

    # Linha separadora para logs
    out_line = '-' * 80

    print("Executando geração de relatórios analíticos avançados...")
    output_dir = os.path.join(dir_file_out, 'relatorios_gerados')
    os.makedirs(output_dir, exist_ok=True)

    df = load_general_entries(sqlite_database, general_entries_table)
    imagens = [gerar_relatorio_tendencia(df, output_dir)]
    imagens += prever_gastos(df, output_dir)
    imagens += gerar_ranking(df, output_dir)
    texto = verificar_consistencia(df, output_dir)

    pdf = PDFReport()
    for img in imagens:
        pdf.add_image(img)
    pdf.add_text(texto)

    pdf_path = os.path.join(output_dir, 'relatorios_pdw.pdf')
    pdf.output(pdf_path)

    print(out_line)
    print("Relatórios analíticos avançados gerados com sucesso.")
    print(f"Relatório PDF salvo em: {pdf_path}")
    print(out_line)
