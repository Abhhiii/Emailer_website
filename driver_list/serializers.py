from rest_framework import serializers
from .models import *

class DriverListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverList
        fields = ['lic', 'driver', 'classes', 'personal_index']



class NewRaceDriversListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewRaceDriversList
        fields = '__all__'