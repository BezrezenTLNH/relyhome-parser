
import re
import time
from datetime import datetime

import requests
from selenium.webdriver.chrome.options import Options

from config import *
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class RelyhomeParser():
    def __init__(self):
        self.rows_data = {}
        self.all_data = {}
        self.creds = None
        self.cookies = None
        self.extracted_data = None
        self.driver = None
        self.today = datetime.today().day
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

    def parse(self):
        # Настройка опций для headless-режима
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Включение headless-режима
        chrome_options.add_argument("--disable-gpu")  # Для стабильности на Windows
        chrome_options.add_argument("--no-sandbox")  # Для работы в Docker (если нужно)
        chrome_options.add_argument("--window-size=1920,1080")  # Установка размера окна
        chrome_options.add_argument("--disable-dev-shm-usage")  # Решение проблем с памятью на некоторых системах
        self.driver = webdriver.Chrome()

        # Open the webpage
        self.driver.get(MAIN_URL)

        # Wait for the dynamic data to load
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.ID, "login-email")))

        # Fill in the email and password
        email_field = self.driver.find_element(By.ID, "login-email")
        password_field = self.driver.find_element(By.ID, "login-password")

        email_field.send_keys(LOGIN)  # Replace with your actual email
        password_field.send_keys(PASSWORD)
        # Ожидание от пользователя ручного прохождения CAPTCHA
        print("Please solve the CAPTCHA manually and press Enter to continue...")
        input("Press Enter when done...")

        # Нажатие кнопки "Sign In"
        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        # Ожидание загрузки страницы после авторизации
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "DataTables_Table_0")))

        # Сохранение cookies после авторизации
        selenium_cookies = self.driver.get_cookies()
        self.cookies = {
            'COOKIE': selenium_cookies[0]['value'],
            'PHPSESSID': selenium_cookies[1]['value'],
        }
        log.debug('Cookies set')
        while 1:
            self.rows_data = {}
            self.all_data = {}
            # Обновляем страницу
            self.driver.refresh()

            # Ждём, чтобы убедиться в обновлении
            time.sleep(3)
            # Загрузка HTML страницы
            html = self.driver.page_source
            log.debug("Start get_page_data")
            self.get_page_data(html)
            log.debug("Finish get_page_data")
            time.sleep(1)
            pagination = 1
            # Пагинация с использованием кнопки "Next"
            while pagination:
                try:
                    self.click_next_button()
                except:
                    log.info("Pagination is done.")
                    pagination = 0
            self.filter_correct_works()
            log.info(f"{len(self.rows_data.keys())} jobs collected.")
            log.debug(f"SVO's of this jobs: {[i for i in self.rows_data.keys()]}.")
            time.sleep(60)
            if len(self.rows_data.keys()):
                for work_num, work_data in self.rows_data.items():
                    log.debug(f"work number: {work_num}, value: {self.rows_data['sum_value']} work data: {work_data}")
                    sid = work_data['href'].split('?sid=')[-1].split('&')[0]
                    cid = work_data['href'].split('&cid=')[-1].split('&')[0]
                    vid = work_data['href'].split('&vid=')[-1].split('&')[0]
                    log.debug(f"sid: {sid}, cid: {cid}, vid: {vid}")
                    appointment_date, step, cid, vendor = self.open_job_page(sid, cid, vid)

                    self.pick_job(appointment_date, step, cid, vendor, sid, vid)

                    self.get_jobs_info()
                    self.put_data_in_sheets()

    def find_first_empty_row(self, service, spreadsheet_id, range_name):
        log.debug("Start find_first_empty_row")
        """
        Находит первую пустую строку в указанном диапазоне.

        :param service: Объект Google Sheets API service
        :param spreadsheet_id: ID таблицы
        :param range_name: Диапазон, например, "Sheet1!B2:B"
        :return: Номер первой пустой строки
        """
        # Получаем данные из указанного диапазона
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        # Получаем существующие значения в диапазоне
        values = result.get("values", [])

        # Если данные пусты, первая строка будет первой в диапазоне
        if not values:
            return 2  # Первый индекс строки для B2

        # Проходим по данным, чтобы найти первую пустую строку
        for idx, row in enumerate(values, start=2):  # Стартуем с индекса 2 (для B2)
            if not row:  # Проверяем, пустая ли строка
                return idx

        # Если все строки заняты, возвращаем следующую после последней занятой
        return len(values) + 2  # Сдвигаем на 2, т.к. индекс начинается с B2

    def put_data_in_sheets(self):
        creds = self.get_google_token()
        try:
            service = build("sheets", "v4", credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            first_free_row = self.find_first_empty_row(service, SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME)
            for svo, svo_data in self.all_data.items():
                log.debug(f"first_free_row: {first_free_row}")
                row = self.preparing_row(svo_data)
                body = {
                    "values": [row]
                }

                target_range = f"A{first_free_row}:AE{first_free_row}"
                log.debug(f"target_range: {target_range}")
                # Вставить данные
                sheet.values().update(
                    spreadsheetId=SAMPLE_SPREADSHEET_ID,
                    range=target_range,
                    valueInputOption="RAW",
                    body=body
                ).execute()

                log.info(f"Данные успешно вставлены в строку {first_free_row}: {svo_data}")
                first_free_row += 1
                if not body['values']:
                    log.warn("No data found.")
                    return
        except HttpError as err:
            log.error(f"An error occurred: {err}")
            raise err

    def preparing_row(self, data: dict) -> list:
        log.debug("Start preparing_row")
        customer_data = data['customer_data']
        swo_data = data['swo_data']
        issue_data = data['issue_data']

        # Подготовка данных для вставки в строку
        row = [
            None,
            swo_data.get("claim_number", None),
            None,
            None,
            None,
            swo_data.get("appointment_date", None),
            swo_data.get("service_call_fee", None),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            issue_data.get("notes", None),
            issue_data.get("issue", None),
            issue_data.get("brand", None),
            issue_data.get("type", None),
            f'{datetime.today()}',
            swo_data.get("appointment_date", None),
            customer_data.get("name", ""),
            f"{customer_data.get('address', None)} {customer_data.get('city_state_zip', None)}",
            customer_data.get("phone", None)
        ]

        return row

    def get_google_token(self):
        log.debug("Start get_google_token")
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Сохраняем обновленные данные авторизации
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        return creds

    def get_jobs_info(self):
        log.debug("Start get_jobs_info")
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://relyhome.com',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }
        for svo, svo_data in self.rows_data.items():
            filtered_data = self.get_job_view(svo, svo['company'])
            data = {
                'claim_id': filtered_data['claim_id'],
                'cust_id': filtered_data['cust_id'],
                'zip': filtered_data['zip'],
                'company': svo_data['company'],
            }
            try:
                response = requests.post('https://relyhome.com/instructions/', cookies=self.cookies, headers=headers,
                                         data=data)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Извлечение данных о клиенте
                customer_info_div = soup.find('div', style=lambda x: x and 'Customer Information' in x)
                customer_lines = customer_info_div.get_text(separator="\n").strip().split("\n")
                customer_data = {
                    "name": customer_lines[1].strip(),
                    "address": customer_lines[2].strip(),
                    "city_state_zip": customer_lines[3].strip(),
                    "phone": customer_lines[4].replace("Phone:", "").strip(),
                    "email": customer_lines[5].replace("Email:", "").strip(),
                }

                # Извлечение данных о заявке
                swo_info_div = soup.find('div', style=lambda x: x and 'SWO Information' in x)
                swo_lines = swo_info_div.get_text(separator="\n").strip().split("\n")
                swo_data = {
                    "claim_number": swo_lines[1].split("-")[-1].strip(),
                    "service_call_fee": int(swo_lines[2].split("-")[-1].strip().split('$')[-1].split('.')[0]),
                    "authorization_limit": swo_lines[3].split("-")[-1].strip(),
                    "appointment_date": swo_lines[4].split("-")[-1].strip(),
                    "time_slot": swo_lines[5].split("-")[-1].strip(),
                }

                # Извлечение проблемы
                issue_paragraph = soup.find('p', text=lambda x: x and 'Issue:' in x).get_text(separator="\n")
                issue_lines = issue_paragraph.split("\n")
                issue_data = {
                    "issue": issue_lines[0].replace("Issue:", "").strip(),
                    "brand": issue_lines[1].replace("Brand:", "").strip(),
                    "type": issue_lines[2].replace("Type:", "").strip(),
                    "last_time_working": issue_lines[3].replace("Last Time Working:", "").strip(),
                    "notes": " ".join(issue_lines[5:]).replace("More Notes:", "").strip(),
                }
                self.all_data[svo] = {'customer_data': customer_data,
                                      'swo_data': swo_data,
                                      'issue_data': issue_data
                                      }
            except Exception as ex:
                log.error(ex)

    def get_job_view(self, svo, company):
        log.debug(f"Start get_job_view")
        params = {
            'claim_no': svo,
            'company': company,
        }
        try:
            response = requests.get('https://relyhome.com/jobs/view/', params=params, cookies=self.cookies,
                                    headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Поиск всех input элементов внутри формы
            form = soup.find('form')
            data = {input_tag['name']: input_tag['value'] for input_tag in form.find_all('input')}

            # Оставляем только нужные поля
            filtered_data = {key: data[key] for key in ['claim_id', 'cust_id', 'zip']}

            return filtered_data
        except Exception as ex:
            log.error(ex)

    def click_next_button(self):
        # Ожидание доступности кнопки "Next"
        next_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="DataTables_Table_0_next"]/a'))
        )
        next_button.click()
        # Обновляем HTML после перехода на новую страницу
        html = self.driver.page_source
        log.debug("Start get_page_data")
        self.get_page_data(html)
        log.debug("Finish get_page_data")
        time.sleep(5)

    def open_job_page(self, sid, cid, vid):
        log.debug('Start open_job_page')
        cookies = self.cookies

        params = {
            'sid': sid,
            'cid': cid,
            'vid': vid,
            'csrc': 'relyportal',
        }
        try:
            response = requests.get('https://relyhome.com/jobs/accept/offer.php', params=params, cookies=cookies,
                                    headers=self.headers)

            soup = BeautifulSoup(response.text, 'html.parser')
            step = soup.find('input', {'name': 'STEP'}).get('value')
            cid = soup.find('input', {'name': 'CID'}).get('value')
            vendor = soup.find('input', {'name': 'VENDOR'}).get('value')
            lists = soup.find_all(class_='list-group-item')
            # Инициализация списка для хранения данных
            appointment_data = []

            # Поиск всех элементов с классом list-group-item (один блок на каждый день)
            for item in lists:
                # Извлечение даты (текст внутри strong)
                date = item.find('strong').text.strip().split(',')[0].split(' ')[-1]
                day_of_date = int(re.search(r'\d+', date).group())
                if self.today < day_of_date <= self.today + 3:
                    # Поиск всех временных интервалов
                    for time_slot in item.find_all('div'):
                        # Извлечение времени и value
                        time_range = time_slot.label.text.strip()
                        value = time_slot.label.input['value']

                        # Добавление данных в список
                        appointment_data.append({
                            'date': day_of_date,
                            'time_range': time_range,
                            'value': value
                        })
                if len(appointment_data) == 0:
                    log.error(f"There is no available appointments")
                else:
                    return appointment_data[0], step, cid, vendor
        except Exception as ex:
            log.error(ex)

    def filter_correct_works(self):
        log.debug("Start filter_correct_works")
        sorted_dict = {
            key: value
            for key, value in sorted(self.rows_data.items(), key=lambda item: item[1]['sum_value'], reverse=True)
        }
        self.rows_data = sorted_dict

    def pick_job(self, appointment_date, step, cid, vendor, sid, vid):
        log.debug("Start pick_job")
        cookies = self.cookies
        log.debug(f"cookies: {cookies}")

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://relyhome.com',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
        }

        params = {
            'sid': sid,
            'cid': cid,
            'vid': vid,
            'csrc': 'relyportal',
        }

        data = {
            'ac': 'submit',
            'STEP': step,
            'CID': cid,
            'VENDOR': vendor,
            'CSRC': 'Rely Portal',
            'appttime': appointment_date['value'],
            'type': 'Accept SWO',
        }
        try:
            response = requests.post('https://relyhome.com/jobs/accept/offer.php', params=params, cookies=cookies,
                                     headers=headers, data=data)
            return response.text
        except Exception as ex:
            log.error(ex)

    def get_page_data(self, page_data):
        log.debug("Start get_page_data")
        soup = BeautifulSoup(page_data, "lxml")
        rows = soup.select('tbody tr')
        for row in rows:
            cells = row.find_all('td')
            svo_number, system, brand, location, city, zip_code, href, company = self.extract_page_data(cells)
            if city in CITIES_WITH_VALUE.keys() and system in SYSTEMS_WITH_VALUE.keys():
                self.rows_data[svo_number] = {'system': system,
                                              'brand': brand,
                                              'location': location,
                                              'city': city,
                                              'zip_code': zip_code,
                                              'sum_value': CITIES_WITH_VALUE[city] + SYSTEMS_WITH_VALUE[system],
                                              'href': href,
                                              'company': company
                                              }

    def extract_page_data(self, cells):
        log.debug("Start extract_page_data")
        extracted_data = []
        for td in cells:
            if td.find('a'):  # Проверяем наличие ссылки
                link = td.find('a')['href']
                extracted_data.append(link)
            elif td.find('span'):  # Проверяем наличие текста в span
                text = td.find('span').text.strip()
                extracted_data.append(text)
            else:  # В противном случае извлекаем текст из td
                text = td.text.strip()
                extracted_data.append(text)
        svo_number = extracted_data[0]
        system = extracted_data[1]
        brand = extracted_data[2]
        location = extracted_data[3]
        city = location.split(',')[0].strip()
        zip_code = location.split(' ')[-1].strip()
        href = extracted_data[6]
        company = extracted_data[5]
        return svo_number, system, brand, location, city, zip_code, href, company
