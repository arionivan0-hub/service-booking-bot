import logging

import gspread
from google.oauth2.service_account import Credentials

import config

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = ["Клиент", "Телефон", "Услуга", "Цена", "Дата", "Время", "Статус", "Создано"]


def _get_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_FILE, scopes=_SCOPES
    )
    return gspread.authorize(creds)


def _get_sheet() -> gspread.Worksheet:
    client = _get_client()
    spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)
    return spreadsheet.sheet1


def ensure_headers() -> None:
    try:
        sheet = _get_sheet()
        existing = sheet.row_values(1)
        if existing != HEADERS:
            sheet.clear()
            sheet.append_row(HEADERS, value_input_option="RAW")
    except Exception as e:
        logger.warning("Could not ensure Google Sheets headers: %s", e)


def add_appointment_row(
    client_name: str,
    phone: str,
    service_name: str,
    price: float,
    date: str,
    time_slot: str,
) -> bool:
    try:
        sheet = _get_sheet()
        from datetime import datetime

        row = [
            client_name,
            phone,
            service_name,
            int(price),
            date,
            time_slot,
            "active",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ]
        sheet.append_row(row, value_input_option="RAW")
        logger.info("Row added to Google Sheets: %s %s", client_name, date)
        return True
    except Exception as e:
        logger.error("Failed to add row to Google Sheets: %s", e)
        return False


def update_appointment_status(date: str, time_slot: str, status: str) -> bool:
    try:
        sheet = _get_sheet()
        all_rows = sheet.get_all_records()
        for i, row in enumerate(all_rows, start=2):
            if str(row.get("Дата")) == date and str(row.get("Время")) == time_slot:
                status_col = HEADERS.index("Статус") + 1
                sheet.update_cell(i, status_col, status)
                return True
        return False
    except Exception as e:
        logger.error("Failed to update Google Sheets: %s", e)
        return False
