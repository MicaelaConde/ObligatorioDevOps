
# Pasos para el despliegue automatizado

## 1 - Crear secreto en AWS Secret Manager

### Este paso es obligatorio, sin la existencia del secreto no podra desplegarse la aplicacion 

	- Ve a la consola de AWS 
    
	- En la barra de busqueda escribe: Secret Manager 
    
	- Selecciona "Almacenar un nuevo secreto" 

	- Selecciona "Otro tipo de secreto" 
    
	- Ingresa clave "password" y la contraseña deseada(no puede contener caracteres como @,/," espacios o ,(coma)) debe tener entre 8 y 41 caracteres. 
    
	- Dejar valores por defecto y seleccionar "siguiente" 
    
	- En "Nombre del serceto" ingresar exactamente el valor secretpassword 
    
	- Dejar valores por defecto y seleccionar siguiente 
    
	- Siguiente 
    
	- Siguiente 
    
	- Almacenar

# 2 - Requisitos antes del despliegue en maquina local 

	- Python 3.8 
    
	- boto3 instalado (pip install boto3) 
    
	- AWS CLI configurado 

# 3 - Requisitos en AWS Contar con permisos: 
	- EC2 
	- S3 
	- RDS 
	- Secret Manager 
	- IAM PassRole

# 4 - Clonar repositorio 

	- git clone https://github.com/MicaelaConde/ObligatorioDevOps.git - cd ObligatorioDevOps

# 5 - Ejecutar script de despliegue 

	- python secure_deploy.py

# El script realizara automaticamente: 

	-Creacion de bucket S3 
    
	-Subida de archivo de la aplicacion 
    
	-Creacion de security group 
    
	-Creacion de una instancia de base de datos RGS MySQL 
    
	-Creacion de instancia EC2 que descarga el archivo de aplicacion e instalacion de servidor web 
    
	-Genera automaticamente archivo .env con credenciales en EC2 
    
	-Deploy final de la aplicacion
    
