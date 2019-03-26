#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Password Injector

Esse programa irá gerar senha aleatórias
e/ou inserir senhas em programas automaticamente.
"""
__title__ = 'Password Injector'
__status__ = 'Development'
__version__ = '1.0'
__language__ = 'pt-BR'
__author__ = 'Luiz Fernando Surian Filho'


import os
import sys
import time
import psutil
import random
import win32api
import threading

from pywinauto.keyboard import SendKeys as send_keys

from graphical_interface import *


def default_exception_hook(hook_type, hook_value, traceback):
    """Retorna o tratamento padrão de Exceptions.

    PyQT5 altera o funcionamento das Exceptions para fechar a UI ao dar erro,
    durante o desenvolvimento essa função é utilizada
    para visualizar o Traceback normalmente e facilitar o debug.
    """
    sys.__excepthook__(hook_type, hook_value, traceback)


if __status__ != 'Production':
    sys.excepthook = default_exception_hook


def resource_path(relative_path):
    """Identifica o caminho dos recursos.

    Procura os arquivos necessários na pasta raiz ou na
    pasta temporária criada pelo PyInstaller.
    """
    base_path = getattr(
        sys, '_MEIPASS',
        os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(base_path, relative_path)


# Variáveis Globais.
wait = time.sleep
path_default = resource_path('dependencies')

chars = {
    "Completo": {
        "description": "Letras, Números e Caracteres Especiais",
        "base": ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                 "abcdefghijklmnopqrstuvwxyz"
                 "0123456789"
                 "!@#$%&"
                 )
    },
    "Simples": {
        "description": "Letras e Números",
        "base": ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                 "abcdefghijklmnopqrstuvwxyz"
                 "0123456789"
                 )
    }
}


class MainWindow(QtWidgets.QMainWindow):
    """Janela principal"""
    def __init__(self):
        super(MainWindow, self).__init__()
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(os.path.join(path_default, 'favicon.ico')),
            QtGui.QIcon.Normal, QtGui.QIcon.Off
        )
        self.setWindowIcon(icon)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        for pass_type in chars:
            self.ui.combo_passtype.addItem(
                f'{pass_type} ({chars[pass_type]["description"]})',
                chars[pass_type]["base"]
            )

        self.ui.btn_generate.clicked.connect(self.generate_password)
        self.watch_user()

    def _random_generator(self, char_base='', size=12):
        """Gerar senha aleatória

        Essa função recebe uma lista de caracteres e um número
        de quantas vezes será necessário escolher aleatóriamente um
        caracter dessa lista para formar uma string.

        Parâmetros:
        char_base (string): Quais caracteres serão usados
            para a geração da senha.
        size (int): Define o tamanho da senha.

        Retorna:
        string: Senha aleatória de acordo com os parâmetros definidos.
        """
        return ''.join(random.choice(char_base) for _ in range(size))

    def _escape_chars(self, text):
        """Escapa caracteres.

        Essa função serve para escapar todos os caracteres enviados
        à função "send_keys()" para evitar que caracteres especiais
        sejam interpretados como comandos.

        Parâmetros:
        text (string): Recebe o texto da senha a ser injetada.

        Retorna:
        string: Retorna o texto original escapado com "{}".
            exemplo:
             - Recebe: "teste"
             - Retorna: "{t}{e}{s}{t}{e}"
        """
        password = ''
        for letter in text:
            password += '{' + letter + '}'
        return password

    def _event_listener(self, stop_event):
        """Aguarda clique do usuário.

        Essa função é um loop que fica aguardando
        o botão "F8" ser pressionado.
        Quando positivo, invoca a função "send_keys()"
        com a senha que será digitada.

        Para não travar a GUI, o loop é efetuado em
        um processo separado da aplicação principal,
        usando "threading.Event()".
        """
        # Botão F8 (0x77). Solto = 0 or 1. Pressionado = -127 or -128.
        mouse_state = win32api.GetKeyState(0x77)
        state = True
        while state and not stop_event.isSet():
            check = win32api.GetKeyState(0x77)
            # Verifica se o botão foi pressionado.
            if check != mouse_state:
                mouse_state = check
                if check < 0:
                    password = self.ui.txt_pass.text()
                    if len(password) > 0:
                        password = self._escape_chars(text=password)
                        wait(1)
                        send_keys(password, with_spaces=True)
                        # self.stop_event.set()
            time.sleep(0.001)

    def generate_password(self):
        """Preencher automaticamente.

        Essa função invoca "_random_generator()" para gerar uma senha
        aleatória e alimenta o campo "txt_pass" com essa string.

        É invocada pelo botão "btn_generate" [Gerar Senha].
        """
        chars_quantity = self.ui.nb_chars.value()
        pass_type = self.ui.combo_passtype.itemData(
            self.ui.combo_passtype.currentIndex())
        password = self._random_generator(
            char_base=pass_type, size=chars_quantity)
        self.ui.txt_pass.setText(password)

    def watch_user(self):
        """Iniciar Injeção.

        Essa função verifica se há uma senha em "txt_pass",
        se houver, invoca "_event_listener()" para aguardar
        o clique do usuário, e após, digitar essa senha.

        É invocada pelo botão "btn_run" [Iniciar].
        """
        self.stop_event = threading.Event()
        self.c_thread = threading.Thread(
            target=self._event_listener, args=(self.stop_event,))
        self.c_thread.start()


def kill_proc_tree(pid, including_parent=True):
    """Mata todos os processos dessa aplicação"""
    parent = psutil.Process(pid)
    if including_parent:
        parent.kill()


def main():
    """Inicia a GUI."""
    app = QtWidgets.QApplication([])
    application = MainWindow()
    application.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
    # Quando o programa é finalizado,
    # encerra todos os processos relacionados.
    me = os.getpid()
    kill_proc_tree(me)
