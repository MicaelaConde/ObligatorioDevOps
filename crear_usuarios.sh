#!/bin/bash

# Codigos de error
# 1 = No se pasaron parametros
# 2 = No existe archivo
# 3 = No es un archivo regular
# 4 = No se tiene permisos de lectura sobre archivo
# 5 = Se paso mas de un archivo regular como parametro
# 6 = No se ingreso contraseña luego de modificador -c
# 7 = Modificador invalido
# 9 = Sintaxis incorrecta en archivo de usuarios

#Verificar que se hayan pasado parametros
if [ $# -eq 0 ]
then
	echo "Debe ingresar archivo con usuarios a crear" >&2
	exit 1
fi

#Validar parametros modificadores
while [[ $1 == -* ]]
do
        case $1 in
                -i)
                    info=true
                    shift
                    ;;
                -c)
                    if [[ -z $2 ]]
                    then
                        echo "Error! Falta ingresar contraseña luego de c-" >&2
                        exit 6
                    fi
                    param_passwd=true
                    passwd=$2
                    shift 2
                    ;;
                *)
                    echo "Error: Modificador "$1" invalido" >&2
                    exit 7
                    ;;
        esac
done


# Validaciones de archivo pasado como parametro

i=0
for arch in $@
do
	#Validar existencia de archivo
	if [[ ! -e $arch ]]
	then
		echo "Error: el archivo '$arch' no existe." >&2
		exit 2
	fi
	#Velidar si es un archivo regular
        if [ ! -f $arch ]
        then
                echo "Error: '$arch' no es un archivo regular" >&2
		exit 3
	else
		#Contar cuantos archivos
		archivo=$arch
                i=$((i+1))
        fi
	#Verificar permisos de lectura sobre archivo
	if [[ ! -r $arch ]]
	then
		echo "Error: no se tiene permisos de lectura sobre '$arch'"
		exit 4
	fi
done

#Verificar que se haya ingresado 1 solo archivo como parametro
if [ $i -ne 1 ]
then
    	echo "Se debe pasar 1 solo archivo por parametro y se detectaron" $i >&2
	exit 5
fi

#Validar que cada linea contenga 5 campos
while IFS=":" read -r
do

	campos=$(echo "$REPLY" | grep -o ':' | wc -l)

	if [ $campos -ne 4 ]
	then
		echo "Error: sintaxis incorrecta en la linea:" $REPLY
		exit 9
	fi
done < $archivo

usuariosCreados=0

#Filtrar datos de archivo de usuarios

while IFS=":" read -r usuario comentario home secrea shell
do
	#Verificar si variable home esta vacia, en ese caso se agrega home por defecto
	if [ -z $home ]
	then
		home="/home/"$usuario
	fi

	#Verificar si esta vacia variable shell
	if [ -z $shell ]
	then
		shell="/bin/bash"
	fi
	shellnovalida=0

	#verificar que la sehll sea valida
	if ! grep -Fxq "$shell" /etc/shells
	then
	    	echo "Shell '$shell' no válida" >&2
		shellnovalida=1
	fi

	#Verificar  variable comentario esta vacia
	if [[ -z $comentario ]]
	then
		comentario="Usuario nominal"
	fi
	
	#No crear ususario si la shell no es valida
	if [ $shellnovalida -eq 1 ]
	then
        	echo "El usuario '$usuario' no fue creado debido a una shell no válida." >&2
     	   continue
    	fi

	#Creacion de usuarios
	if [ $shellnovalida -eq 0 ]
	then
		if [[ $secrea == "si" ]]
       		then
			#Se crea usuario con directorio home
			sudo useradd -m -s "$shell" -c "\"$comentario\"" -d "$home" "$usuario"
		else
			#Se crea usuario sin directorio home
			sudo useradd -M -s "$shell" -c "\"$comentario\"" "$usuario"
		fi
	fi
	#Validar la creacion de usuarios y contar la cantida
	if [ $? -eq 0 ]
	then
		usuariosCreados=$((usuariosCreados+1))

		#Asignar contraseña
        	if [[ $param_passwd == "true" ]]
        	then
                	echo "$usuario:$passwd" | sudo chpasswd
        	fi

		#Mostrar informacion
		if [[ $info == "true" ]] 
		then
			echo "Usuario '$usuario' creado con exito con datos indicados:"
			echo "Comentario: " $comentario
			echo "Directorio home: " $home
			echo "Asegurado existencia de directorio home: " $secrea
			echo "Shell por defecto: " $shell
			echo ""
		fi
	else
		#No se pudo crear usuario
		if [[ $info == "true" ]]
		then
			echo "ATENCION: el usuario '$usuario' no pudo ser creado"
		fi
	fi

done < $archivo

if [[ $info == "true" ]]
then
	echo ""
	echo "Se han creado '$usuariosCreados' usuarios con exito"
fi

exit 0
