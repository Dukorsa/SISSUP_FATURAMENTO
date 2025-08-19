import sys
import os

def resource_path(relative_path):
    """ Retorna o caminho absoluto para um recurso, funcionando tanto em
        desenvolvimento quanto no executável do PyInstaller. """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Se não estiver empacotado, o caminho base é o diretório do projeto
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)