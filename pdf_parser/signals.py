# pdf_parser/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from pdf_parser.models import PdfForFactor,TrackDocs
from pdf_parser.apis.viewsets import ParseExcelAPIView, ProcessAltitudeFactors 

@receiver(post_save, sender=PdfForFactor)
def process_pdf_for_factors(sender, instance, created, **kwargs):
    if created:  
        try:
            with open(instance.factor_pdf.path, 'rb') as pdf_file:
                view = ProcessAltitudeFactors()
                view.extract_and_create_factors(pdf_file)

        except Exception as e:
            print(f"Error processing PDF: {e}")




@receiver(post_save, sender=TrackDocs)
def process_uploaded_excel(sender, instance, created, **kwargs):
    if created:
        try:
            with open(instance.track_doc.path, 'rb') as excel_file:
                view = ParseExcelAPIView()
                view.process_excel(excel_file)
        except Exception as e:
            print(f"Error processing Excel file: {e}")