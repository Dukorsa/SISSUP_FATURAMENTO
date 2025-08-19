import sqlite3
import pandas as pd
from datetime import datetime
import os

from config import get_table_configs, get_clean_headers

class Database:

    def __init__(self, db_name="database.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS laudos_apac (id INTEGER PRIMARY KEY, nome TEXT, tratamento_procedimento TEXT, situacao TEXT, data_saida TEXT, n_apac TEXT, final TEXT, data_importacao DATE)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS sessoes_hd (id INTEGER PRIMARY KEY, nome TEXT, hd_normais INTEGER, hd_extras INTEGER, hd_remarcadas INTEGER, data_importacao DATE)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS estatistica_mensal (id INTEGER PRIMARY KEY, nome TEXT, dt_entr TEXT, hep_c TEXT, hbsag TEXT, hiv TEXT, alta_amb TEXT, obito TEXT, data_importacao DATE)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS eventos_cateter (id INTEGER PRIMARY KEY, data TEXT, acesso TEXT, nome TEXT, evento TEXT, tipo TEXT, localizacao TEXT, convenio TEXT, nao_cobra TEXT, data_importacao DATE)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS faturamento_geral (id INTEGER PRIMARY KEY, posicao TEXT, convenio TEXT, data TEXT, cod_prontuario TEXT, nome TEXT, matricula TEXT, numero_guia TEXT, senha_autoriz TEXT, lote TEXT, data_envio TEXT, protocolo TEXT, titulo TEXT, data_inc_titulo TEXT, executante TEXT, tipo_atendimento TEXT, servico_material TEXT, codigo TEXT, grupo TEXT, quant REAL, total REAL, tipo_guia TEXT, programa_tratamento TEXT, tipo_cobranca TEXT, data_importacao DATE)")
            self.cursor.execute("CREATE TABLE IF NOT EXISTS faturamento_convenio (id INTEGER PRIMARY KEY, posicao TEXT, convenio TEXT, data TEXT, cod_prontuario TEXT, nome TEXT, matricula TEXT, numero_guia TEXT, senha_autoriz TEXT, lote TEXT, data_envio TEXT, protocolo TEXT, titulo TEXT, data_inc_titulo TEXT, executante TEXT, tipo TEXT, servico_material TEXT, codigo TEXT, grupo TEXT, quant REAL, total REAL, tipo_guia TEXT, programa_tratamento TEXT, tipo_apresentacao TEXT, plano TEXT, data_importacao DATE)")
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao criar tabelas: {e}")

    def import_from_csv(self, file_path, table_name):
        if not file_path:
            return False

        configs = get_table_configs()
        table_config = configs.get(table_name)
        clean_headers = get_clean_headers(table_name)

        if not table_config or not clean_headers:
            raise ValueError(f"Não há configuração para a tabela '{table_name}'.")

        df = pd.read_csv(file_path, sep=';', encoding='latin-1', header=None, skiprows=1, dtype=str)

        if len(df.columns) != len(clean_headers):
            raise ValueError(f"O arquivo '{os.path.basename(file_path)}' possui {len(df.columns)} colunas, mas a configuração espera {len(clean_headers)}.")

        df.columns = clean_headers

        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        date_format = '%d/%m/%Y %H:%M:%S'
        date_cols = {
            'laudos_apac': ['data_saida', 'final'],
            'estatistica_mensal': ['dt_entr'],
            'eventos_cateter': ['data'],
            'faturamento_geral': ['data', 'data_envio', 'data_inc_titulo'],
            'faturamento_convenio': ['data', 'data_envio', 'data_inc_titulo']
        }
        if table_name in date_cols:
            for col in date_cols[table_name]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], format=date_format, errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        df.dropna(subset=['nome'], inplace=True)
        df = df[df['nome'] != '']
        if df.empty:
            return False

        final_columns = table_config['final_columns']
        df_final = df[final_columns].copy()
        df_final['data_importacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        numeric_cols_map = {
            "sessoes_hd": ['hd_normais', 'hd_extras', 'hd_remarcadas'],
            "faturamento_geral": ['quant', 'total'],
            "faturamento_convenio": ['quant', 'total']
        }
        if table_name in numeric_cols_map:
            for col in numeric_cols_map[table_name]:
                if col in df_final.columns:
                    df_final[col] = df_final[col].astype(str).str.replace(',', '.', regex=False)
                    df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)

        if table_name == 'sessoes_hd':
            for col in numeric_cols_map[table_name]:
                df_final[col] = df_final[col].astype(int)

        df_final.to_sql(table_name, self.conn, if_exists='replace', index=False)
        self.conn.commit()
        return True

    def get_last_import_info(self, table_name):
        try:
            query = f"SELECT data_importacao, COUNT(*) as linhas FROM {table_name} GROUP BY data_importacao ORDER BY data_importacao DESC LIMIT 1"
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            if row:
                return {'data_importacao': row[0], 'linhas': row[1]}
        except Exception:
            return None

    def generate_geral_report_data(self):
        try:
            df_apac = pd.read_sql_query("SELECT * FROM laudos_apac", self.conn, parse_dates=['data_saida', 'final'])
            df_estatistica = pd.read_sql_query("SELECT * FROM estatistica_mensal", self.conn, parse_dates=['dt_entr'])
            df_cateter = pd.read_sql_query("SELECT * FROM eventos_cateter", self.conn)
            df_faturamento = pd.read_sql_query("SELECT * FROM faturamento_geral", self.conn)
        except pd.io.sql.DatabaseError as e:
            raise ValueError(f"Erro ao ler tabelas do banco de dados: {e}. Verifique se todas as fontes de dados foram importadas.")

        df_faturamento_sus = df_faturamento[df_faturamento['convenio'].str.upper() == 'SUS'].copy()
        df_faturamento_unique = df_faturamento_sus.drop_duplicates(subset=['nome', 'numero_guia', 'servico_material'], keep='first').copy()
        df_hemodialise = df_faturamento_unique[df_faturamento_unique['grupo'].str.contains('Hemodiálise', case=False, na=False)].copy()
        df_hd_normais = df_hemodialise[df_hemodialise['servico_material'].str.contains('HEMODIÁLISE', case=False, na=False) & ~df_hemodialise['servico_material'].str.contains('EXTRA', case=False, na=False)]
        sessoes_normais = df_hd_normais.groupby(['nome', 'numero_guia'])['quant'].sum().reset_index()
        sessoes_normais.rename(columns={'quant': 'hd_normais'}, inplace=True)
        df_hd_extras = df_hemodialise[df_hemodialise['servico_material'].str.contains('HEMODIÁLISE', case=False, na=False) & df_hemodialise['servico_material'].str.contains('EXTRA', case=False, na=False)]
        sessoes_extras = df_hd_extras.groupby(['nome', 'numero_guia'])['quant'].sum().reset_index()
        sessoes_extras.rename(columns={'quant': 'hd_extras'}, inplace=True)
        df_sessoes_calculado = pd.merge(sessoes_normais, sessoes_extras, on=['nome', 'numero_guia'], how='outer').fillna(0)
        df_base = df_apac[df_apac['tratamento_procedimento'].str.contains('Hemodiálise', case=False, na=False)].copy()
        df_cdl = df_cateter[(df_cateter['evento'].str.lower() == 'colocação') & (df_cateter['tipo'].str.lower() == 'duplo lumen hd') & (df_cateter['convenio'].str.lower() == 'sus') & (pd.isna(df_cateter['nao_cobra']) | (df_cateter['nao_cobra'] == ''))].copy()
        df_cdl['CDL'] = 'CDL'
        df_cdl = df_cdl[['nome', 'CDL']].drop_duplicates(subset=['nome'])
        def get_sorologia(row):
            sorologias = []
            if 'reag' in str(row['hbsag']).lower(): sorologias.append('HBV')
            if 'reag' in str(row['hep_c']).lower(): sorologias.append('HCV')
            if 'reag' in str(row['hiv']).lower(): sorologias.append('HIV')
            return ', '.join(sorologias)
        df_estatistica['Sorologia'] = df_estatistica.apply(get_sorologia, axis=1)
        df_estatistica_final = df_estatistica[['nome', 'dt_entr', 'Sorologia']].sort_values('dt_entr').drop_duplicates(subset=['nome'], keep='last')
        df_base['n_apac'] = df_base['n_apac'].astype(str)
        df_sessoes_calculado['numero_guia'] = df_sessoes_calculado['numero_guia'].astype(str)
        df_final = pd.merge(df_base[['nome', 'n_apac', 'situacao', 'data_saida']], df_sessoes_calculado, left_on=['nome', 'n_apac'], right_on=['nome', 'numero_guia'], how='left')
        df_final = pd.merge(df_final, df_estatistica_final, on='nome', how='left')
        df_final = pd.merge(df_final, df_cdl, on='nome', how='left')
        def format_saida(row):
            if pd.notna(row['data_saida']):
                situacao = str(row['situacao'])
                if situacao == "Transferência de centro": situacao_abbr = "Transf."
                elif situacao == "Transplante": situacao_abbr = "Transp."
                else: situacao_abbr = situacao
                data_br = row['data_saida'].strftime('%d/%m/%Y')
                return f"{situacao_abbr} {data_br}"
            return ''
        df_final['Saída'] = df_final.apply(format_saida, axis=1)
        df_final['Entrada'] = df_final['dt_entr'].dt.strftime('%d/%m/%Y')
        df_final.rename(columns={'nome': 'Nome', 'n_apac': 'Nº APAC', 'hd_normais': 'HD', 'hd_extras': 'Extras'}, inplace=True)
        final_cols = ['Nome', 'Nº APAC', 'HD', 'Extras', 'CDL', 'Sorologia', 'Entrada', 'Saída']
        df_final = df_final[final_cols]
        for col in ['HD', 'Extras']:
             df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0).astype(int)
        for col in ['CDL', 'Sorologia', 'Entrada', 'Saída']:
            df_final[col] = df_final[col].fillna('')
        return df_final

    def get_remarcacoes_count(self):
        try:
            query = "SELECT SUM(hd_remarcadas) FROM sessoes_hd"
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except sqlite3.Error:
            return 0

    def get_remarcacoes_data(self):
        try:
            query = "SELECT nome, hd_normais, hd_extras, hd_remarcadas FROM sessoes_hd WHERE hd_remarcadas > 0"
            df = pd.read_sql_query(query, self.conn)
            df.rename(columns={'nome': 'Nome','hd_normais': 'HD Normais','hd_extras': 'HD Extras','hd_remarcadas': 'HD Remarcadas'}, inplace=True)
            return df
        except (sqlite3.Error, pd.io.sql.DatabaseError):
            return pd.DataFrame()

    def generate_fistulas_report_data(self):
        try:
            df_eventos = pd.read_sql_query("SELECT * FROM eventos_cateter", self.conn)
            df_apac = pd.read_sql_query("SELECT nome, n_apac FROM laudos_apac", self.conn)
        except pd.io.sql.DatabaseError as e:
            raise ValueError(f"Erro ao ler as tabelas 'eventos_cateter' ou 'laudos_apac': {e}.")

        df_apac_unique = df_apac.drop_duplicates(subset=['nome'], keep='last')

        def classify_procedure(row):
            evento = str(row['evento']).lower()
            tipo = str(row['tipo']).lower()
            acesso = str(row['acesso']).lower()
            convenio = str(row['convenio']).lower()
            nao_cobra_is_empty = pd.isna(row['nao_cobra']) or str(row['nao_cobra']) == ''
            is_billable_sus = (convenio == "sus" and nao_cobra_is_empty)
            if not is_billable_sus: return 'Outro'
            if 'colocação' in evento and 'longa perm. hd' in tipo: return 'Permcath'
            if 'fechamento' in evento and 'autógena' in tipo: return 'Fechamento'
            if 'retirada' in evento and 'cateter' in acesso and 'longa perm. hd' in tipo: return 'Retirada'
            if 'confecção' in evento and 'autógena' in tipo: return 'Fístula'
            if 'confecção' in evento and 'heteróloga' in tipo: return 'Prótese'
            if 'intervenção' in evento: return 'Intervenção'
            return 'Outro'

        df_eventos['Fístula'] = df_eventos.apply(classify_procedure, axis=1)
        df_eventos_filtrado = df_eventos[df_eventos['Fístula'] != 'Outro'].copy()
        df_merged = pd.merge(df_eventos_filtrado, df_apac_unique, on='nome', how='left')
        df_merged.rename(columns={'nome': 'Nome', 'n_apac': 'Nº APAC'}, inplace=True)
        final_cols = ['Nome', 'Nº APAC', 'Fístula']
        df_final = df_merged[final_cols]
        df_final = df_final.sort_values(by=['Fístula', 'Nome'], ascending=True).reset_index(drop=True)
        return df_final

    def generate_continuidade_report_data(self, month, year):
        try:
            df_apac = pd.read_sql_query("SELECT * FROM laudos_apac", self.conn, parse_dates=['final'])
        except pd.io.sql.DatabaseError as e:
            raise ValueError(f"Erro ao ler a tabela 'laudos_apac': {e}.")

        end_of_month = pd.Timestamp(year=year, month=month, day=1).to_period('M').to_timestamp('M').normalize()
        df_base = df_apac[df_apac['tratamento_procedimento'].str.contains('Hemodiálise', case=False, na=False) & (df_apac['final'] > end_of_month)].copy()
        df_base['Final'] = df_base['final'].dt.strftime('%d/%m/%Y')
        df_final = df_base.rename(columns={'nome': 'Nome', 'n_apac': 'Nº APAC'})
        final_cols = ['Nome', 'Nº APAC', 'Final']
        df_final = df_final[final_cols]
        df_final = df_final.sort_values(by='Nome', ascending=True).reset_index(drop=True)
        return df_final

    def _get_raw_convenio_data(self):
        try:
            df = pd.read_sql_query("SELECT * FROM faturamento_convenio", self.conn)
            if df.empty:
                return pd.DataFrame()
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            df['quant'] = pd.to_numeric(df['quant'], errors='coerce').fillna(0)
            df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
            return df
        except (pd.io.sql.DatabaseError, sqlite3.Error) as e:
            raise ValueError(f"Erro ao ler a tabela 'faturamento_convenio': {e}. Verifique se a fonte de dados foi importada.")

    def generate_convenio_geral_data(self):
        df = self._get_raw_convenio_data()
        if df.empty:
            return pd.DataFrame()

        agg_df = df.groupby('numero_guia').agg(
            nome=('nome', 'first'),
            matricula=('matricula', 'first'),
            lote=('lote', 'first'),
            programa_tratamento=('programa_tratamento', 'first'),
            plano=('plano', 'first'),
            quant=('quant', 'sum'),
            total=('total', 'sum'),
            data_inicio=('data', 'min'),
            data_final=('data', 'max')
        ).reset_index()

        agg_df.rename(columns={
            'nome': 'Nome',
            'numero_guia': 'Número da Guia',
            'matricula': 'Matrícula',
            'lote': 'Lote',
            'programa_tratamento': 'Programa Tratamento',
            'plano': 'Plano',
            'quant': 'Quant.',
            'total': 'Total',
            'data_inicio': 'Data Início',
            'data_final': 'Data Final'
        }, inplace=True)

        agg_df = agg_df.sort_values(by='Nome', ascending=True).reset_index(drop=True)
        agg_df['Total'] = agg_df['Total'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        agg_df['Data Início'] = agg_df['Data Início'].dt.strftime('%d/%m/%Y')
        agg_df['Data Final'] = agg_df['Data Final'].dt.strftime('%d/%m/%Y')

        final_columns_order = [
            'Nome', 'Matrícula', 'Número da Guia', 'Lote', 'Quant.',
            'Programa Tratamento', 'Plano', 'Total', 'Data Início', 'Data Final'
        ]

        return agg_df[final_columns_order]

    def calculate_convenio_summary(self):
        df = self._get_raw_convenio_data()
        if df.empty:
            return {}

        qtd_guias = df['numero_guia'].nunique()
        total_sessoes = df['quant'].sum()
        valor_total = df['total'].sum()

        programa_str = df['programa_tratamento'].astype(str).str.upper()
        qtd_hd = df[programa_str.str.contains("HEMODIÁLISE", na=False)]['quant'].sum()
        qtd_hdf = df[programa_str.str.contains("HEMODIAFILTRA", na=False)]['quant'].sum()

        return {
            "Quantidade de Guias": int(qtd_guias),
            "Quantidade Total de Sessões": int(total_sessoes),
            "Quantidade de Sessões HD": int(qtd_hd),
            "Quantidade de Sessões HDF": int(qtd_hdf),
            "Valor Total": f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        }