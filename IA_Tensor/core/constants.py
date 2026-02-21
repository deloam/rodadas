"""
Constantes e variáveis globais do sistema.
Centraliza as regras matemáticas da Lotofácil para evitar repetição de código.
"""

# Regras Matemáticas Base
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
FIBONACCI = {1, 2, 3, 5, 8, 13, 21}

# Parâmetros de Equilíbrio
METAS_EQUILIBRIO = {
    'Impares': {'ideal': 8.0, 'min': 7, 'max': 9},
    'Primos': {'ideal': 5.0, 'min': 4, 'max': 6},
    'Moldura': {'ideal': 10.0, 'min': 9, 'max': 11},
    'Fibo': {'ideal': 4.0, 'min': 3, 'max': 5},
    'Soma': {'ideal': 200.0, 'min': 180, 'max': 220},
    'Repetentes': {'ideal': 9.0, 'min': 8, 'max': 10}
}
