# this file serve to take a model and convert it into JSON compatible data

from core.models import (
    Macchinari,
    AllarmiSoluzioni,
    Componenti,
    Informazioni
)

from rest_framework import serializers

class MacchinariSerializers(serializers.ModelSerializer):
    class Meta:
        model = Macchinari

        fields = ["piano_produzione","categoria","tipo"]
#
class ComponentiSerializers(serializers.ModelSerializer):
    class Meta:
        model = Componenti

        fields = ["descrizione_pezzo"]
#
class AllarmiSerializers(serializers.ModelSerializer):
    class Meta:
        model = AllarmiSoluzioni

        fields = ["titolo"]
#
class InformazioniSerializers(serializers.ModelSerializer):
    class Meta:
        # reference to the model
        model = Informazioni

        # info to serialize and return
        # fields = ["id_macchinario","id_allarme","id_componente","soluzione_problema","path_img","path_video"]
        fields = "__all__"
#