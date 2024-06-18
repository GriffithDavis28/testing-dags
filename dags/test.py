import psycopg2
import logging
from config.dbConfig import db_connection_config

def connect_to_db():
    logging.info("Establising connection in connect_to_db method...")
    
    try:
        conn = psycopg2.connect(
            host=db_connection_config["host"],
            port=db_connection_config["port"],
            user=db_connection_config["username"],
            password=db_connection_config["password"],
            database=db_connection_config["database"]
        )

        logging.info("Connection established")
        print("Connected")
    except Exception as e:
        logging.error(f'Something went wrong. -->>  {e}')


if __name__=="__main__":
    connect_to_db()