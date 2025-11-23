# from django.shortcuts import render
# from rest_framework import generics
# from rest_framework.response import Response
# from .models import *
# from .serializers import DriverListSerializer,NewRaceDriversListSerializer
# from django.db.models import Q
# from rest_framework.views import APIView
# from pdf_parser.models import ClassIndex
# from rest_framework import status
# import uuid
# # Create your views here.

# class DriverListAPIView(APIView):
#     serializer_class = DriverListSerializer

#     def get(self, request, *args, **kwargs):
#         session_key = self.request.session.get('newuser')
#         name_query = self.request.query_params.get('name')
#         class_query = self.request.query_params.get('class')

#         if name_query and class_query:
#             queryset = DriverList.objects.filter(driver__icontains=name_query, classes__icontains=class_query)
#             if queryset.exists():
#                 latest_data = queryset.last()
#                 serializer = self.serializer_class(latest_data)
#                 NewRaceDriversList.objects.create(
#                     type='PI',
#                     session_id=session_key,
#                     lic=latest_data.lic,
#                     driver=latest_data.driver,
#                     classes=latest_data.classes,
#                     index=latest_data.personal_index
#                 )
#                 response_data = {
#                     'type':'PI',**serializer.data
#                 }
#                 return Response(response_data)
#             else:
#                 try:
#                     class_index = ClassIndex.objects.get(classes__exact=class_query)
                    
#                     response_data = {
#                         'lic': ' ',
#                         'driver': name_query,
#                         'classes': class_query,
#                         'personal_index': class_index.one_by_four 
#                     }
#                     NewRaceDriversList.objects.create(
#                         session_id=session_key,
#                         lic=response_data['lic'],
#                         driver=response_data['driver'],
#                         classes=response_data['classes'],
#                         index=response_data['personal_index']
#                     )
#                     return Response(response_data)
#                 except ClassIndex.DoesNotExist:
#                     return Response({'detail': 'No matching driver or class found.'}, status=status.HTTP_404_NOT_FOUND)

#         elif name_query:
#             name_suggestions = DriverList.objects.filter(driver__icontains=name_query).values_list('driver', flat=True).distinct()
#             class_suggestions = DriverList.objects.filter(driver__icontains=name_query).values_list('classes', flat=True).distinct()
#             return Response({'name_suggestions': name_suggestions, 'class_suggestions': class_suggestions})
#         elif class_query:
#             queryset = DriverList.objects.filter(classes__icontains=class_query)
#             serializer = self.serializer_class(queryset, many=True)
#             return Response(serializer.data)
#         else:
#             return Response({'detail': 'Please provide either name or class query parameter.'}, status=status.HTTP_400_BAD_REQUEST)



# class NewRaceDriversListView(generics.ListAPIView):
#     serializer_class = NewRaceDriversListSerializer

#     def get_queryset(self):
#         session_key = self.request.session.get('newuser')
#         if not session_key:
#             session_key = str(uuid.uuid4())
#             self.request.session['newuser'] = session_key
#         queryset = NewRaceDriversList.objects.filter(session_id=session_key)
#         return queryset

# class NewRaceDriversListDeleteView(generics.DestroyAPIView):
#     queryset = NewRaceDriversList.objects.all()
#     serializer_class = NewRaceDriversListSerializer
#     lookup_field = 'id' 



















from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from .models import *
from .serializers import DriverListSerializer,NewRaceDriversListSerializer
from django.db.models import Q
from rest_framework.views import APIView
from pdf_parser.models import ClassIndex, FactorsByAltitude, Track
from rest_framework import status
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
import uuid
import math





class DriverListAPIView(APIView):
    serializer_class = DriverListSerializer

    def get(self, request, *args, **kwargs):
        session_key = self.request.session.get('newuser')
        name_query = self.request.query_params.get('name')
        class_query = self.request.query_params.get('class')
        track_id = self.request.query_params.get('track_id')

        try:
            track = Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            return Response({'detail': 'Invalid track_name_id.'}, status=status.HTTP_404_NOT_FOUND)

        if name_query and class_query:
            queryset = DriverList.objects.filter(driver__icontains=name_query, classes__exact=class_query)
            if queryset.exists():
                latest_data = queryset.last()
                serializer = self.serializer_class(latest_data)
                updated_index = self.calculate_updated_index(class_query, track,latest_data.personal_index)
                NewRaceDriversList.objects.create(
                    type='PI',
                    session_id=session_key,
                    lic=latest_data.lic,
                    driver=latest_data.driver,
                    classes=latest_data.classes,
                    index=latest_data.personal_index,
                    updated_index=updated_index
                )
                response_data = {
                    'type': 'PI',
                    **serializer.data,
                    'updated_index': updated_index
                }
                return Response(response_data)
            else:
                try:
                    class_index = ClassIndex.objects.get(classes__exact=class_query)
                    updated_index = self.calculate_updated_index(class_query, track,class_index.one_by_four)

                    response_data = {
                        'lic': ' ',
                        'driver': name_query,
                        'classes': class_query,
                        'personal_index': class_index.one_by_four,
                        'updated_index': updated_index
                    }
                    NewRaceDriversList.objects.create(
                        session_id=session_key,
                        lic=response_data['lic'],
                        driver=response_data['driver'],
                        classes=response_data['classes'],
                        index=response_data['personal_index'],
                        updated_index=response_data['updated_index']
                    )
                    return Response(response_data)
                except ClassIndex.DoesNotExist:
                    return Response({'detail': 'No matching driver or class found.'}, status=status.HTTP_404_NOT_FOUND)
        elif name_query:
            name_suggestions = DriverList.objects.filter(driver__icontains=name_query).values_list('driver', flat=True).distinct()
            class_suggestions = DriverList.objects.filter(driver__icontains=name_query).values_list('classes', flat=True).distinct()
            return Response({'name_suggestions': name_suggestions, 'class_suggestions': class_suggestions})
        elif class_query:
            queryset = DriverList.objects.filter(classes__icontains=class_query)
            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Please provide either name or class query parameter.'}, status=status.HTTP_400_BAD_REQUEST)



    def calculate_updated_index(self, class_query, track,personal_index):
            class_index = ClassIndex.objects.get(classes__exact=class_query)
            personal_index = float(personal_index)
            if class_index.power_adder:
                try:
                    factors = FactorsByAltitude.objects.get(altitude=track.altitude)
                    factor = float(factors.factor)
                    offset = float(factors.offset)
                    # slet = float(track.slet)
                    updated_index = (personal_index * (((factor - 1) / 2) + 1)) + (offset / 2)
                except FactorsByAltitude.DoesNotExist:
                    updated_index = 0  
            else:
                try:
                    factors = FactorsByAltitude.objects.get(altitude=track.altitude)
                    factor = float(factors.factor)
                    offset = float(factors.offset)
                    # slet = float(track.slet)
                    updated_index = ((personal_index *factor ) + offset)
                except FactorsByAltitude.DoesNotExist:
                    updated_index = 0  

            formatted_updated_index = math.floor(updated_index*100)/100

            return f"{formatted_updated_index:.2f}"


class NewRaceDriversListView(generics.ListAPIView):
    serializer_class = NewRaceDriversListSerializer

    def get_queryset(self):
        session_key = self.request.session.get('newuser')
        if not session_key:
            session_key = str(uuid.uuid4())
            self.request.session['newuser'] = session_key

        queryset = NewRaceDriversList.objects.filter(session_id=session_key).order_by('driver')
        return queryset

class NewRaceDriversListDeleteView(generics.DestroyAPIView):
    queryset = NewRaceDriversList.objects.all()
    serializer_class = NewRaceDriversListSerializer
    lookup_field = 'id' 