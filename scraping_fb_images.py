from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

import pymysql
import boto3
import logging
from botocore.exceptions import ClientError
import requests
import io

import time
from datetime import datetime
import ssl
import os
from dotenv import load_dotenv


load_dotenv()


path = 'chromedriver.exe'
service = Service(path)
options = webdriver.ChromeOptions()

# Desactivar las notificaciones
prefs = {
    "profile.default_content_setting_values.notifications": 2  # 2 para bloquear notificaciones
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()
driver.get("https://www.facebook.com/login/")
time.sleep(10)

# Configuraci´n para entrar a facebook
FACEBOOK_USER = os.environ.get('FACEBOOK_USER')
FACEBOOK_PASSWORD = os.environ.get('FACEBOOK_PASSWORD')

ssl._create_default_https_context = ssl._create_unverified_context
textos = []
# login
time.sleep(8)
username = driver.find_element("css selector", "input[name='email']")
password = driver.find_element("css selector", "input[name='pass']")
username.clear()
password.clear()
username.send_keys(FACEBOOK_USER)
password.send_keys(FACEBOOK_PASSWORD)
login = driver.find_element("css selector", "button[type='submit']").click()
time.sleep(6)


# Función para obtener los perfiles válidos desde la base de datos
def get_valid_profiles_from_db():
    """Función para obtener la lista de perfiles válidos desde la tabla perfil_facebook_new."""
    connection = pymysql.connect(
        host=os.environ.get('host'),
        database=os.environ.get('database'),
        user=os.environ.get('user'),
        password=os.environ.get('password'),
        port= int(os.environ.get('port'))
    )
    
    try:
        with connection.cursor() as cursor:
            # Consulta para obtener perfiles
            query = """
            SELECT id_perfil, perfil 
            FROM perfiles_scraping;
            """
            cursor.execute(query)
            result = cursor.fetchall()  # Obtener todos los resultados
            if result:  # Si hay resultados
                profile_list = [{'id_perfil': row[0], 'perfil': row[1]} for row in result]
                return profile_list
            else:
                return []
    finally:
        connection.close()
    
    return profile_list
    

def save_image_to_db(id_perfil, s3_url):
    """Guarda una imagen en la tabla prueba_scraping_images."""
    connection = pymysql.connect(
        host=os.environ.get('host'),
        database=os.environ.get('database'),
        user=os.environ.get('user'),
        password=os.environ.get('password'),
        port=int(os.environ.get('port'))
    )

    try:
        with connection.cursor() as cursor:
            insert_query = """
            INSERT INTO prueba_scraping_images (id_perfil, foto, descripcion, red_social, periodo_scraping)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                id_perfil,
                s3_url,
                None,  
                None,
                '2024-10' 
            ))
        connection.commit()
    finally:
        connection.close()


# Función para subir archivos desde memoria a S3
def upload_image_to_s3(image_binary, bucket, object_name):
    s3_client = boto3.client(
        service_name='s3',
        region_name=os.environ.get('ENV_AWS_REGION_NAME'),
        aws_access_key_id=os.environ.get('ENV_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key= os.environ.get('ENV_AWS_SECRET_ACCESS_KEY')
    )
    
    try:
        # Convertir la imagen descargada (binaria) a un objeto de Bytes
        file_obj = io.BytesIO(image_binary)
        s3_client.upload_fileobj(file_obj, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

# Nombre del bucket
bucket_name = os.environ.get('ENV_AWS_S3_BUCKET_NAME')


profile_list = get_valid_profiles_from_db()

image_data = []

for profile_data in profile_list:
    url = profile_data['perfil']
    id_perfil = profile_data['id_perfil']
    username = url.split('/')[-1]

    # Vamos al perfil
    photos_perfil = f"{url}/photos"
    driver.get(photos_perfil)
    time.sleep(10)

    image_data = []

    # Desplazarse hacia abajo en la página para cargar más imágenes
    last_height = driver.execute_script("return document.body.scrollHeight")
    max_scrolls = 3  # límite de desplazamientos
    scroll_count = 0  # Contador de desplazamientos

    while scroll_count < max_scrolls:
        # Desplazar hacia abajo
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Esperar a que las nuevas imágenes se carguen

        # Calcular nueva altura y comparar con la altura anterior
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Salir si no hay más contenido para cargar
        last_height = new_height
        scroll_count += 1 
    
    while True:
        try:
            image_elements = driver.find_elements(By.CSS_SELECTOR, "img.xzg4506")
            image_urls = [img.get_attribute("src") for img in image_elements]
            break
        except Exception as e:
            print(f"Elemento no encontrado: {e}")
            time.sleep(4)

    print(f"Se encontraron {len(image_urls)} imágenes, del perfil {username}.")


    for index, image_url in enumerate(image_urls[:5]):
        try:
            #current_date = datetime.now().strftime("%Y-%m")
            perido = '2024-10'
            foto_nombre = f"{perido}_{id_perfil}_{index + 1}.png"
            print(f"Imagen obtenida: {foto_nombre}")

            object_name = f"web-scraping/img/facebook/{foto_nombre}"

            # Descargar la imagen desde la URL en memoria
            response = requests.get(image_url)
            if response.status_code == 200:
                image_binary = response.content  # Obtener el contenido binario de la imagen
                
                # Subir la imagen directamente desde la memoria a S3
                if upload_image_to_s3(image_binary, bucket_name, object_name):
                    print(f"{foto_nombre} subida exitosamente.")

                    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"

                    # Guardar los datos de la imagen en la base de datos
                    save_image_to_db(id_perfil, s3_url)

                else:
                    print(f"Error al subir {foto_nombre}.")
            else:
                print(f"Error al descargar la imagen desde {image_url}")

        except Exception as e:
            print(f"Error al procesar la imagen: {e}")
        
    time.sleep(3)

driver.quit()