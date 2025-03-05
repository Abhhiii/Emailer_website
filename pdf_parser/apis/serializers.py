from rest_framework import serializers
# from pdf_parser.models import Emails, Pdfdata


# class EmailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Emails
#         fields = '__all__'

# class PdfdataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Pdfdata
#         fields = '__all__'

from pdf_parser.models import ClassIndex,Track


class ClassIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassIndex
        fields = ['classes']




class TrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = ['id','track_name', 'altitude']

