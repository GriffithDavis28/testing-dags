def fecth_data(dag_id, **kwargs):
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

        select_query= """SELECT dag_id, state FROM task_instance WHERE dag_id=%s AND state='skipped';"""

        cursor.execute(select_query, (dag_id,))

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
