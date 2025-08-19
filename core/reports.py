import pandas as pd
from abc import ABC, abstractmethod
from core.database import Database
from core.utils import resource_path
from reportlab.lib.pagesizes import letter, landscape
from core.exporter import (
    export_to_excel, export_simple_excel, export_fistulas_to_excel,
    export_to_pdf, export_fistulas_to_pdf, export_continuidade_to_pdf
)

class BaseReport(ABC):

    def __init__(self, db: Database, logo_path: str, **kwargs):
        self.db = db
        self.default_logo_path = logo_path
        self.params = kwargs

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def sheet_name(self) -> str:
        pass

    @abstractmethod
    def get_data(self) -> pd.DataFrame:
        pass

    def get_summary(self, df: pd.DataFrame) -> dict:
        return {}

    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def export(self, file_path: str, file_format: str):
        df_raw = self.get_data()
        df_final = self.filter_dataframe(df_raw)

        if df_final.empty:
            raise ValueError(f"Não foram encontrados dados para o relatório '{self.title}'.")

        summary = self.get_summary(df_final)

        for col in ['HD', 'Extras']:
            if col in df_final.columns:
                df_final[col] = df_final[col].astype(object)
                df_final.loc[df_final[col] == 0, col] = ''

        clinic_name = self.params.get('clinic', '')
        logo_file_map = {
            "Renal Clínica": "logo_renal_clinica.png",
            "Instituto do Rim": "logo_instituto_rim.png",
            "Nefron Clínica": "logo_nefron_clinica.png",
            "CNN": "logo_cnn.png",
            "Pronto Rim": "logo_pronto_rim.png",
            "Clínica do Rim": "logo_clinica_do_rim.png",
            "Hospital do Rim": "logo_hospital_do_rim.png",
        }
        logo_filename = logo_file_map.get(clinic_name, 'logo.png')
        logo_to_use = resource_path(f'assets/{logo_filename}')

        col_widths = None
        if isinstance(self, EntradaReport):
            col_widths = ['28%', '15%', '7%', '9%', '9%', '10%', '22%']
        elif isinstance(self, SaidaReport):
            col_widths = ['28%', '15%', '7%', '8%', '7%', '12%', '23%']
        elif isinstance(self, GeralReport):
            col_widths = ['30%', '20%', '7%', '10%', '7%', '26%']

        if file_format.lower() == 'excel':
            export_to_excel(df_final, file_path, self.sheet_name, summary)
        elif file_format.lower() == 'pdf':
            export_to_pdf(df_final, file_path, logo_to_use, self.title, summary, pagesize=letter, col_widths=col_widths)
        else:
            raise NotImplementedError(f"Formato de arquivo '{file_format}' não suportado.")

class GeralReport(BaseReport):
    @property
    def title(self) -> str:
        month = self.params.get('month', 0)
        year = self.params.get('year', 0)
        clinic = self.params.get('clinic', 'Clínica')
        return f"Geral - {clinic} - {month:02d}.{year}"

    sheet_name = "Geral"

    def get_data(self) -> pd.DataFrame:
        return self.db.generate_geral_report_data()

    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        month = self.params.get('month')
        year = self.params.get('year')

        df_filtered = df[df['Saída'].str.strip() == ''].copy()
        df_filtered['Entrada_dt'] = pd.to_datetime(df_filtered['Entrada'], format='%d/%m/%Y', errors='coerce')

        df_row_filtered = df_filtered[
            ~(
                (df_filtered['Entrada_dt'].dt.month == month) &
                (df_filtered['Entrada_dt'].dt.year == year)
            )
        ].copy()

        df_row_filtered['Observação'] = df_row_filtered['Sorologia']

        final_cols = ['Nome', 'Nº APAC', 'HD', 'Extras', 'CDL', 'Observação']
        df_final = df_row_filtered[final_cols]

        return df_final

    def get_summary(self, df: pd.DataFrame) -> dict:
        hd_sessions = pd.to_numeric(df['HD'], errors='coerce').sum()
        extra_sessions = pd.to_numeric(df['Extras'], errors='coerce').sum()

        summary = {
            "Pacientes na Listagem": len(df),
            'Sessões Totais': int(hd_sessions + extra_sessions),
            'Sessões HD': int(hd_sessions),
            'Sessões Extras': int(extra_sessions),
            'Colocações de CDL': int(df['CDL'].str.strip().ne('').sum()),
        }

        sorologia_col = df['Observação']
        summary['Total HBV'] = int(sorologia_col.str.contains('HBV', na=False).sum())
        summary['Total HCV'] = int(sorologia_col.str.contains('HCV', na=False).sum())
        summary['Total HIV'] = int(sorologia_col.str.contains('HIV', na=False).sum())

        return summary

class SaidaReport(GeralReport):
    @property
    def title(self) -> str:
        month = self.params.get('month', 0)
        year = self.params.get('year', 0)
        clinic = self.params.get('clinic', 'Clínica')
        return f"Saídas - {clinic} - {month:02d}.{year}"

    sheet_name = "Saídas"

    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_filtered = df[df['Saída'].str.strip() != ''].copy()
        df_filtered['Observação'] = df_filtered['Sorologia']
        final_cols = ['Nome', 'Nº APAC', 'HD', 'Extras', 'CDL', 'Saída', 'Observação']
        df_final = df_filtered[final_cols]
        return df_final

class EntradaReport(GeralReport):
    @property
    def title(self) -> str:
        month = self.params.get('month', 0)
        year = self.params.get('year', 0)
        clinic = self.params.get('clinic', 'Clínica')
        return f"Entradas - {clinic} - {month:02d}.{year}"

    sheet_name = "Entradas"

    def filter_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        month = self.params.get('month')
        year = self.params.get('year')

        df['Entrada_dt'] = pd.to_datetime(df['Entrada'], format='%d/%m/%Y', errors='coerce')
        df_filtered = df[
            (df['Entrada_dt'].dt.month == month) &
            (df['Entrada_dt'].dt.year == year) &
            (df['Saída'].str.strip() == '')
        ].copy()

        df_filtered['Observação'] = df_filtered['Sorologia']

        final_cols = ['Nome', 'Nº APAC', 'HD', 'Extras', 'CDL', 'Entrada', 'Observação']
        df_final = df_filtered[final_cols]

        return df_final

    def get_summary(self, df: pd.DataFrame) -> dict:
        hd_sessions = pd.to_numeric(df['HD'], errors='coerce').sum()
        extra_sessions = pd.to_numeric(df['Extras'], errors='coerce').sum()

        summary = {
            "Total de Pacientes na Listagem": len(df),
            'Total de Sessões HD': int(hd_sessions),
            'Total de Sessões Extras': int(extra_sessions),
            'Total de Sessões (HD + Extras)': int(hd_sessions + extra_sessions),
            'Total de Colocações de CDL (SUS)': int(df['CDL'].str.strip().ne('').sum()),
        }
        
        sorologia_col = df['Observação']
        summary['Total HBV'] = int(sorologia_col.str.contains('HBV', na=False).sum())
        summary['Total HCV'] = int(sorologia_col.str.contains('HCV', na=False).sum())
        summary['Total HIV'] = int(sorologia_col.str.contains('HIV', na=False).sum())

        return summary

class FistulasReport(BaseReport):
    @property
    def title(self) -> str:
        clinic = self.params.get('clinic', 'Clínica')
        return f"Fístulas - {clinic}"

    sheet_name = "Procedimentos FAV"

    def get_data(self) -> pd.DataFrame:
        return self.db.generate_fistulas_report_data()

    def get_summary(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        counts = df['Fístula'].value_counts().to_dict()
        summary = {"Total Geral de Procedimentos": len(df)}
        for procedure, count in counts.items():
            summary[f"Total de {procedure}"] = count
        return summary

    def export(self, file_path: str, file_format: str):
        df = self.get_data()
        if df.empty:
            raise ValueError(f"Não foram encontrados dados para o relatório '{self.title}'.")
        summary = self.get_summary(df)

        clinic_name = self.params.get('clinic', '')
        logo_file_map = {
            "Renal Clínica": "logo_renal_clinica.png",
            "Instituto do Rim": "logo_instituto_rim.png",
            "Nefron Clínica": "logo_nefron_clinica.png",
            "CNN": "logo_cnn.png",
            "Pronto Rim": "logo_pronto_rim.png",
            "Clínica do Rim": "logo_clinica_do_rim.png",
            "Hospital do Rim": "logo_hospital_do_rim.png",
        }
        logo_filename = logo_file_map.get(clinic_name, 'logo.png')
        logo_to_use = resource_path(f'assets/{logo_filename}')

        if file_format.lower() == 'excel':
            export_fistulas_to_excel(df, file_path, totals=summary)
        elif file_format.lower() == 'pdf':
            export_fistulas_to_pdf(df, file_path, logo_to_use, totals=summary)

class ContinuidadeReport(BaseReport):
    @property
    def title(self) -> str:
        month = self.params.get('month', 0)
        year = self.params.get('year', 0)
        clinic = self.params.get('clinic', 'Clínica')
        return f"Continuidade - {clinic} - {month:02d}.{year}"

    sheet_name = "Continuidade"

    def get_data(self) -> pd.DataFrame:
        month = self.params.get('month')
        year = self.params.get('year')
        return self.db.generate_continuidade_report_data(month, year)

    def export(self, file_path: str, file_format: str):
        df = self.get_data()
        if df.empty:
            raise ValueError(f"Não foram encontrados dados para o relatório '{self.title}'.")

        clinic_name = self.params.get('clinic', '')
        logo_file_map = {
            "Renal Clínica": "logo_renal_clinica.png",
            "Instituto do Rim": "logo_instituto_rim.png",
            "Nefron Clínica": "logo_nefron_clinica.png",
            "CNN": "logo_cnn.png",
            "Pronto Rim": "logo_pronto_rim.png",
            "Clínica do Rim": "logo_clinica_do_rim.png",
            "Hospital do Rim": "logo_hospital_do_rim.png",
        }
        logo_filename = logo_file_map.get(clinic_name, 'logo.png')
        logo_to_use = resource_path(f'assets/{logo_filename}')

        if file_format.lower() == 'excel':
            export_simple_excel(df, file_path, sheet_name=self.sheet_name)
        elif file_format.lower() == 'pdf':
            export_continuidade_to_pdf(df, file_path, logo_to_use, self.title)

class ConvenioGeralReport(BaseReport):
    title = "Relatório Geral de Faturamento Convênio"
    sheet_name = "Geral Convenio"

    def get_data(self) -> pd.DataFrame:
        return self.db.generate_convenio_geral_data()

    def get_summary(self, df: pd.DataFrame) -> dict:
        return self.db.calculate_convenio_summary()

    def export(self, file_path: str, file_format: str):
        df_display = self.get_data()
        if df_display.empty:
            raise ValueError(f"Não foram encontrados dados para o relatório '{self.title}'.")
        summary = self.get_summary(df_display)
        if file_format.lower() == 'excel':
            export_to_excel(df_display, file_path, self.sheet_name, totals=summary)
        elif file_format.lower() == 'pdf':
            export_to_pdf(df_display, file_path, self.default_logo_path, self.title, summary, pagesize=landscape(letter))
        else:
            raise NotImplementedError(f"Formato de arquivo '{file_format}' não suportado.")

REPORT_REGISTRY = {
    "Geral": GeralReport,
    "Entrada": EntradaReport,
    "Saída": SaidaReport,
    "Fístulas": FistulasReport,
    "Continuidade": ContinuidadeReport,
    "Geral Convênio": ConvenioGeralReport,
}