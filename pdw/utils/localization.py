# ============================================================================
# FUNÇÕES AUXILIARES - DICIONÁRIOS E CONSTANTES
# ============================================================================

def get_month_names():
    """
    Retorna dicionário com nomes dos meses em português.

    Returns:
        dict: Mapeamento de número do mês para nome formatado
    """
    return {
        1: "01-Janeiro",
        2: "02-Fevereiro",
        3: "03-Março",
        4: "04-Abril",
        5: "05-Maio",
        6: "06-Junho",
        7: "07-Julho",
        8: "08-Agosto",
        9: "09-Setembro",
        10: "10-Outubro",
        11: "11-Novembro",
        12: "12-Dezembro"
    }

def get_weekday_names():
    """
    Retorna dicionário com nomes dos dias da semana em português.

    Returns:
        dict: Mapeamento de número do dia para nome
    """
    return {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }
