import torch
import os
from . import utils
# from cached_path import cached_path
DOWNLOAD_CKPT_URLS = {
    'EN': 'models/EN/checkpoint.pth',
    'EN_V2': 'models/EN_V2/checkpoint.pth',
    'FR': 'models/FR/checkpoint.pth',
    'JP': 'models/JP/checkpoint.pth',
    'ES': 'models/ES/checkpoint.pth',
    'ZH': 'models/ZH/checkpoint.pth',
    'KR': 'models/KR/checkpoint.pth',
}

DOWNLOAD_CONFIG_URLS = {
    'EN': 'models/EN/config.json',
    'EN_V2': 'models/EN_V2/config.json',
    'FR': 'models/FR/config.json',
    'JP': 'models/JP/config.json',
    'ES': 'models/ES/config.json',
    'ZH': 'models/ZH/config.json',
    'KR': 'models/KR/config.json',
}

import sys
if getattr(sys, 'frozen', False):
    # 打包成 exe
    current_file_path = os.path.dirname(sys.executable)
else:
    current_file_path = './'

def load_or_download_config(locale):
    language = locale.split('-')[0].upper()
    assert language in DOWNLOAD_CONFIG_URLS
    config_path = os.path.join(current_file_path, DOWNLOAD_CONFIG_URLS[language])
    return utils.get_hparams_from_file(config_path)

def load_or_download_model(locale, device):
    language = locale.split('-')[0].upper()
    assert language in DOWNLOAD_CKPT_URLS
    ckpt_path = os.path.join(current_file_path, DOWNLOAD_CKPT_URLS[language])
    return torch.load(ckpt_path, map_location=device)
