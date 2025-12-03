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

