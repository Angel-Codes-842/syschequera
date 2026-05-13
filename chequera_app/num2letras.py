"""
Módulo de conversión de números a letras en guaraní.
Convierte importes enteros a su representación en palabras.
"""


def numero_a_letras(numero: int) -> str:
    """
    Convierte un número entero a su representación en letras en guaraní.
    
    Args:
        numero: Número entero a convertir (0 a 9,999,999,999)
    
    Returns:
        String con el número en letras, en mayúsculas, terminado con "GUARANÍES"
    
    Ejemplos:
        1 -> "UN GUARANÍ"
        125000 -> "CIENTO VEINTICINCO MIL GUARANÍES"
        1000000 -> "UN MILLÓN DE GUARANÍES"
        1000000000 -> "UN MIL MILLONES DE GUARANÍES"
    """
    
    if numero == 0:
        return "CERO GUARANÍES"
    
    # Validación (Hasta 9.999.999.999)
    if numero < 0 or numero > 9999999999:
        raise ValueError(f"Número fuera de rango: {numero}")
    
    unidades = [
        "", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", 
        "SIETE", "OCHO", "NUEVE"
    ]
    
    decenas = [
        "", "", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
        "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"
    ]
    
    especiales = {
        10: "DIEZ",
        11: "ONCE",
        12: "DOCE",
        13: "TRECE",
        14: "CATORCE",
        15: "QUINCE",
        16: "DIECISÉIS",
        17: "DIECISIETE",
        18: "DIECIOCHO",
        19: "DIECINUEVE",
        21: "VEINTIUNO",
        22: "VEINTIDÓS",
        23: "VEINTITRÉS",
        24: "VEINTICUATRO",
        25: "VEINTICINCO",
        26: "VEINTISÉIS",
        27: "VEINTISIETE",
        28: "VEINTIOCHO",
        29: "VEINTINUEVE"
    }
    
    centenas = [
        "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
        "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"
    ]
    
    def convertir_hasta_mil(n, es_final=False):
        """Convierte números de 0 a 999.
        es_final: True si es el último grupo (después de mil/millón), para usar UNO en lugar de UN.
        """
        if n == 0:
            return ""
        
        partes = []
        
        # Centenas
        c = n // 100
        if c > 0:
            if c == 1 and (n % 100 == 0):
                partes.append("CIEN")
            else:
                partes.append(centenas[c])
        
        # Decenas y unidades
        resto = n % 100
        if resto in especiales:
            # Para 21-29 usar la forma especial
            partes.append(especiales[resto])
        elif resto >= 30:
            d = resto // 10
            u = resto % 10
            if u == 0:
                partes.append(decenas[d])
            else:
                partes.append(decenas[d] + " Y " + unidades[u])
        elif resto >= 20:
            # El 20 está aquí, 21-29 están en especiales
            partes.append(decenas[resto // 10])
        elif resto > 0:
            # Si es final (después de mil/millón) o hay centenas antes, usar UNO; si no, usar UN
            if es_final and resto == 1:
                partes.append("UNO")
            elif c > 0 and resto == 1:
                partes.append("UNO")
            else:
                partes.append(unidades[resto])
        
        return " ".join(partes)
    
    # Desglose del número
    mil_millones = numero // 1000000000
    resto_mil_millones = numero % 1000000000
    
    millones = resto_mil_millones // 1000000
    resto_millones = resto_mil_millones % 1000000
    
    miles = resto_millones // 1000
    resto_miles = resto_millones % 1000
    
    partes = []
    
    # Mil Millones
    if mil_millones > 0:
        if mil_millones == 1:
            partes.append("UN MIL")
        else:
            partes.append(convertir_hasta_mil(mil_millones) + " MIL")

    # Millones
    if mil_millones > 0 and millones == 0:
        if miles == 0 and resto_miles == 0:
            partes.append("MILLONES DE")
        else:
            partes.append("MILLONES")
    elif millones > 0:
        if millones == 1:
            if miles == 0 and resto_miles == 0:
                partes.append("UN MILLÓN DE")
            else:
                partes.append("UN MILLÓN")
        else:
            if miles == 0 and resto_miles == 0:
                partes.append(convertir_hasta_mil(millones) + " MILLONES DE")
            else:
                partes.append(convertir_hasta_mil(millones) + " MILLONES")
    
    # Miles
    if miles > 0:
        if miles == 1:
            partes.append("MIL")
        else:
            partes.append(convertir_hasta_mil(miles) + " MIL")
    
    # Unidades (es_final=True porque es después de mil/millón o es el último grupo)
    if resto_miles > 0:
        partes.append(convertir_hasta_mil(resto_miles, es_final=True))
    
    resultado = " ".join(partes).strip()
    
    # Aplicar formato singular/plural
    if numero == 1:
        return "UN GUARANÍ"
    elif resultado:
        resultado += " GUARANÍES"
        return resultado
    else:
        return "CERO GUARANÍES"


if __name__ == "__main__":
    # Casos de prueba
    casos_prueba = [
        (1, "UN GUARANÍ"),
        (20, "VEINTE GUARANÍES"),
        (100, "CIEN GUARANÍES"),
        (101, "CIENTO UNO GUARANÍES"),
        (1000, "MIL GUARANÍES"),
        (1001, "MIL UNO GUARANÍES"),
        (125000, "CIENTO VEINTICINCO MIL GUARANÍES"),
        (1000000, "UN MILLÓN DE GUARANÍES"),
        (1000000000, "UN MIL MILLONES DE GUARANÍES"),
        (9000000000, "NUEVE MIL MILLONES DE GUARANÍES"),
        (9999999999, "NUEVE MIL NOVECIENTOS NOVENTA Y NUEVE MILLONES NOVECIENTOS NOVENTA Y NUEVE MIL NOVECIENTOS NOVENTA Y NUEVE GUARANÍES"),
    ]
    
    print("Pruebas de num2letras.py:")
    print("-" * 80)
    for numero, esperado in casos_prueba:
        resultado = numero_a_letras(numero)
        estado = "OK" if resultado == esperado else "ERROR"
        print(f"[{estado}] {numero:>15} -> {resultado}")
        if resultado != esperado:
            print(f"  Esperado: {esperado}")
    print("-" * 80)
