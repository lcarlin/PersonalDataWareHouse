import gzip
import shutil
import os


def gzip_compressor(arquivo_origem):
    arquivo_destino = arquivo_origem + '.gz'
    print(f'creating compressed file {arquivo_destino}')
    with open(arquivo_origem, 'rb') as f_in:
        with gzip.open(arquivo_destino, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Excluindo o arquivo original após a compactação
    os.remove(arquivo_origem)