import os
from datetime import datetime, timedelta
import pandas as pd
import configparser
from yahoo_fin.stock_info import get_data
from pgdb import PGDatabase

config = configparser.ConfigParser()
config.read("config.ini")
SALES_PATH = config["Files"]["SALES_path"]
COMPANIES = eval(config["Companies"]["COMPANIES"])
DATABASE_CREDS = config["Database"]
 
sales_df = pd.DataFrame()  # create empty df
if os.path.exists(SALES_PATH):
    sales_df = pd.read_csv(SALES_PATH)
    print(sales_df)
    # os.remove(SALES_PATH)

historical_data = {}

# Получаем данные для каждой компании
for company in COMPANIES:
    # Определяем даты
    if datetime.today().weekday() == 0:  # Если сегодня понедельник
        start_date = (datetime.today() - timedelta(days=3)).strftime(
            "%Y-%m-%d"
        )  # Пятница
    else:
        start_date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    end_date = datetime.today().strftime("%Y-%m-%d")

    # Получаем данные
    try:
        historical_data[company] = get_data(
            company, start_date=start_date, end_date=end_date
        ).reset_index()

        # Проверяем, есть ли данные
        if historical_data[company].empty:
            print(
                f"Нет данных для компании {company} за период с {start_date} по {end_date}."
            )
        else:
            print(f"Данные для компании {company} успешно загружены:")
            print(historical_data[company])
    except Exception as e:
        print(f"Ошибка при загрузке данных для компании {company}: {e}")

database = PGDatabase(
    host=DATABASE_CREDS["HOST"],
    database=DATABASE_CREDS["DATABASE"],
    user=DATABASE_CREDS["USER"],
    password=DATABASE_CREDS["PASSWORD"],
)


for i, row in sales_df.iterrows():
    query = f"insert into sales values ('{row['dt']}', '{row['com']}', '{row['transaction_type']}', {row['amount']} )"  # числа без кавычек в {row}
    print(query)
    database.post(query)

for company, data in historical_data.items():
    for i, row in data.iterrows():
        query = f"insert into stock values ('{row['index']}', '{row['ticker']}',  {row['open']} , {row['close']} )"
        database.post(query)
