import requests
import pandas as pd
from pdf_parser.models import Pdfdata
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from urllib.parse import quote_plus
from sqlalchemy import create_engine
import tabula
import PyPDF2
from django.conf import settings
import os
import http.client
import json
import time
from datetime import datetime
import pytz
from driver_list.models import DriverList, UpdatedIndex
from emailtriggering.models import PreviousTriggeredEmail,ResendEmail
import re

# def send_log_to_slack(message, properties):
#     webhook_url = ""
#     current_utc_time = datetime.now(pytz.utc).isoformat()
#     log_message = {
#         "text": f"Log Message:\nMessage: {message}\nProperties: {json.dumps(properties)}\nTimestamp: {current_utc_time}"
#     }

#     headers = {
#         "Content-Type": "application/json"
#     }

#     try:
#         response = requests.post(url=webhook_url, json=log_message, headers=headers)

#         if response.status_code == 200:
#             print("Log message successfully sent to Slack!")
#         else:
#             print(f"Failed to send log message to Slack. Status code: {response.status_code}")

#     except Exception as e:
#         print(f"Error sending log message to Slack: {str(e)}")


def send_message_to_slack(message):
  
    payload = {
        "text": message
    }
    
    try:
        response = requests.post("https://hooks.slack.com/services/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", json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            print(f"Message successfully sent to Slack: {message}")
        else:
            print(f"Failed to send message to Slack. Status code: {response.status_code}")
            print(f"Response: {response.text}")
        
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Slack: {str(e)}")
        return None

# def send_log_to_railtown(log_message):
#     url = "https://pcaee280bd8e0af4a6a969d3abced3dace7.railtownlogs.com"

#     headers = {
#         "Content-Type": "application/json",
#         'Authorization': f"Bearer {settings.LOGS_API_KEY}"
#     }

#     try:
#         response = requests.post(url=url, json=log_message, headers=headers)

#         if response.status_code == 201:
#             print("Log message successfully sent to Railtown!")
#         else:
#             print(f"Failed to send log message to Railtown.")

#     except Exception as e:
#         print(f"Error sending log message to Railtown: {str(e)}")

def create_log_message(message, properties):
    current_utc_time = datetime.now(pytz.utc).isoformat()


    log_message = [
        {
            "Body": json.dumps({
                "Message": message,
                "Level": 4,
                "Runtime": "python",
                "Properties": properties,
                "TimeStamp": current_utc_time,
                "EnvironmentId": "24f199d6-6702-4d74-ac73-95d68137100f",
                "OrganizationId": "8b312c13-8389-4f34-a43a-0c8ebbd23399",
                "ProjectId": "7c7d64d6-7e7d-4a21-8630-db1441775928"
            }),
            "UserProperties": {
                "Encoding": "utf-8",
                "AuthenticationCode": "Jd0jy5WesQLQ0l+N7WeXBUTGuxUCAX1EMJk79evVif0=",
                "ConnectionName": "pcaee280bd8e0af4a6a969d3abced3dace7.railtownlogs.com",
                "ClientVersion": "REST.v1"
            }
        }
    ]
    send_message_to_slack(message=message)
    # send_log_to_railtown(log_message)
def remove_numeric(text):
    return re.sub(r'\d+', '', str(text))
def fetch_and_process_pdf(pdf_url):
    try:
        response = requests.get(pdf_url)

        if response.status_code != 200:
            error_message = f"Failed to fetch PDF from {pdf_url}. Status code: {response.status_code}"
            create_log_message(message=error_message, properties={"Function": "fetch_and_process_pdf"})
            return None, None

        pdf_content = response.content

        if not pdf_content:
            create_log_message(message="Fetched PDF is empty.", properties={"Function": "fetch_and_process_pdf"})
            return None, None

        pdf_file_obj = Pdfdata.objects.create(pdf_url=pdf_url)
        pdf_file_name = f'{pdf_file_obj.id}.pdf'
        pdf_directory = 'pdf_files'
        pdf_path = default_storage.save(os.path.join(pdf_directory, pdf_file_name), ContentFile(pdf_content))
        csv_file_name = pdf_file_name.replace(".pdf", ".csv")

        pdf_reader = PyPDF2.PdfReader(pdf_path)

        num_pages = len(pdf_reader.pages)
        #page 1
        last_lic = None
        last_driver = None

        # Define areas for each table on the first page
        area_first_table = [0, 35, 10000, 180]
        area_second_table = [30, 190, 10000, 320]
        area_third_table = [30, 330, 10000, 460]
        area_fourth_table = [30, 465, 10000, 600]
        area_fifth_table = [30, 610, 10000, 800]

        # Process each table on the first page
        for area in [area_first_table, area_second_table, area_third_table, area_fourth_table, area_fifth_table]:
            try:
                # Read tables from PDF
                df_list = tabula.read_pdf(pdf_path, output_format='dataframe', pages=1, multiple_tables=True, area=area)

                if not df_list or len(df_list) == 0:
                    raise ValueError(f"No tables found on the specified area {area} of page 1.")

                table_df = df_list[0]

                if table_df.empty:
                    raise ValueError(f"Table is empty for area {area}.")

                # Adjust column names if needed
                if area == area_first_table:
                    table_df = table_df.iloc[1:]  # Skip header row
                    table_df.columns = ['Competition Eliminator Person']

                    cleaned_data = []
                    current_lic = None
                    current_driver = None

                    for index, row in table_df.iterrows():
                        row_data = row['Competition Eliminator Person']
                        if not pd.isna(row_data):
                            row_data_split = row_data.split('\r')

                            for data in row_data_split:
                                components = data.strip().split()
                                if len(components) >= 1:
                                    lic_candidate = components[0][:3]
                                    if lic_candidate.isdigit():
                                        current_lic = lic_candidate
                                        remaining_data = components[0][3:] + " " + " ".join(components[1:])
                                    else:
                                        remaining_data = " ".join(components)

                                    pi_value = remaining_data[-4:].strip()

                                    class_search = re.search(r'([A-Z/]+)\s*\d{1,2}\.\d{2}$', remaining_data)
                                    if class_search:
                                        class_value = class_search.group(1)
                                        driver_value = remaining_data[:class_search.start()].strip()
                                    else:
                                        class_value = ""
                                        driver_value = remaining_data.strip()

                                    if not current_lic or driver_value == "":
                                        current_lic = last_lic
                                        driver_value = last_driver
                                    else:
                                        last_lic = current_lic
                                        last_driver = driver_value

                                    cleaned_data.append({
                                        'LIC#': current_lic,
                                        'Driver': driver_value,
                                        'Class': class_value,
                                        'Personal Index': pi_value
                                    })

                    cleaned_df = pd.DataFrame(cleaned_data)

                    if not cleaned_df.empty:
                        for index, row in cleaned_df.iterrows():
                            try:
                                DriverList.objects.get_or_create(
                                    lic=row['LIC#'][:25],
                                    driver=row['Driver'],
                                    classes=row['Class'][:25],
                                    personal_index=row['Personal Index'],
                                )
                            except Exception as e:
                                print(f"Error occurred while processing first table data: {str(e)}")
                    else:
                        raise ValueError("First table data does not have the expected number of columns.")

                # Process other tables similarly
                elif area == area_second_table:
                    table_df.columns = ['Lic# Driver', 'Class', 'PI']
                    table_df = table_df.dropna(subset=['Class', 'PI'])

                    cleaned_data = []

                    for index, row in table_df.iterrows():
                        lic_driver = row['Lic# Driver']
                        class_value = row['Class']
                        pi_value = row['PI']

                        if pd.notna(lic_driver):
                            lic_driver_split = lic_driver.split(maxsplit=1)
                            if len(lic_driver_split) >= 2:
                                current_lic = lic_driver_split[0]
                                current_driver = lic_driver_split[1]
                            else:
                                current_driver = lic_driver

                        if not current_lic or not current_driver:
                            current_lic = last_lic
                            current_driver = last_driver
                        else:
                            last_lic = current_lic
                            last_driver = current_driver

                        cleaned_data.append({
                            'LIC#': current_lic,
                            'Driver': current_driver,
                            'Class': class_value,
                            'Personal Index': pi_value
                        })

                    cleaned_second_df = pd.DataFrame(cleaned_data)
                    cleaned_second_df = cleaned_second_df[cleaned_second_df['LIC#'] != 'Lic#']

                    if not cleaned_second_df.empty:
                        for index, row in cleaned_second_df.iterrows():
                            try:
                                DriverList.objects.get_or_create(
                                    lic=row['LIC#'][:25],
                                    driver=row['Driver'],
                                    classes=row['Class'][:25],
                                    personal_index=row['Personal Index'],
                                )
                            except Exception as e:
                                print(f"Error occurred while processing second table data: {str(e)}")
                    else:
                        raise ValueError("Second table data does not have the expected number of columns.")

                elif area == area_third_table:
                    table_df.columns = ['Lic#', 'Driver', 'Class', 'PI']
                    table_df['Lic#'] = table_df['Lic#'].ffill()
                    table_df['Driver'] = table_df['Driver'].ffill()

                    cleaned_data = []

                    for index, row in table_df.iterrows():
                        lic = row['Lic#']
                        driver = row['Driver']
                        class_value = row['Class']
                        pi_value = row['PI']

                        if not lic or not driver:
                            lic = last_lic
                            driver = last_driver
                        else:
                            last_lic = lic
                            last_driver = driver

                        cleaned_data.append({
                            'LIC#': lic,
                            'Driver': driver,
                            'Class': class_value,
                            'Personal Index': pi_value
                        })

                    cleaned_third_df = pd.DataFrame(cleaned_data)

                    if not cleaned_third_df.empty:
                        for index, row in cleaned_third_df.iterrows():
                            try:
                                DriverList.objects.get_or_create(
                                    lic=row['LIC#'][:25],
                                    driver=row['Driver'],
                                    classes=row['Class'][:25],
                                    personal_index=row['Personal Index'],
                                )
                            except Exception as e:
                                print(f"Error occurred while processing third table data: {str(e)}")
                    else:
                        raise ValueError("Third table data does not have the expected number of columns.")

                elif area == area_fourth_table:
                    table_df.columns = ['Lic#', 'Driver', 'Class', 'PI']
                    table_df['Lic#'] = table_df['Lic#'].ffill()
                    table_df['Driver'] = table_df['Driver'].ffill()

                    cleaned_data = []

                    for index, row in table_df.iterrows():
                        lic = row['Lic#']
                        driver = row['Driver']
                        class_value = row['Class']
                        pi_value = row['PI']

                        if not lic or not driver:
                            lic = last_lic
                            driver = last_driver
                        else:
                            last_lic = lic
                            last_driver = driver

                        cleaned_data.append({
                            'LIC#': lic,
                            'Driver': driver,
                            'Class': class_value,
                            'Personal Index': pi_value
                        })

                    cleaned_fourth_df = pd.DataFrame(cleaned_data)

                    if not cleaned_fourth_df.empty:
                        for index, row in cleaned_fourth_df.iterrows():
                            try:
                                DriverList.objects.get_or_create(
                                    lic=row['LIC#'][:25],
                                    driver=row['Driver'],
                                    classes=row['Class'][:25],
                                    personal_index=row['Personal Index'],
                                )
                            except Exception as e:
                                print(f"Error occurred while processing fourth table data: {str(e)}")
                    else:
                        raise ValueError("Fourth table data does not have the expected number of columns.")

                elif area == area_fifth_table:
                    page_1_fifth_df_list = tabula.read_pdf(pdf_path, output_format='dataframe', pages=1, multiple_tables=True, area=area_fifth_table)

                    if not page_1_fifth_df_list or len(page_1_fifth_df_list) == 0:
                        raise ValueError("No tables found on the specified area of page 1.")

                    # Get the fifth table
                    fifth_table_df = page_1_fifth_df_list[0]

                    # Drop the 'Effective' column if it exists
                    if 'Effective' in fifth_table_df.columns:
                        fifth_table_df.drop(columns=['Effective'], inplace=True)

                    # Drop rows where all elements are NaN
                    fifth_table_df.dropna(how='all', inplace=True)

                    # Reset index after dropping rows
                    fifth_table_df.reset_index(drop=True, inplace=True)

                    # Assuming the first row contains headers, we'll set those explicitly
                    fifth_table_df.columns = ['Lic# Driver', 'Class PI']

                    # Forward fill NaN values in 'Lic# Driver'
                    fifth_table_df['Lic# Driver'] = fifth_table_df['Lic# Driver'].ffill()

                    # Split the 'Lic# Driver' column into 'LIC#' and 'Driver'
                    fifth_table_df[['LIC#', 'Driver']] = fifth_table_df['Lic# Driver'].str.split(maxsplit=1, expand=True)

                    # Split the 'Class PI' column into 'Class' and 'PI'
                    fifth_table_df[['Class', 'PI']] = fifth_table_df['Class PI'].str.split(' ', n=1, expand=True)

                    # Drop the original 'Lic# Driver' and 'Class PI' columns
                    fifth_table_df.drop(columns=['Lic# Driver', 'Class PI'], inplace=True)

                    # Print the cleaned dataframe for debugging
                    print("Cleaned and processed data:")
                    print(fifth_table_df)

                    # Extracting data and cleaning it
                    cleaned_data = []

                    for index, row in fifth_table_df.iterrows():
                        lic = row['LIC#']
                        driver = row['Driver']
                        class_value = row['Class']
                        pi_value = row['PI']

                        if not lic or not driver:
                            lic = last_lic
                            driver = last_driver
                        else:
                            last_lic = lic
                            last_driver = driver

                        cleaned_data.append({
                            'LIC#': lic,
                            'Driver': driver,
                            'Class': class_value,
                            'Personal Index': pi_value
                        })

                    cleaned_fifth_df = pd.DataFrame(cleaned_data)

                    if not cleaned_fifth_df.empty:
                        for index, row in cleaned_fifth_df.iterrows():
                            try:
                                DriverList.objects.get_or_create(
                                    lic=row['LIC#'][:25],
                                    driver=row['Driver'],
                                    classes=row['Class'][:25],
                                    personal_index=row['Personal Index'],
                                )
                            except Exception as e:
                                print(f"Error occurred while processing fifth table data: {str(e)}")
                    else:
                        raise ValueError("Fifth table data does not have the expected number of columns.")

        # except Exception as e:
        #     print(f"Error processing fifth table: {str(e)}")
        #     create_log_message(message=f"Error processing fifth table: {str(e)}", properties={"Function": "fetch_and_process_pdf"})


            except Exception as e:
                print(f"Error processing table with area {area}: {str(e)}")
                create_log_message(message=f"Error in fetch_and_process_pdf: {str(e)}", properties={"Function": "fetch_and_process_pdf"})



        

        # till here

        page_range = f'{settings.PAGE_INCLUDE}-{num_pages}'
        bottom = 10000 + (num_pages - 1) * 1000

       # Define the area coordinates [top, left, bottom, right]

        area = [0, 35, bottom, 1300]  

 
        df_list = tabula.read_pdf(pdf_path,output_format='dataframe', pages=page_range,area=area,multiple_tables=True,pandas_options={"header": None,"name": None})
        print(df_list)
        if not df_list:
            create_log_message(message="No tables found in the PDF.", properties={"Function": "fetch_and_process_pdf"})
            return None, None
        df_list = [df.iloc[4:].reset_index(drop=True) for df in df_list]

        first_table = df_list[0]

        if pd.isnull(first_table.iloc[:, 0]).all():
            first_table = first_table.iloc[:, 1:]

        first_table = first_table.iloc[1:]

        first_table.columns = [f"Unnamed_{i}" for i in range(len(first_table.columns))]

        first_table['Unnamed_1'] = first_table['Unnamed_1'].apply(remove_numeric)


        df_list[0] = first_table

        sheet_read = pd.concat(df_list, ignore_index=True)

        sheet_read.columns = [f"Unnamed_{i}" for i in range(len(sheet_read.columns))]

        
        

        csv_directory = 'csv_files'
        csv_path = default_storage.save(os.path.join(csv_directory, csv_file_name), ContentFile(sheet_read.to_csv(index=False)))
        sheet_read.to_csv(csv_path, index=False)

        pdf_file_obj.csv_file.name = csv_path
        pdf_file_obj.save()

        result = sheet_read.drop_duplicates(keep=False)

        db_settings = settings.DATABASES['default']

        db_username = db_settings['USER']
        db_password = db_settings['PASSWORD']
        encoded_password = quote_plus(db_password)
        db_host = db_settings['HOST']
        db_name = db_settings['NAME']
        table_name = settings.PDF_TABLE_NAME

        engine = create_engine(f'mysql://{db_username}:{encoded_password}@{db_host}/{db_name}')

        try:
            existing_data = pd.read_sql(table_name, con=engine)
            merged_data = existing_data.merge(result, indicator=True, how='outer')
            changed_rows = merged_data[merged_data['_merge'] == 'right_only']

            if not changed_rows.empty:
                changed_rows = changed_rows.copy()
                changed_rows.drop('_merge', axis=1, inplace=True, errors='ignore')
                changed_rows.to_sql(table_name, con=engine, if_exists='append', index=False)

                create_log_message(message="PDF processed and new data added to the database.", properties={"Function": "fetch_and_process_pdf"})

                return pdf_file_obj.id, changed_rows  

        except Exception as e:
            result.to_sql(table_name, con=engine, if_exists='replace', index=False)

            print(f"Error occurred while updating the database: {str(e)}")
            create_log_message(message=f"Error processing PDF and updating the database: {str(e)}", properties={"Function": "fetch_and_process_pdf"})


    except Exception as e:
        print(f"Error occurred in fetch_and_process_pdf: {str(e)}")
        create_log_message(message=f"Error in fetch_and_process_pdf: {str(e)}", properties={"Function": "fetch_and_process_pdf"})

    return None, None


def send_payload_to_customer_io(api_key, payload):
    try:
        conn = http.client.HTTPSConnection("api.customer.io")

        headers = {
            'content-type': "application/json",
            'Authorization': f"Bearer {api_key}"
        }

        conn.request("POST", "/v1/campaigns/15/triggers", json.dumps(payload).encode('utf-8'), headers)
        res = conn.getresponse()
        data = res.read()
        create_log_message(message="Mail sent successfully to FYC Personal Index Update", properties={"Function": "send_appended_rows_email"})


    except Exception as e:
        create_log_message(message=f"Error sending email via Customer.io: {str(e)}", properties={"Function": "send_payload_to_customer_io"})




def send_payload_to_customer_io_testgroup(api_key, payload):
    try:
        conn = http.client.HTTPSConnection("api.customer.io")

        headers = {
            'content-type': "application/json",
            'Authorization': f"Bearer {api_key}"
        }

        conn.request("POST", "/v1/campaigns/15/triggers", json.dumps(payload).encode('utf-8'), headers)
        res = conn.getresponse()
        data = res.read()
        create_log_message(message=f"Mail sent successfully to FYC Personal Index Update(TST)",properties={"Function": "ResendEmail.save"})


    except Exception as e:
        create_log_message(message=f"Error sending email via Customer.io: {str(e)}", properties={"Function": "send_payload_to_customer_io"})

def send_appended_rows_email(pdf_data_id, changed_rows):
    try:
        api_key = settings.CUSTOMER_IO_API_KEY
        alerts = []
        resend_email = ResendEmail.objects.create()


        for index, row in changed_rows.iterrows():
            lic_data = row[0]
            driver_data = row[1]
            classs_data = row[2]
            locationEvent_data = row[3]
            date_data = row[4]
            mineshaft_data = row[5]
            personalIndex_data = row[6]
            classIDX_data = row[7]
            et_data = row[8]
            underPersonalIDX_data = row[9]
            newPersonalIDX_data = row[10]
            underClassIDX_data = row[11]
            newClassIDX_data = row[12]

            lic_data = lic_data if pd.notna(lic_data) else ''
            driver_data = driver_data if pd.notna(driver_data) else ''
            classs_data = classs_data if pd.notna(classs_data) else ''
            locationEvent_data = locationEvent_data if pd.notna(locationEvent_data) else ''
            date_data = date_data if pd.notna(date_data) else ''
            mineshaft_data = mineshaft_data if pd.notna(mineshaft_data) else ''
            personalIndex_data = personalIndex_data if pd.notna(personalIndex_data) else ''
            classIDX_data = classIDX_data if pd.notna(classIDX_data) else ''
            et_data = et_data if pd.notna(et_data) else ''
            underPersonalIDX_data = underPersonalIDX_data if pd.notna(underPersonalIDX_data) else ''
            newPersonalIDX_data = newPersonalIDX_data if pd.notna(newPersonalIDX_data) else ''
            underClassIDX_data = underClassIDX_data if pd.notna(underClassIDX_data) else ''
            newClassIDX_data = newClassIDX_data if pd.notna(newClassIDX_data) else ''

            alert_data = {
                "lic": lic_data,
                "driver": driver_data,
                "class": classs_data,
                "locationEvent": locationEvent_data,
                "date": date_data,
                "mineshaft": mineshaft_data,
                "personalIndex": personalIndex_data,
                "classIDX": classIDX_data,
                "et": et_data,
                "underPersonalIDX": underPersonalIDX_data,
                "newPersonalIDX": newPersonalIDX_data,
                "underClassIDX": underClassIDX_data,
                "newClassIDX": newClassIDX_data
            }

            alerts.append(alert_data)
            print(alert_data)
            PreviousTriggeredEmail.objects.create(
                index = resend_email,
                lic_data = lic_data,
                driver_data = driver_data,
                classs_data =classs_data,
                locationEvent_data=locationEvent_data,
                date_data=date_data,
                mineshaft_data =mineshaft_data,
                personalIndex_data =personalIndex_data,
                classIDX_data=classIDX_data,
                et_data =et_data,
                underPersonalIDX_data =underPersonalIDX_data,
                newPersonalIDX_data=newPersonalIDX_data, 
                underClassIDX_data =underClassIDX_data,
                newClassIDX_data=newClassIDX_data,

            )

            # DriverList.objects.create(
            #     lic = lic_data,
            #     driver = driver_data,
            #     classes = classs_data,
            #     personal_index = personalIndex_data,
            # )
            


        json_data = {'items': alerts}

        payload = {
            "data": json_data
        }

        # send_payload_to_customer_io(api_key=api_key, payload=payload)
        time.sleep(10)

        pdf_data = Pdfdata.objects.get(id=pdf_data_id)
        pdf_data.sent_emails = True
        pdf_data.save()


    except Exception as e:
        create_log_message(message=f"Error in sending appended rows email: {str(e)}", properties={"Function": "send_appended_rows_email"})

