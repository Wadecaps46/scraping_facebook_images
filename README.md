# Scraping de Imágenes de Perfiles de Facebook

Este proyecto permite realizar scraping de imágenes de perfiles de Facebook, subirlas a un bucket de Amazon S3 y registrar la información en una base de datos MySQL.
Yo trabaje este poryecto con windows y chrome

## Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Estructura del Código](#estructura-del-código)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)

## Descripción del Proyecto

Este script utiliza Selenium para automatizar la navegación por perfiles de Facebook y extraer imágenes. Las imágenes son luego subidas a un bucket en Amazon S3 y los metadatos se almacenan en una base de datos MySQL. Esto permite gestionar eficientemente grandes volúmenes de datos visuales.

## Requisitos

- Python 3.6 o superior
- Selenium
- Boto3 (para interactuar con AWS S3)
- pymysql (para interactuar con MySQL)
- requests (para descargar imágenes)
- Instalar chromedriver respectivamenrte la versión de su navegador Chrome que tengan
- Otros más que estan en el archivo requirements.txt

## El script se encargará de:
Navegar a los perfiles de Facebook especificados.
Realizar el scraping de las imágenes.
Subir las imágenes a S3.
Guardar la información en la base de datos MySQL.