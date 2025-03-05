from django.views.generic import TemplateView
from rest_framework import status
from pdf_parser.models import Track,FactorsByAltitude
import docx
from rest_framework.views import APIView
from rest_framework.response import Response
import PyPDF2
from rest_framework.response import Response
from pdf_parser.apis.serializers import TrackSerializer





class SubmittedView(TemplateView):
    template_name = 'mailer-1.html'


class TrackListView(APIView):


    def get(self, request):
        tracks = Track.objects.all()
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)






class ProcessAltitudeFactors(APIView):
    def extract_and_create_factors(self, pdf_file):
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        page = pdf_reader.pages[2]  
        page_text = page.extract_text()

        lines = page_text.split('\n')[2:] 

        data = []
        for line in lines:
            if line.strip():  
                parts = line.split()
                if len(parts) == 5:
                    altitude = parts[0]
                    factor = parts[1]
                    offset = parts[2]
                    data.append((altitude, factor, offset))

        for altitude, factor, offset in data:
            FactorsByAltitude.objects.get_or_create(
                altitude=altitude,
                factor=factor,
                offset=offset
            )

    def post(self, request):
        pdf_file = request.FILES.get('pdf_file') 
        if not pdf_file:
            return Response({'error': 'No PDF file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.extract_and_create_factors(pdf_file)
            return Response({'message': 'Altitude factors imported successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ParseDocxAPIView(APIView):
    def process_docx(self, docx_file):
        try:
            doc = docx.Document(docx_file)
            tracks_created = 0

            for table in doc.tables:
                first_row_skipped = False

                for row in table.rows:
                    if not first_row_skipped:
                        first_row_skipped = True
                        continue  

                    cells = [cell.text.strip() for cell in row.cells]
                    if len(cells) >= 9:
                        division = cells[0]
                        date = cells[1]
                        track_name = cells[2]
                        city = cells[3]
                        state = cells[4]
                        altitude = cells[5]
                        et_1 = cells[6]
                        mph_1 = cells[7]
                        et_2 = cells[8]
                        mph_2 = cells[9] if len(cells) > 9 else None

                        track, created = Track.objects.get_or_create(
                            # division=division if division else None,
                            # date=date if date else None,
                            track_name=track_name if track_name else None,
                            city=city if city else None,
                            state=state if state else None,
                            altitude=altitude if altitude else None,
                            slet=et_1 if et_1 else None,
                        )

                        if created:
                            tracks_created += 1
                        

            return Response({'message': f'Successfully created {tracks_created} Track objects'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        docx_file = request.FILES.get('docx_file')

        if not docx_file:
            return Response({'error': 'No DOCX file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.process_docx(docx_file)
            return Response({'message': 'Altitude factors imported successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)