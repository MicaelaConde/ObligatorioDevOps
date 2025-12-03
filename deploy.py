import boto3
import os
from botocore.exceptions import ClientError
import json

# Inicializar clientes
s3 = boto3.client("s3")
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
secrets = boto3.client("secretsmanager")

# Parámetros
BUCKET_NAME = "rh-app-secure-bucket"
ARTIFACT_PATH = "artefactos/app_rh.zip"
ARTIFACT_NAME = "app_rh.zip"

EC2_AMI = "ami-06b21ccaeff8cd686"
INSTANCE_TYPE = "t2.micro"
INSTANCE_PROFILE = "LabInstanceProfile"
TAG_NAME = "webserver-rh"

DB_IDENTIFIER = "rhapp-mysql"
DB_NAME = "demo_db"
DB_USER = "admin"
DB_SECRET_NAME = "secretpassword"

# Obtener password desde Secrets Manager
print("*** Obteniendo password desde AWS Secrets Manager ***")
try:
    response = secrets.get_secret_value(SecretId=DB_SECRET_NAME)
    secret_dict = json.loads(response["SecretString"])
    DB_PASSWORD = secret_dict["password"]

except ClientError:
    raise Exception(
        f"ERROR: No se pudo obtener el secreto {DB_SECRET_NAME}. "
        "Debe crearse en Secrets Manager"
    )

# Crear bucket S3
print("\n*** Creando bucket s3 ***")
try:
    s3.create_bucket(Bucket=BUCKET_NAME)
    print(f"Bucket creado: {BUCKET_NAME}")

except ClientError as e:
    if "BucketAlreadyOwnedByYou" in str(e):
        print(f"El bucket {BUCKET_NAME} ya existe.")
    else:
    	raise e

# Subir archivo al busket
print("*** Subiendo archivo al bucket ***")
try:
    s3.upload_file(ARTIFACT_PATH, BUCKET_NAME, ARTIFACT_NAME)
    print("Archivo subido correctamente")
except FileNotFoundError:
    raise Exception(f"ERROR: No se encontró el archivo {ARTIFACT_PATH}")

# Crear Security Group
print("\n*** Creando Security Group ***")
SG_NAME = "rhapp-web-sg"

try:
    sg = ec2.create_security_group(
        GroupName=SG_NAME,
        Description="SG para app RH"
    )
    SG_ID = sg["GroupId"]

    ec2.authorize_security_group_ingress(
        GroupId=SG_ID,
        IpPermissions=[
            {
             	"IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            },
            {
             	"IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            },
            {
             	"IpProtocol": "tcp",
                "FromPort": 3306,
                "ToPort": 3306,
                "UserIdGroupPairs": [{"GroupId": SG_ID}]
            }
	]
    )
    print(f"Security Group creado: {SG_ID}")

except ClientError as e:
    if "InvalidGroup.Duplicate" in str(e):
        SG_ID = ec2.describe_security_groups(
            GroupNames=[SG_NAME])["SecurityGroups"][0]["GroupId"]
        print(f"SG ya existente: {SG_ID}")
else:
	raise e

# Crear RDS MySQL
print("\n*** Creando Instancia RDS ***")
try:
    rds.create_db_instance(
        DBInstanceIdentifier=DB_IDENTIFIER,
        AllocatedStorage=20,
        Engine="mysql",
        DBInstanceClass="db.t3.micro",
        MasterUsername=DB_USER,
        MasterUserPassword=DB_PASSWORD,
        DBName=DB_NAME,
        PubliclyAccessible=False,
        BackupRetentionPeriod=0
    )
    print("RDS en proceso de creación..")
except rds.exceptions.DBInstanceAlreadyExistsFault:
    print("La instancia RDS ya existe")

# Esperar que RDS esté disponible
print("Esperando que RDS esté disponible...")
rds.get_waiter("db_instance_available").wait(DBInstanceIdentifier=DB_IDENTIFIER)

db_instance = rds.describe_db_instances(DBInstanceIdentifier=DB_IDENTIFIER)
DB_ENDPOINT = db_instance["DBInstances"][0]["Endpoint"]["Address"]
print(f"Endpoint RDS: {DB_ENDPOINT}")

# Crear EC2 con UserData que genera archivo .env con credenciales de RDS
user_data = '''#!/bin/bash
sudo yum update -y
sudo yum install -y httpd mysql -y
sudo systemctl start httpd
sudo systemctl enable httpd

echo "DB_HOST={DB_ENDPOINT}" >> /home/ec2-user/.env
echo "DB_NAME={DB_NAME}" >> /home/ec2-user/.env
echo "DB_USER={DB_USER}" >> /home/ec2-user/.env
echo "DB_PASSWORD={DB_PASSWORD}" >> /home/ec2-user/.env
echo "DB_PORT=3306" >> /home/ec2-user/.env

echo "¡Sitio personalizado con conexión a RDS!" > /var/www/html/index.html
'''
print("\n *** Creando instancia EC2 ***")
response = ec2.run_instances(
    ImageId=EC2_AMI,
    InstanceType=INSTANCE_TYPE,
    MinCount=1,
    MaxCount=1,
    IamInstanceProfile={'Name': INSTANCE_PROFILE},
    SecurityGroupIds=[SG_ID],
    UserData=user_data
)

# Agregar tag Name: webserver-devops
instance_id = response['Instances'][0]['InstanceId']
ec2.create_tags(
    Resources=[instance_id],
    Tags=[{'Key': 'Name', 'Value': 'webserver-devops'}]
)
print(f"Instancia EC2 creada con ID: {instance_id} y tag 'webserver-devops'")

# Esperar estado running
print("Esperando que la instancia esté running..")
ec2.get_waiter("instance_running").wait(InstanceIds=[instance_id])

print("\n*** Despliegue realizado con exito ***")

