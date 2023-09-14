import requests
from bs4 import BeautifulSoup
from collections import deque
import mysql.connector

# En esta lista crearemos un registro de los enlaces para evitar duplicidad
enlaces_explorados = set()

# Conéctate a la base de datos
def conectar_base_de_datos():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            # Crear base de datos en PHPMyAdmin
            database='losandes_ws'
        )
        return conn
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        return None

# Inserta un resultado en la base de datos
def insertar_resultado(palabra, url, descripcion, fecha, conn):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO resultados_juliacaJ (palabra, url, descripcion, fecha) VALUES (%s, %s, %s, %s)",
                       (palabra, url, descripcion, fecha))
        conn.commit()
        cursor.close()
    except Exception as e:
        print("Error al insertar en la base de datos:", e)

def buscar_palabra(palabra, url, conn):
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        div_contenido = soup.find('body')
        #div_contenido = soup.find('div', class_='content-inner')

        if div_contenido:
            descripcion = '\n'.join(p.text for p in div_contenido.find_all('p'))
        else:
            descripcion = ""

        entry_header = soup.find('div', class_='entry-header')
        if entry_header:
            fecha = entry_header.find('div', class_='jeg_meta_date').text.strip()
        else:
            fecha = ""

        if palabra.lower() in descripcion or palabra in descripcion or palabra.upper() in descripcion :
            print(palabra, "url encontrada:", url)
            insertar_resultado(palabra, url, descripcion, fecha, conn)
        else:
            print("Palabra no encontrada en la descripción de la URL:", url)

    else:
        print("Error al acceder a la URL", url)

def explorar_enlaces(url_inicial, nivel_maximo, conn):
    cola = deque([(url_inicial, 0)])

    while cola:
        url_actual, nivel_actual = cola.popleft()
        enlaces_explorados.add(url_actual)

        if nivel_actual <= nivel_maximo:
            response = requests.get(url_actual)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                enlaces = soup.find_all('a', href=True)

                for cada_enlace in enlaces:
                    enlace_url = cada_enlace['href']

                    if enlace_url.startswith('http') and enlace_url not in enlaces_explorados:
                        cola.append((enlace_url, nivel_actual + 1))
                        enlaces_explorados.add(enlace_url)
                        buscar_palabra("Juliaca", enlace_url, conn)

# Cambia los valores con tu configuración
conn = conectar_base_de_datos()
if conn is not None:
    explorar_enlaces("https://www.losandes.com.pe", 10, conn)
    conn.close()
else:
    print("No se pudo conectar a la base de datos.")
