from django.core.management.base import BaseCommand
from pdf_parser.models import Pdfdata

class Command(BaseCommand):
    help = 'Reset the sent_emails status for new appended data'

    def handle(self, *args, **kwargs):
        Pdfdata.objects.filter(sent_emails=True).update(sent_emails=False)
