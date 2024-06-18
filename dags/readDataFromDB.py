import logging
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from config.dbConfig import db_connection_config
from datetime import datetime, timedelta


default_args = {
    'owner':'airflow',
    'retires':5,
    'retry_delay':timedelta(minutes=3)
}

def fecth_data():
    logging.info("Establising connection in connect_to_db method...")
    
    try:
        conn = psycopg2.connect(
            host=db_connection_config["host"],
            port=db_connection_config["port"],
            user=db_connection_config["username"],
            password=db_connection_config["password"],
            database=db_connection_config["database"]
        )

        cursor = conn.cursor()

        select_query= """SELECT * FROM task_instance;"""

        cursor.execute(select_query)

        rows = cursor.fetchall()

        for row in rows:
            logging.info(row)
            print(f'Data: {row}')

        conn.commit()
        cursor.close()
        conn.close()


        logging.info("Connection established")
    except Exception as e:
        logging.error(f'Something went wrong. -->>  {e}')

dag=DAG(
    dag_id="testing",
    start_date=datetime.now(),
    schedule_interval=timedelta(minutes=2),
    default_args=default_args
)


start = EmptyOperator(
    task_id="start"
)

end = EmptyOperator(
    task_id="end"
)

fetch = PythonOperator(
    task_id='fetching_data',
    python_callable=fecth_data,
    dag=dag
)

start >> fetch >> end