import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
import json
import pprint

import logging
logging.basicConfig(
    level=logging.INFO,
    filename='parsing_logging.log',
    format='%(asctime)s -,- %(levelname)s -,- %(name)s -,- %(message)s',
    filemode="a",
)


def initiate_sheets_service():
    CREDENTIALS_FILE = 'coastal-volt-384406-717099073bb9.json'
    # Read data from json file
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE,
                                                                   ['https://www.googleapis.com/auth/spreadsheets'])
    httpAuth = credentials.authorize(httplib2.Http())  # Authorization in system
    # Create service (goggle spreadsheets of 4 version API
    return apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def create_sheet(service_sheets, spreadsheet_id, sheet_title):
    body = {'requests': [
    {
        'addSheet':{
            'properties':{'title': sheet_title}
        }
    }
    ]}
    try:
        res = service_sheets.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        SHEET_ID = res['replies'][0]['addSheet']['properties']['sheetId']
        return SHEET_ID
    except Exception as err:
        return None


def read_from_sheet(service_sheets, spreadsheet_id, sheet_name):
    resp = service_sheets.spreadsheets().values().batchGet(spreadsheetId=spreadsheet_id,
                                                           ranges=[f"{sheet_name}!A1:G500"]).execute()
    return resp['valueRanges'][0]['values']


def create_header(service_sheets, spreadsheet_id,  sheet_name):

    ranges = [f"{sheet_name}!A1:G1", f"{sheet_name}!A2:G2"]

    values = [[sheet_name],
              ["Дата", "Ротация", "НР", "Место в НР", "Кол-во оценивших команд", "кол-во отзывов", "Рейтинг"]]

    # Define the request body to input values to the ranges.
    request_body = {
        "valueInputOption": "USER_ENTERED",  # Input values as user-entered strings.
        "data": []
    }

    # Iterate over the ranges and input values to each range.
    for i, range_name in enumerate(ranges):
        request_body["data"].append({
            "range": range_name,
            "majorDimension": "ROWS",  # Input values row by row.
            "values": [values[i]]
        })

    resp = service_sheets.spreadsheets().values().batchUpdate(
                          spreadsheetId=spreadsheet_id,
                          body=request_body).execute()

    spreadsheet = service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    sheet_id = None
    for _sheet in spreadsheet['sheets']:
        if _sheet['properties']['title'] == sheet_name:
            sheet_id = _sheet['properties']['sheetId']

    body = {
        "requests": [
            {'updateBorders': {'range': {'sheetId': sheet_id,
                             'startRowIndex': 1,
                             'endRowIndex': 2,
                             'startColumnIndex': 0,
                             'endColumnIndex': 7},
                   'bottom': {
                   # Задаем стиль для верхней границы
                              'style': 'SOLID', # Сплошная линия
                              'width': 2,       # Шириной 2 пикселя
                              'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}}, # Черный цвет
                   'top': {
                   # Задаем стиль для нижней границы
                              'style': 'SOLID',
                              'width': 2,
                              'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                   'left': { # Задаем стиль для левой границы
                              'style': 'SOLID',
                              'width': 2,
                              'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                   'right': {
                   # Задаем стиль для правой границы
                              'style': 'SOLID',
                              'width': 2,
                              'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                   'innerHorizontal': {
                   # Задаем стиль для внутренних горизонтальных линий
                              'style': 'SOLID',
                              'width': 1,
                              'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}},
                   'innerVertical': {
                   # Задаем стиль для внутренних вертикальных линий
                              'style': 'SOLID',
                              'width': 1,
                              'color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 1}}
                             }
             },
            {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "endRowIndex": 2,
                    "startColumnIndex": 0,
                    "endColumnIndex": 7
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER"  # Set horizontal alignment to center.
                    }
                },
                "fields": "userEnteredFormat.horizontalAlignment"  # Update the horizontal alignment field.
            }
        },
        {"repeatCell": {"range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 7
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER"  # Set horizontal alignment to center.
                    }
                },
                "fields": "userEnteredFormat.horizontalAlignment"  # Update the horizontal alignment field.
            }
        },
        {
        "mergeCells": {"range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 7
                },
                "mergeType": "MERGE_ALL"  # Merge all cells in the range.
            }
        },
        ]
    }

    results = service_sheets.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id,
                                                        body=body).execute()


def create_record(service_sheets, spreadsheet_id,  sheet_name, payload):
    current_page_content = (read_from_sheet(service_sheets, spreadsheet_id, sheet_name))
    last_row = len(current_page_content)
    if last_row > 1:
        last_date = current_page_content[-1][0]
        if payload['date'] != last_date:
            body = {
            'valueInputOption': 'RAW',
            'data': [
                {'range': f'{sheet_name}!A{last_row+1}:G{last_row+1}', 'values': [
                    [payload['date'],
                     payload['rotation'],
                     payload['NR'],
                     payload['place in NR'],
                     payload['number teams'],
                     payload['number comment'],
                     payload['avg mark'],
                     ],
                ]},
                ]
            }
            results = service_sheets.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id,
                                                                         body=body).execute()




if __name__ == '__main__':
    service_sheets = initiate_sheets_service()
    spreadsheet_id = '1dzjzPZh7jTuO69yZCnPi4wwprkDcKJRsEa9gUBCVBd8'
    create_sheet(service_sheets=service_sheets,
                 spreadsheet_id=spreadsheet_id,
                 sheet_title='Foo bar')