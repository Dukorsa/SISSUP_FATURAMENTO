# --- INÍCIO DO ARQUIVO COMPLETO E ATUALIZADO: styles.py ---

COLORS = {
    'primary': '#6a2e4d',
    'primary-hover': '#834465',
    'primary-text': '#FFFFFF',
    'dark-primary': '#2d343c',
    'dark-secondary': '#3c4552',
    'dark-text': '#f0f0f0',
    'selection-red': '#c0392b',
    'background-widget': '#f4f6f9',
    'text': '#343a40',
    'text-muted': '#6c757d',
    'border': '#e9ecef',
    'icon-color-light-bg': '#6a2e4d',
    'icon-color-dark-bg': '#FFFFFF',
}

STYLES = f"""
/* --- ESTILO GERAL E TRANSIÇÕES --- */
QWidget {{
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", "Arial", sans-serif;
    color: {COLORS['text']};
}}
#mainContentArea {{
    background-color: {COLORS['background-widget']};
}}
QScrollArea#scrollArea {{
    border: none;
}}
QPushButton, #menuTree::item, #lobbyCard {{
    transition: all 0.2s ease-in-out;
}}

/* --- BARRA SUPERIOR E LATERAL --- */
#topBar, #sidebar {{
    background-color: {COLORS['dark-primary']};
    border: none;
    font-weight: bold;
}}
#moduleTitle {{
    color: {COLORS['dark-text']};
    font-size: 12pt;
    font-weight: 600;
}}
#menuToggleButton {{
    color: {COLORS['dark-text']};
    background-color: {COLORS['dark-secondary']};
    border: none;
    border-radius: 8px;
    padding: 8px;
    min-width: 38px;
    min-height: 38px;
    transition: background-color 0.2s ease-in-out, transform 0.1s ease;
}}
#menuToggleButton:hover {{
    background-color: {COLORS['primary']};
}}
#menuToggleButton:pressed {{
    transform: scale(0.95);
}}
#menuTree {{
    background-color: {COLORS['dark-primary']};
    color: {COLORS['dark-text']};
    font-size: 11pt;
    border: none;
}}
#menuTree::item {{ padding: 10px; border-radius: 5px; }}
#menuTree::item:hover {{
    background-color: {COLORS['dark-secondary']};
}}
#menuTree::item:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['primary-text']};
    font-weight: 600;
}}
#menuTree::branch {{ image: url(none); }}
#quitButton {{
    background-color: {COLORS['dark-secondary']};
    color: {COLORS['dark-text']};
    text-align: left;
    padding: 10px;
    font-weight: 600;
    border: none;
    border-radius: 5px;
}}
#quitButton:hover {{ background-color: {COLORS['primary']}; }}

/* --- PÁGINA DE INÍCIO (LOBBY + RESUMO) --- */
#homeTopContainer {{
    background-color: #ffffff;
    border-bottom: 1px solid {COLORS['border']};
}}
#welcomeTitle {{
    font-size: 18pt;
    font-weight: 700;
    color: {COLORS['text']};
}}
#welcomeText {{
    font-size: 11pt;
    color: {COLORS['text-muted']};
}}
#lobbyTitle {{
    font-size: 14pt;
    font-weight: 600;
    color: {COLORS['primary']};
    margin-bottom: 5px;
}}
#lobbyCard {{
    background-color: #ffffff;
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 25px;
    min-height: 220px;
    max-height: 220px;
    min-width: 280px;
    max-width: 320px;
}}
#lobbyCard:hover {{
    border-color: {COLORS['primary']};
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
}}
#lobbyCardTitle {{
    font-size: 13pt;
    font-weight: 600;
    color: {COLORS['primary']};
}}
#lobbyCardText {{
    font-size: 10pt;
    color: {COLORS['text-muted']};
}}

/* MODIFICADO: Estilo para a assinatura na página inicial */
#signatureWidget {{
    margin-left: 20px;
}}

/* --- TEXTOS E TÍTULOS NO CONTEÚDO (PÁGINA DE RELATÓRIOS) --- */
#sectionHeaderFrame {{
    margin: 15px 0 5px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid {COLORS['border']};
}}
#sectionTitle {{
    font-size: 14pt;
    font-weight: bold;
    color: {COLORS['primary']};
}}
#cardTitle {{
    font-size: 12pt;
    font-weight: bold;
    margin-bottom: 8px;
}}
#infoLabel, QLabel {{
    font-size: 10pt;
    color: {COLORS['text']};
}}
#infoLabel b {{
    color: {COLORS['text']};
    font-weight: 600;
}}
#countLabel {{
    font-size: 11pt;
    font-weight: 600;
    color: {COLORS['text']};
}}

/* --- CARDS E BOTÕES --- */
QFrame#card {{
    background-color: #ffffff;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    min-width: 280px;
    max-width: 310px;
}}
#card QPushButton {{
    font-size: 10pt;
    font-weight: 600;
    padding: 10px 12px;
    border-radius: 6px;
    transition: background-color 0.2s ease-in-out, border-color 0.2s ease-in-out, transform 0.1s ease;
}}
#card QPushButton:pressed {{
    transform: scale(0.97);
}}
#importButton {{
    background-color: {COLORS['primary']};
    color: {COLORS['primary-text']};
    border: 1px solid {COLORS['primary']};
}}
#importButton:hover {{
    background-color: {COLORS['primary-hover']};
    border-color: {COLORS['primary-hover']};
}}
#previewButton, #exportButton {{
    background-color: #ffffff;
    border: 1px solid {COLORS['border']};
}}
#previewButton:hover, #exportButton:hover {{
    border-color: {COLORS['primary']};
    color: {COLORS['primary']};
}}
"""