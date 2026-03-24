# this file serve to take a model and convert it into JSON compatible data
# BUT FOR NOW I DO IT MANUALLY - CAUSE I CAN'T MAKE IT WORK WITH MULTIPLE-TABLES

from core.models import (
    Macchinari,
    AllarmiSoluzioni,
    Informazioni
)

from rest_framework import serializers

class MacchinariSerializers(serializers.ModelSerializer):
    class Meta:
        model = Macchinari

        fields = "__all__"
#
#
class AllarmiSerializers(serializers.ModelSerializer):
    class Meta:
        model = AllarmiSoluzioni

        fields = "__all__"
#
class InformazioniSerializers(serializers.ModelSerializer):
    
    id_macchinario = MacchinariSerializers(read_only=True)
    id_allarme = AllarmiSerializers(read_only=True)
    
    class Meta:
        # reference to the model
        model = Informazioni

        # info to serialize and return
        # fields = ["id_macchinario","id_allarme"]
        fields = ['id', 'id_macchinario', 'id_allarme']
#