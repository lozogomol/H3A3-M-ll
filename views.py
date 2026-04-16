import requests
import urllib3
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
# CORRECCIÓN: Importamos MapaGeografico en lugar de CapturaClimatica
from .models import RegistroUsuario, MapaGeografico 
from .serializers import MapaGeograficoSerializer
from django.contrib.auth.hashers import make_password, check_password

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@api_view(['GET'])
def listar_capturas_view(request):
    try:
        # CORRECCIÓN: Usamos MapaGeografico
        capturas = MapaGeografico.objects.all().order_by('-fecha_registro')
        serializer = MapaGeograficoSerializer(capturas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def telemetria_proxy_view(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    
    if not lat or not lon:
        return Response({"error": "Coordenadas ausentes"}, status=status.HTTP_400_BAD_REQUEST)

    API_KEY_WEATHER = '9350bc1e2a27af0c161a776609588edc'
    
    nombres_paises = {
        'BO': 'BOLIVIA', 'AR': 'ARGENTINA', 'BR': 'BRASIL', 'CL': 'CHILE',
        'PY': 'PARAGUAY', 'PE': 'PERÚ', 'UY': 'URUGUAY', 'CO': 'COLOMBIA',
        'VE': 'VENEZUELA', 'EC': 'ECUADOR', 'US': 'ESTADOS UNIDOS', 'ES': 'ESPAÑA',
        'MX': 'MÉXICO', 'FR': 'FRANCIA', 'IT': 'ITALIA', 'DE': 'ALEMANIA'
    }
    
    try:
        url_clima = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY_WEATHER}&units=metric&lang=es"
        response = requests.get(url_clima, timeout=5, verify=False)
        res_clima = response.json()

        if res_clima.get('cod') != 200:
            return Response({"error": "Error en API OpenWeather"}, status=status.HTTP_400_BAD_REQUEST)

        main_data = res_clima.get('main', {})
        sys_data = res_clima.get('sys', {})
        weather_data = res_clima.get('weather', [{}])[0]
        
        try:
            presion_mar = float(main_data.get('pressure', 1013.25))
            temp_c = float(main_data.get('temp', 15))
            temp_k = temp_c + 273.15
            presion_estacion = main_data.get('grnd_level')
            
            if presion_estacion and float(presion_estacion) > 0:
                presion_estacion = float(presion_estacion)
                altitud_final = round(((pow((presion_mar / presion_estacion), (1/5.257)) - 1) * temp_k) / 0.0065)
            else:
                altitud_final = round(44330 * (1 - pow(presion_mar / 1013.25, 0.1903)))
            
            f_lon = float(lon)
            if f_lon < -67.5 and altitud_final < 2000:
                altitud_final += 3600
            elif f_lon > -62.0 and altitud_final > 1000:
                altitud_final = round(altitud_final / 10)
                
        except (TypeError, ValueError, ZeroDivisionError):
            altitud_final = 0

        if altitud_final < 0: altitud_final = 0

        return Response({
            'temperatura': round(temp_c),
            'humedad': main_data.get('humidity', 0),
            'descripcion': weather_data.get('description', '').upper(),
            'lugar': res_clima.get('name', 'ZONA RURAL').upper(),
            'pais': nombres_paises.get(sys_data.get('country'), sys_data.get('country', '')).upper(),
            'altitud': altitud_final
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"--- ERROR CRÍTICO EN TELEMETRÍA: {str(e)} ---")
        return Response({"error": "Fallo interno en el cálculo de datos"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def capturar_datos_view(request):
    # CORRECCIÓN: El serializer ahora usará internamente MapaGeografico
    serializer = MapaGeograficoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    def post(self, request):
        data = request.data
        try:
            hashed_password = make_password(data.get('password'))
            usuario = RegistroUsuario.objects.create(
                nombre=data.get('nombre'),
                email=data.get('email'),
                password=hashed_password,
                departamento=data.get('departamento')
            )
            return Response({"status": "success", "id": usuario.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        data = request.data
        try:
            usuario = RegistroUsuario.objects.get(email=data.get('email'))
            if check_password(data.get('password'), usuario.password):
                return Response({
                    "status": "success",
                    "user": {
                        "nombre": usuario.nombre,
                        "email": usuario.email,
                        "departamento": usuario.departamento
                    }
                }, status=status.HTTP_200_OK)
            return Response({"error": "Password incorrecto"}, status=status.HTTP_401_UNAUTHORIZED)
        except RegistroUsuario.DoesNotExist:
            return Response({"error": "Usuario no registrado"}, status=status.HTTP_404_NOT_FOUND)
        