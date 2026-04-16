from rest_framework import serializers
from .models import MapaGeografico, RegistroUsuario

class MapaGeograficoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapaGeografico
        fields = '__all__'

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroUsuario
        fields = ['id', 'nombre', 'email', 'departamento']