import configparser

from pdw import __version__

CURRENT_VERSION = __version__


def load_config(param_file):
    """
    Lê e valida o arquivo de configuração .cfg.

    Args:
        param_file (str): Caminho alternativo para o arquivo de configuração.
                          Se vazio, usa 'PersonalDataWareHouse.cfg'.

    Returns:
        dict: Dicionário com todos os parâmetros de configuração.
              Encerra o processo com exit(1) em caso de erro.
    """
    config = configparser.ConfigParser()
    config_file = 'PersonalDataWareHouse.cfg'

    if len(param_file) > 0:
        config_file = param_file

    try:
        print('Reading configuration file ... .. .')
        with open(config_file) as cfg:
            config.read_file(cfg)

        parameters_version = config['SETTINGS']['CURRENT_VERSION']
        if parameters_version != CURRENT_VERSION:
            print(f'The version in parameter file {config_file} does not Match')
            print(f'Informed :-> {parameters_version}')
            print(f'Expected :-> {CURRENT_VERSION}')
            exit(1)

        dir_log = config['DIRECTORIES']['LOG_DIR']

        cfg_values = {
            'current_version': CURRENT_VERSION,
            'config_file': config_file,
            'dir_file_in': config['DIRECTORIES']['DIR_IN'],
            'dir_file_out': config['DIRECTORIES']['DIR_OUT'],
            'dir_log': dir_log,
            'dir_db': config['DIRECTORIES']['DATABASE_DIR'],
            'in_file': config['FILE_TYPES']['INPUT_FILE'],
            'in_type': config['FILE_TYPES']['TYPE_IN'],
            'out_type': config['FILE_TYPES']['TYPE_OUT'],
            'out_db': config['FILE_TYPES']['OUT_DB_FILE'],
            'output_name': config['FILE_TYPES']['OUT_RPT_FILE'],
            'db_file_type': config['FILE_TYPES']['DB_FILE_TYPE'],
            'log_file_cfg': dir_log + config['FILE_TYPES']['LOG_FILE'],
            # splitter = config.getint('SETTINGS', 'PARALLELS')
            'multithread': config.getboolean('SETTINGS', 'MULTITHREADING'),
            'overwrite_db': config.getboolean('SETTINGS', 'OVERWRITE_DB'),
            'run_loader': config.getboolean('SETTINGS', 'RUN_DATA_LOADER'),
            'run_reports': config.getboolean('SETTINGS', 'RUN_REPORTS'),
            'multi_rept_file': config.getboolean('SETTINGS', 'RPT_SINGLE_FILE'),
            'guiding_table': config['SETTINGS']['GUIDING_TABLE'],
            'types_of_entries': config['SETTINGS']['TYPES_OF_ENTRIES'],
            'general_entries_table': config['SETTINGS']['GENERAL_ENTRIES_TABLE'],
            'create_pivot': config.getboolean('SETTINGS', 'CREATE_PIVOT'),
            'save_discarted_data': config.getboolean('SETTINGS', 'SAVE_DISCARTED_DATA'),
            'discarted_data_table': config['SETTINGS']['DISCARTED_DATA_TABLE'],
            'full_hist_table': config['SETTINGS']['FULL_PIVOT_TABLE'],
            'anual_hist_table': config['SETTINGS']['ANUAL_PIVOT_TABLE'],
            # export_transeient_data = config.getboolean('SETTINGS','EXPORT_TRANSIENT_DATA')
            # transient_data_table = config['SETTINGS']['TRANSIENT_DATA_TABLE']
            # transient_data_file = config['FILE_TYPES']['TRANSIENT_DATA_FILE']
            'origem_dados': config['SETTINGS']['TRANSIENT_DATA_COLUMN'],
            'other_file_types': config.getboolean('SETTINGS', 'EXPORT_OTHER_TYPES'),
            'dinamic_reports': config.getboolean('SETTINGS', 'RUN_DINAMIC_REPORT'),
            'din_report_guinding': config['SETTINGS']['DIN_REPORT_GUIDING'],
            'dayly_progress': config['SETTINGS']['DAYLY_PROGRESS'],
            'split_paymnt_table': config['SETTINGS']['SPLT_PAYMNT_TAB'],
            'out_table': config['SETTINGS']['OUT_RES_PMNT_TAB'],
            'monthly_summarie': config['SETTINGS']['MONTHLY_SUMMATIES'],
            'queries_file': config['SETTINGS']['YAML_SQL_FILE'],
            # NOVO02 = config.getboolean('settings', 'SelfDestruction')
        }
        return cfg_values

    except FileNotFoundError:
        print(f"Configuration file {config_file} not found !")
        exit(1)
    except configparser.Error as e:
        print(e)
        exit(1)
    except Exception as e:
        print(e)
        exit(1)
