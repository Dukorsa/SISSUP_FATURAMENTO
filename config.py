def get_table_configs():
    """
    Define as colunas finais a serem salvas no banco de dados para cada tabela.
    """
    # --- Colunas do Módulo SUS (Inalterado) ---
    faturamento_geral_cols = [
        'posicao', 'convenio', 'data', 'cod_prontuario', 'nome', 'matricula',
        'numero_guia', 'senha_autoriz', 'lote', 'data_envio', 'protocolo', 'titulo',
        'data_inc_titulo', 'executante', 'tipo_atendimento', 'servico_material',
        'codigo', 'grupo', 'quant', 'total', 'tipo_guia', 'programa_tratamento', 'tipo_cobranca'
    ]
    
    # AJUSTE: Adiciona a nova coluna 'plano' no final da lista
    faturamento_convenio_cols = [
        'posicao', 'convenio', 'data', 'cod_prontuario', 'nome', 'matricula',
        'numero_guia', 'senha_autoriz', 'lote', 'data_envio', 'protocolo', 'titulo',
        'data_inc_titulo', 'executante', 'tipo', 'servico_material', 'codigo',
        'grupo', 'quant', 'total', 'tipo_guia', 'programa_tratamento', 'tipo_apresentacao', 'plano'
    ]

    return {
        # --- Módulo SUS (Inalterado) ---
        "laudos_apac": {
            'final_columns': ['nome', 'tratamento_procedimento', 'situacao', 'data_saida', 'n_apac', 'final']
        },
        "sessoes_hd": {
            'final_columns': ['nome', 'hd_normais', 'hd_extras', 'hd_remarcadas']
        },
        "estatistica_mensal": {
            'final_columns': ['nome', 'dt_entr', 'hep_c', 'hbsag', 'hiv', 'alta_amb', 'obito']
        },
        "eventos_cateter": {
            'final_columns': ['data', 'acesso', 'nome', 'evento', 'tipo', 'localizacao', 'convenio', 'nao_cobra']
        },
        "faturamento_geral": {
            'final_columns': faturamento_geral_cols
        },
        # AJUSTE: Módulo Convênio agora usa a nova lista de colunas atualizada
        "faturamento_convenio": {
            'final_columns': faturamento_convenio_cols
        }
    }

def get_clean_headers(table_name):
    """
    Define os nomes das colunas esperados para cada arquivo CSV.
    """
    headers = {
        # --- Módulo SUS (Inalterado) ---
        "laudos_apac": ['nome', 'inicio_prog', 'codigo_procedimento', 'tratamento_procedimento', 'situacao', 'data_saida', 'n_apac', 'inicio', 'final', 'solicitante', 'turno', 'cns', 'cpf', 'telefone', 'cidade', 'servico'],
        "sessoes_hd": ['nome', 'convenio', 'hd_normais', 'hd_extras', 'hd_remarcadas', 'falta', 'nao_cobra', 'total_exceto_faltas'],
        "estatistica_mensal": ['num', 'nome', 'dt_nasc', 'sexo', 'cpf', 'cns', 'dt_entr', 'diag', 'cr', 'u_pre', 'u_pos', 'n_s', 'hep_c', 'hbsag', 'hiv', 't_centro', 't_proced', 'txr', 'alta_amb', 'abandono', 'obito'],
        "eventos_cateter": ['data', 'acesso', 'nome', 'evento', 'tipo', 'localizacao', 'convenio', 'nao_cobra', 'data_cobranca', 'medico', 'observacoes', 'programa_na_data', 'programa_ref', 'programa_atual'],
        "faturamento_geral": [
            'posicao', 'convenio', 'data', 'cod_prontuario', 'nome', 'matricula',
            'numero_guia', 'senha_autoriz', 'lote', 'data_envio', 'protocolo', 'titulo',
            'data_inc_titulo', 'executante', 'tipo_atendimento', 'servico_material',
            'codigo', 'grupo', 'quant', 'total', 'tipo_guia', 'programa_tratamento', 'tipo_cobranca'
        ],
        # AJUSTE: Adiciona a nova coluna 'plano' ao final da lista de cabeçalhos
        "faturamento_convenio": [
            'posicao', 'convenio', 'data', 'cod_prontuario', 'nome', 'matricula',
            'numero_guia', 'senha_autoriz', 'lote', 'data_envio', 'protocolo', 'titulo',
            'data_inc_titulo', 'executante', 'tipo', 'servico_material', 'codigo',
            'grupo', 'quant', 'total', 'tipo_guia', 'programa_tratamento', 'tipo_apresentacao', 'plano'
        ]
    }
    return headers.get(table_name, [])

# --- O resto do arquivo permanece INALTERADO ---
REPORT_DEFINITIONS = {
    "Relatório de Fechamento SUS": {
        "imports": ["laudos_apac", "faturamento_geral", "sessoes_hd", "estatistica_mensal", "eventos_cateter"],
        "corrections": ["Remarcações"],
        "exports": ["Geral", "Entrada", "Saída", "Fístulas", "Continuidade"]
    },
    "Relatório de Faturamento Convênio": {
        "imports": ["faturamento_convenio"],
        "corrections": [],
        "exports": ["Geral Convênio"]
    }
}

DATA_SOURCE_TITLES = {
    "laudos_apac": "Laudos de APAC",
    "faturamento_geral": "Faturamento Geral (SUS)",
    "sessoes_hd": "Sessões HD (p/ Remarcações)",
    "estatistica_mensal": "Estatística Mensal",
    "eventos_cateter": "Eventos de Cateter e FAV",
    "faturamento_convenio": "Faturamento Geral (Convênio)"
}

SIDEBAR_CONFIG = [
    {
        "id": "home",
        "text": "Início",
        "icon": "fa5s.home",
        "widget_name": "home_page"
    },
    {
        "id": "reports_group",
        "is_group": True,
        "name": "Relatórios",
        "icon": "fa5s.chart-bar",
        "modules": [
            {
                "id": "report_sus_closing",
                "text": "Fechamento SUS",
                "icon": "fa5s.file-invoice-dollar",
                "widget_name": "relatorio_page",
                "report_name": "Relatório de Fechamento SUS"
            },
            {
                "id": "report_convenio_billing",
                "text": "Faturamento Convênio",
                "icon": "fa5s.hand-holding-usd",
                "widget_name": "relatorio_page",
                "report_name": "Relatório de Faturamento Convênio"
            }
        ]
    },
    {
        "id": "settings",
        "text": "Configurações",
        "icon": "fa5s.cog",
        "widget_name": "settings_page"
    }
]