import os
import datetime


def open_log(log_file_cfg):
    """
    Abre ou cria o arquivo de log.

    Returns:
        tuple: (log_file_handle, number_of_runs, last_run_date)
    """
    # begin of log block
    last_run_date = 'none'
    log_file_exists = os.path.isfile(log_file_cfg)
    is_log_empty = False
    if log_file_exists:
        is_log_empty = os.stat(log_file_cfg).st_size == 0
        if is_log_empty:
            print(f'Log File {log_file_cfg} is Empty ')
    else:
        print(f'Log File {log_file_cfg} does Not Exists yet ')
        new_log_file = open(log_file_cfg, 'w')
        new_log_file.write('New LOG created at :-> ' + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n')
        new_log_file.close()

    log_file = open(log_file_cfg, 'r+')
    number_of_runs = 0
    if not is_log_empty and log_file_exists:
        number_of_runs = sum(1 for _ in log_file)
        log_file.seek(0)
        last_run_date = log_file.readlines()[-1].split('|')[0]
    # end of LOG block
    return log_file, number_of_runs, last_run_date


def finalize_log(log_file, log_line):
    """Escreve a linha final de log e fecha o arquivo."""
    log_file.write(log_line)
    log_file.close()
