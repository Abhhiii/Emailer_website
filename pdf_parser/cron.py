from .utils import fetch_and_process_pdf, send_appended_rows_email, create_log_message
from django_cron import CronJobBase, Schedule
import logging
from django.conf import settings
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pdf_parser.models import ClassIndex  



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SendAppendedRowsEmailCronJob(CronJobBase):
    RUN_EVERY_MINS = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'process_pdf_cron_job'

    def do(self):
        pdf_url = settings.PDF_URL

        try:
            pdf_data_id, changed_rows = fetch_and_process_pdf(pdf_url)

            if pdf_data_id is not None and changed_rows is not None:
                send_appended_rows_email(pdf_data_id, changed_rows)
                logging.info("Mail sent successfully.")
            else:
                logging.info("No new data to send")

        except Exception as e:
            logging.info("Cron job execution failed.")
            create_log_message(message="Cron job execution failed.", properties={"Function": "send_appended_rows_email_cron_job"})



# from rest_framework import viewsets
# from rest_framework.response import Response
# from pdf_parser.apis.serializers import ClassIndexSerializer

    url = settings.CLASS_INDEX_SCRAPING_URL
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', {'width': '250'})
                        
        if table:
            rows = table.find_all('tr')
            for row in rows[3:]:
                columns = [col.text.strip() for col in row.find_all(['th', 'td'])]

                if len(columns) >= 3:
                    class_name = columns[0]
                    one_by_four = columns[1].lstrip('0') if columns[1].startswith('0') else columns[1]
                    one_by_eight = columns[2].lstrip('0') if columns[2].startswith('0') else columns[2]


                    if class_name in [
                        'AA/AM', 'AA/AT', 'AA/AF',
                        'BB/A', 'BB/AM', 'BB/AT', 'BB/AF',
                        'CC/A', 'CC/AT', 'DD/AT', 'A/PM', 'AA/PM'
                    ]:
                        power_adder = True
                    else:
                        power_adder = False

                    class_index_instance, created = ClassIndex.objects.get_or_create(
                        classes=class_name,
                        one_by_four=one_by_four,
                        one_by_eight=one_by_eight
                    )
                    class_index_instance.power_adder = power_adder
                    class_index_instance.save()

                else:
                    print(f"Skipping row: {columns}. Not enough columns.")
            create_log_message(message="Class Index scrapped from NHRA website and successfully saved in database", properties={"Function": "send_appended_rows_email_cron_job"})

        else:
            create_log_message(message="Class Index table not found on the NHRA website", properties={"Function": "send_appended_rows_email_cron_job"})
    else:
        create_log_message(message={"Issue in scrapping Class Index from NHRA website.This url : {url} does not responded. "}, properties={"Function": "send_appended_rows_email_cron_job"})
