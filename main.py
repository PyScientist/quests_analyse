import datetime
from parse_quests import parsing_process
from google_sheets_api import initiate_sheets_service, \
                              create_sheet, \
                              create_header, \
                              create_record

import logging
logging.basicConfig(
    level=logging.INFO,
    filename='parsing_logging.log',
    format='%(asctime)s -,- %(levelname)s -,- %(name)s -,- %(message)s',
    filemode="a",
)


def current_date():
    return datetime.datetime.now().strftime('%d.%m.%Y')


def create_sheets_if_not_exists(service_sheets, spreadsheet_id, sheet_names) -> None:
    spreadsheet = service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets_titles = [x['properties']['title'] for x in spreadsheet['sheets']]
    for name in sheet_names:
        if name not in sheets_titles:
            creation_result = create_sheet(spreadsheet_id=spreadsheet_id,
                                           service_sheets=service_sheets,
                                           sheet_title=name)
            if creation_result is not None:
                create_header(spreadsheet_id=spreadsheet_id,
                              service_sheets=service_sheets,
                              sheet_name=name)


def prepare_data_to_load(record) -> dict:
    """Preparation of data for farther loading to the sheet
    :param record: record from quest list
    :return: dictionary with data to input"""
    try:
        data_to_load = {
                        'name': record['quest_name'],
                        'date': current_date(),
                        'rotation': record['main_page_position'],
                        'NR': record['people_rating'],
                        'place in NR': record['id_people_rating'],
                        'number teams': record['teams_ammount_for_rating'],
                        'number comment': record['ammount_of_votes'],
                        'avg mark': record['avg_mark'],
                        }
        return data_to_load
    except KeyError as key_err:
        logging.error(f'Some issue rise during data preparation for single record')
        logging.error(key_err, exc_info=False)
        return {}


def paste_records(service_sheets_in, spreadsheet_id_in, data_in) -> None:
    """Function to paste data into spreadsheet
    :param service_sheets_in: service to interact with Google spreadsheets
    :param spreadsheet_id_in: id of spreadsheet to work with
    :param data_in: list of dictionaries with parsed quests details"""
    try:
        spreadsheet = service_sheets_in.spreadsheets().get(spreadsheetId=spreadsheet_id_in).execute()
        sheets_titles = [x['properties']['title'] for x in spreadsheet['sheets']]
        for i in range(len(data_in)):
            try:
                if data_in[i]['quest_name'] in sheets_titles:
                    create_record(service_sheets=service_sheets_in,
                                  spreadsheet_id=spreadsheet_id_in,
                                  sheet_name=data_in[i]['quest_name'],
                                  payload=prepare_data_to_load(data_in[i]))
            except Exception as single_record_error:
                logging.critical(f'Some error occurred during pasting records in general')
                logging.critical(single_record_error, exc_info=False)
    except Exception as general_error:
        logging.critical('Some error occurred during pasting records in general')
        logging.critical(general_error, exc_info=False)


if __name__ == '__main__':
    service_sheets = initiate_sheets_service()
    spreadsheet_id = '1dzjzPZh7jTuO69yZCnPi4wwprkDcKJRsEa9gUBCVBd8'

    list_of_goal_quest_details = parsing_process()

    data = test_data

    create_sheets_if_not_exists(service_sheets=service_sheets,
                                spreadsheet_id=spreadsheet_id,
                                sheet_names=[item['quest_name'] for item in data])

    paste_records(service_sheets=service_sheets,
                  spreadsheet_id=spreadsheet_id,
                  data=data)

