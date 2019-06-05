#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Luiz Fernando Surian Filho'

import re
import time

from . import controller
from . import keybinds

_quick_enabled = False


def _get_key(key):
    _alias = dict(keybinds.ALIAS)
    if _quick_enabled:
        _alias.update(keybinds.QUICK)
    try:
        return keybinds.VK[key]
    except KeyError:
        bind = _alias[key]
        try:
            return keybinds.VK[bind]
        except TypeError:
            if type(bind) is dict:
                if bind['function'] == 'alt_code':
                    alt_code(bind['value'])
                else:
                    print('undefined')
            else:
                combination(bind)
            return False


def press(keys: list):
    for k in keys:
        key = _get_key(k)
        controller.press_key(key)
        controller.release_key(key)


def combination(keys: list):
    for k in keys:
        controller.press_key(_get_key(k))
    for k in keys:
        controller.release_key(_get_key(k))


def ez_type(string, quick=False):
    global _quick_enabled
    _quick_enabled = quick
    for letter in string:
        if re.match('^[A-Z]*$', letter):
            combination(['LSHIFT', letter])
        elif re.match('^[a-z]*$', letter):
            press([letter.upper()])
        else:
            press([letter])
        time.sleep(0.06)

    _quick_enabled = False


def alt_code(number):
    controller.press_key(_get_key('ALT'))
    keys = []
    for k in str(number):
        keys.append(f'NUMPAD{k}')
    press(keys)
    controller.release_key(_get_key('ALT'))


def normalize_caps_lock():
    if controller.get_caps_lock_state():
        controller.press_key(_get_key('CAPSLOCK'))
        controller.release_key(_get_key('CAPSLOCK'))


def verify_caps_lock():
    return bool(controller.get_caps_lock_state())


def move(x=0, y=0):
    controller.set_pos(x, y)


def click():
    controller.click()


def mouse(x=0, y=0, t=0.2):
    move(x, y)
    click()
    time.sleep(t)
