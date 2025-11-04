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
import logging



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
    # send_message_to_slack(message=message)
    # send_log_to_railtown(log_message)


def parse_driver_line(text):
            text = text.strip()
            pattern1 = r'^(\d+[A-Z]?)\s*([A-Z][a-zA-Z\s]+?)\s*([A-Z]+/[A-Z]+)\s*(\d+\.\d+)$'
            match = re.match(pattern1, text)
            if match:
                lic = match.group(1)
                driver = match.group(2).strip()
                class_val = match.group(3)
                pi = match.group(4)
                return (lic, driver, class_val, pi)
            pattern2 = r'^([A-Z]+/[A-Z]+)\s*(\d+\.\d+)$'
            match = re.match(pattern2, text)
            if match:
                class_val = match.group(1)
                pi = match.group(2)
                return (None, None, class_val, pi)
            return None




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

        # Page 1 Processing
        last_lic = None
        last_driver = None
        # Define areas for each table on the first page
        area_first_table = [30, 50, 10000, 190]
        area_second_table = [30, 190, 10000, 325]
        area_third_table = [30, 330, 10000, 460]
        area_fourth_table = [30, 465, 10000, 600]
        area_fifth_table = [30, 600, 10000, 800]

        # Process each table on the first page
        for area_idx, area in enumerate([area_first_table, area_second_table, area_third_table, area_fourth_table, area_fifth_table], 1):
            try:
                df_list = tabula.read_pdf(pdf_path, output_format='dataframe', pages=1, multiple_tables=True, area=area)
                
                print(f"\n--- Area {area} (Table {area_idx}) ---")
                if not df_list:
                    print("No tables detected.")
                    continue
                
                for i, df in enumerate(df_list):
                    print(f"Table {i+1}: shape={df.shape}, columns={list(df.columns)}")
                    print(df.head(3))

                if not df_list or len(df_list) == 0:
                    print(f"No tables found for area {area}")
                    continue

                table_df = df_list[0]

                if table_df.empty:
                    print(f"Table is empty for area {area}")
                    continue

                cleaned_data = []

                # AREA 3 is already well-formatted with separate columns
                if area_idx == 3:
                    # This table already has proper columns
                    if 'Lic#' not in table_df.columns:
                        table_df.columns = ['Lic#', 'Driver', 'Class', 'PI']
                    
                    # Forward fill Lic# and Driver
                    table_df['Lic#'] = table_df['Lic#'].ffill()
                    table_df['Driver'] = table_df['Driver'].ffill()
                    
                    for _, row in table_df.iterrows():
                        lic = str(row['Lic#']).strip() if pd.notna(row['Lic#']) else ''
                        driver = str(row['Driver']).strip() if pd.notna(row['Driver']) else ''
                        class_value = str(row['Class']).strip() if pd.notna(row['Class']) else ''
                        pi_value = str(row['PI']).strip() if pd.notna(row['PI']) else ''
                        
                        if not lic and last_lic:
                            lic = last_lic
                        if not driver and last_driver:
                            driver = last_driver
                        
                        if lic and driver:
                            last_lic = lic
                            last_driver = driver
                            
                            cleaned_data.append({
                                'LIC#': lic,
                                'Driver': driver,
                                'Class': class_value,
                                'Personal Index': pi_value
                            })
                
                # For all other areas, combine columns and parse
                else:
                    for index, row in table_df.iterrows():
                        # Combine all columns into one string
                        combined_text = ' '.join([str(val) for val in row if pd.notna(val) and str(val) != 'nan'])
                        if not combined_text or 'Lic#Driver' in combined_text or 'Driver' in combined_text:
                            continue
                        
                        # Split by newlines if present
                        lines = re.split(r'[\r\n]+', combined_text)
                        
                        for line in lines:
                            line = line.strip()
                            if not line or line == 'nan':
                                continue
                            
                            # Parse the line
                            result = parse_driver_line(line)
                            
                            if result:
                                lic, driver, class_val, pi = result
                                
                                # If LIC and driver are present, update our tracking
                                if lic and driver:
                                    last_lic = lic
                                    last_driver = driver
                                # Otherwise use last known values
                                else:
                                    lic = last_lic
                                    driver = last_driver
                                
                                if lic and driver:
                                    cleaned_data.append({
                                        'LIC#': lic,
                                        'Driver': driver,
                                        'Class': class_val,
                                        'Personal Index': pi
                                    })

                if cleaned_data:
                    for record in cleaned_data:
                        try:
                            DriverList.objects.get_or_create(
                                lic=record['LIC#'][:25],
                                driver=record['Driver'][:255],
                                classes=record['Class'][:25],
                                personal_index=record['Personal Index'][:25],
                            )
                        except Exception as e:
                            print(f"Error saving record: {record} - {str(e)}")
                else:
                    print(f"✗ Area {area_idx}: No data extracted")

            except Exception as e:
                print(f"Error processing area {area} (Table {area_idx}): {str(e)}")
                import traceback
                traceback.print_exc()
                create_log_message(
                    message=f"Error processing area {area}: {str(e)}", 
                    properties={"Function": "fetch_and_process_pdf", "Area": str(area)}
                )

        

        # till here

        page_range = f'{settings.PAGE_INCLUDE}-{num_pages}'
        bottom = 10000 + (num_pages - 1) * 1000

       # Define the area coordinates [top, left, bottom, right]

        area = [0, 35, bottom, 1300]  
 
        df_list = tabula.read_pdf(pdf_path,output_format='dataframe', pages=page_range,area=area,multiple_tables=True,pandas_options={"header": None})
        if not df_list:
            create_log_message(message="No tables found in the PDF.", properties={"Function": "fetch_and_process_pdf"})
            return None, None
        cleaned_list = []
        for df in df_list:
            if df.empty:
                continue

            header_idx = df.apply(lambda r: r.astype(str).str.contains("Lic", case=False).any(), axis=1)
            if header_idx.any():
                header_row = header_idx[header_idx].index[0]
                df.columns = df.iloc[header_row].fillna('')
                df = df.iloc[header_row + 1:]
            df = df.reset_index(drop=True)
            cleaned_list.append(df)

        sheet_read = pd.concat(cleaned_list, ignore_index=True)

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
            lic_data = row[1]
            driver_data = row[2]
            classs_data = row[3]
            locationEvent_data = row[4]
            date_data = row[5]
            mineshaft_data = row[6]
            personalIndex_data = row[7]
            classIDX_data = row[8]
            et_data = row[9]
            underPersonalIDX_data = row[10]
            newPersonalIDX_data = row[11]
            underClassIDX_data = row[12]
            newClassIDX_data = row[13]

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
        send_payload_to_mailchimp(api_key=api_key, payload=payload)
        time.sleep(10)

        pdf_data = Pdfdata.objects.get(id=pdf_data_id)
        pdf_data.sent_emails = True
        pdf_data.save()


    except Exception as e:
        create_log_message(message=f"Error in sending appended rows email: {str(e)}", properties={"Function": "send_appended_rows_email"})



def send_payload_to_mailchimp(api_key, payload):
    """
    Updates an existing Mailchimp campaign (keeps header/footer intact),
    replaces only <div id="d5">...</div> content with dynamic payload body,
    then sends the campaign.
    """

    try:
        # === Mailchimp configuration ===
        MAILCHIMP_API_KEY = settings.MC_API_KEY
        MAILCHIMP_SERVER_PREFIX = settings.MC_SERVER_PREFIX  # e.g. 'us2'
        MAILCHIMP_CAMPAIGN_ID = settings.MC_CAMPAIGN_ID      # e.g. '9945956'

        base_url = f"https://{MAILCHIMP_SERVER_PREFIX}.api.mailchimp.com/3.0"
        content_url = f"{base_url}/campaigns/{MAILCHIMP_CAMPAIGN_ID}/content"
        send_url = f"{base_url}/campaigns/{MAILCHIMP_CAMPAIGN_ID}/actions/send"

        headers = {
            "Authorization": f"Bearer {MAILCHIMP_API_KEY}",
            "Content-Type": "application/json",
        }

        # === 1️⃣ Get existing campaign HTML ===
        resp = requests.get(content_url, headers=headers, timeout=30)
        resp.raise_for_status()
        existing_html = resp.json().get("html", "") or "<html><body></body></html>"
        # === 2️⃣ Extract alerts list from payload ===
        alerts = payload.get("data", {}).get("items", [])
        if not alerts:
            logging.warning("No alerts found in payload; skipping Mailchimp send.")
            return False

        # === 3️⃣ Build formatted body HTML ===
        body_blocks = []
        for a in alerts:
            lic = a.get("lic", "")
            name = a.get("driver", "")
            new_pi = a.get("newPersonalIDX", "")
            old_pi = a.get("personalIndex", "")
            class_name = a.get("class", "")
            location = a.get("locationEvent", "")
            date = a.get("date", "")
            et = a.get("et", "")
            amt = a.get("underPersonalIDX", "")

            block = f"""
            <p class="mcePastedContent" style="margin:0; margin-bottom:16px;">
                {lic}<br>
                {name} {new_pi} <span style="background-color:#fff;">(was {old_pi})</span> {class_name}
            </p>
            <p class="mcePastedContent" style="margin:0; margin-bottom:16px;">{location}{date}</p>
            <p class="mcePastedContent last-child" style="margin:0; margin-bottom:16px;">{et}({amt})</p>
            """
            body_blocks.append(block.strip())

        # Join multiple blocks with extra spacing
        body_html = "<br><br>".join(body_blocks)

        # === 4️⃣ Replace only the <div id="d5">...</div> ===
        pattern = r'(<div[^>]+id=["\']d5["\'][^>]*>)(.*?)(</div>)'
        new_html, count = re.subn(
            pattern,
            rf"\1{body_html}\3",
            existing_html,
            flags=re.DOTALL | re.IGNORECASE
        )

        if count == 0:
            logging.warning("Could not find <div id='d5'> block; skipping replacement.")
            return False

        # === 5️⃣ Update campaign content ===
        r2 = requests.put(content_url, json={"html": new_html}, headers=headers, timeout=30)
        r2.raise_for_status()
        logging.info(f"[Mailchimp] Updated campaign content (status {r2.status_code})")

        # === 6️⃣ Send campaign ===
        r3 = requests.post(send_url, headers=headers, timeout=30)
        r3.raise_for_status()
        logging.info(f"[Mailchimp] Campaign sent successfully (status {r3.status_code})")

        return True

    except Exception as e:
        logging.exception(f"Error sending to Mailchimp: {str(e)}")
        return False
