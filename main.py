#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Password Injector

Esse programa irá gerar senhas aleatórias e/ou inserir senhas em programas automaticamente.
"""
__title__ = 'Password Injector'
__version__ = '0.6.1'
__language__ = 'pt-BR'
__author__ = 'Luiz Fernando Surian Filho'

import os
import random
import string
import sys
import threading
import time
import win32api

import psutil

from graphical_interface import *
from injector import injector


def find_process_id(process_name):
    """Verifica se há processos existentes.

    Procura se há algum processo rodando com o nome "process_name".

    Parâmetros:
    process_name (string): Nome do processo a ser retornado.

    Retorna:
    list: IDs dos processos encontrados.
    """
    process_objects = []
    for process in psutil.process_iter():
        try:
            process_info = process.as_dict(attrs=['pid', 'name', 'create_time'])
            if process_name.lower() in process_info['name'].lower():
                process_objects.append(process_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return process_objects


def resource_path(relative_path):
    """Identifica o caminho dos recursos.

    Procura os arquivos necessários na pasta raiz ou na pasta temporária criada pelo PyInstaller.
    """
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    base_path = getattr(sys, '_MEIPASS', absolute_path)
    return os.path.join(base_path, relative_path)


# Variáveis Globais.
path_default = resource_path('dependencies')
path_images = os.path.join(path_default, 'images')
path_icon = os.path.join(path_images, 'favicon.ico')

wait = time.sleep

chars_upper = string.ascii_uppercase  # A~Z
chars_lower = string.ascii_lowercase  # a~z
chars_numbers = string.digits  # 0~9
chars_special = string.punctuation
chars_special_reduced = "!@#$%&"

chars = {
    "Completo": {
        "description": "Letras, Números e alguns Caracteres Especiais",
        "base": (chars_upper
                 + chars_lower
                 + chars_numbers
                 + chars_special_reduced)
    },
    "Simples": {
        "description": "Letras e Números",
        "base": (chars_upper
                 + chars_lower
                 + chars_numbers)
    },
    "Forte": {
        "description": "Letras, Números e todos Caracteres Especiais",
        "base": (chars_upper
                 + chars_lower
                 + chars_numbers
                 + chars_special)
    },
}

# msdn.microsoft.com/en-us/library/dd375731
trigger_keys = {
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
    "INSERT": 0x2D,
    "SHIFT Esquerdo": 0xA0,
    "SHIFT Direito": 0xA1,
    "CTRL Esquerdo": 0xA2,
    "CTRL Direito": 0xA3,
    "ALT Esquerdo": 0xA4,
    "ALT Direito": 0xA5,
}


class MainWindow(QtWidgets.QMainWindow):
    """Janela principal"""

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap(path_icon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(self.icon)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Password Generator.
        for pass_type in chars:
            self.ui.combo_passtype.addItem(
                f'{pass_type} ({chars[pass_type]["description"]})',
                chars[pass_type]["base"])
        self.ui.btn_generate.clicked.connect(self.generate_password)
        # Password Injector.
        for key, value in trigger_keys.items():
            self.ui.combo_trigger.addItem(key, value)
        self.trigger = 0x77  # Padrão: 0x77 (F8).
        self.ui.combo_trigger.setCurrentIndex(7)
        self.ui.combo_trigger.currentIndexChanged.connect(self.change_trigger)
        self.trigger_thread = None
        self.stop_event = None
        self.my_id = os.getpid()
        self.start_process()

    @QtCore.pyqtSlot(list, name='msg_box')
    def msg_box(self, text):
        alert = QtWidgets.QMessageBox()
        alert.setWindowIcon(self.icon)
        alert.setIcon(QtWidgets.QMessageBox.Warning)
        alert.setWindowTitle(__title__)
        # Insere os textos.
        alert.setText(text[0])
        alert.setInformativeText(text[1])
        # Habilita "Sempre no Topo".
        alert.setWindowFlags(alert.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        # Posiciona em cima da janela principal.
        alert.move(self.x() + 50, self.y() + 50)
        # Mostra a janela de diálogo.
        alert.exec()

    def verify_caps_lock(self):
        if injector.verify_caps_lock():
            text = ['<b>Atenção!</b> O <i>Caps Lock</i> está ativo!',
                    'Isso compromete a digitação automática, favor desligá-lo e tentar novamente.']
            QtCore.QMetaObject.invokeMethod(
                self, 'msg_box', QtCore.Qt.BlockingQueuedConnection, QtCore.Q_ARG(list, text))
            return False
        else:
            return True

    def generate_password(self):
        """Preencher automaticamente.

        Essa função gera uma senha aleatória e alimenta o campo "txt_pass" com essa string.
        É invocada pelo botão "btn_generate" [Gerar Senha].
        """
        chars_quantity = self.ui.nb_chars.value()
        pass_index = self.ui.combo_passtype.currentIndex()
        pass_type = self.ui.combo_passtype.itemData(pass_index)
        password = ''.join(random.choice(pass_type) for _ in range(chars_quantity))
        self.ui.txt_pass.setText(password)

    def change_trigger(self):
        """Altera o botão que ativa o Payload."""
        trigger_index = self.ui.combo_trigger.currentIndex()
        self.trigger = self.ui.combo_trigger.itemData(trigger_index)

    def trigger_event_listener(self, stop_event):
        """Aguarda ação do usuário.

        Essa função é um loop que fica aguardando um botão ser pressionado, determinado pela variável "self.trigger".
        Quando positivo, invoca a função "injector.ez_type()" com a senha que será digitada.
        Para não travar a GUI, o loop é efetuado em um processo separado
        da aplicação principal, usando "threading.Event()".
        """
        key_state = win32api.GetKeyState
        first_state = key_state(self.trigger)
        state = True
        while state and not stop_event.isSet():
            check = key_state(self.trigger)
            # Verifica se o botão foi pressionado.
            if check != first_state:
                first_state = check
                # Solto = 0 ou 1; Pressionado = -127 ou -128.
                if check < 0:
                    password = self.ui.txt_pass.text()
                    if len(password) > 0 and self.verify_caps_lock():
                        wait(1.2)
                        injector.ez_type(password)
            time.sleep(0.01)

    def start_process(self):
        """Iniciar processo.

        Essa função verifica se já existem processos rodando além deste e
        os finaliza para não permitir multiplas execuções.
        Depois inicia a Thread que monitora a ação do usuário pela função "trigger_event_listener()".
        """
        list_process_id = find_process_id("password_injector")
        if len(list_process_id) > 0:
            for element in list_process_id:
                p_id = element["pid"]
                if p_id != self.my_id:
                    # Finaliza todos os processos com o mesmo nome, exceto ele mesmo.
                    psutil.Process(p_id).kill()
        # Aguarda o término da ação anterior.
        wait(0.01)
        # Observa a tecla escolhida para executar o Payload.
        self.stop_event = threading.Event()
        self.trigger_thread = threading.Thread(target=self.trigger_event_listener, args=(self.stop_event,))
        self.trigger_thread.start()

    def closeEvent(self, event):
        """Handle do botão de fechar.

        Quando o programa é finalizado, encerra todos os processos relacionados.
        """
        self.stop_event.set()
        psutil.Process(self.my_id).kill()
        event.accept()


if __name__ == '__main__':
    """Inicia a GUI."""
    app = QtWidgets.QApplication([])
    application = MainWindow()
    application.show()
    sys.exit(app.exec())
