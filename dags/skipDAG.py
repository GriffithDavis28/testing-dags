import logging
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from datetime import datetime, timedelta
from airflow.operators.empty import EmptyOperator
from airflow.models.dagrun import DagRun
from airflow.utils.state import State
from config.dbConfig import db_connection_config


skips_allowed = 3

logging.basicConfig(level=logging.INFO)

default_args = {
    'owner': 'airflow',
    'retries': 5,
    'retry_delay': timedelta()
}

dag = DAG(
    dag_id='skip_dag_v2',
    schedule_interval=timedelta(minutes=5),
    start_date=datetime.now(),
    default_args=default_args
)

start = EmptyOperator(
    task_id='start'
)

end = EmptyOperator(
    task_id='end'
)


def check_prev_dag(dag_id, **kwargs):
    DAG_RUN = DagRun.find(dag_id, state=State.FAILED)

    if DAG_RUN:
        return 'skipped_run'
    else:
        return 'check_status'
    

def store_skipped_state(dag_id, **kwargs):

    logging.info("Storing state")

    try:
        conn = psycopg2.connect(
            host=db_connection_config["host"],
            port=db_connection_config["port"],
            user=db_connection_config["username"],
            password=db_connection_config["password"],
            database=db_connection_config["database"]
        )

        cursor = conn.cursor()

        select_query = f"""
            SELECT task_id, state FROM public.task_instance WHERE dag_id='{dag.dag_id}' AND state='skipped';           
        """
        cursor.execute(select_query)

        rows = cursor.fetchall()

        logging.info(f'incoming data: {rows}')

        logging.info(f'incoming data: {len(rows)}')

        for row in rows:

            check_record = """
                SELECT COUNT(*) from public.skipped_data WHERE dag_id=%s AND task_id=%s;
            """
            cursor.execute(check_record, (dag_id, row[0]))
            count= cursor.fetchone()[0]
            logging.info('checking if record already exists....')
            logging.info(f'{count}')

            if count==0:
                insert_query = """
                    INSERT INTO public.skipped_data (dag_id, task_id, state, "timestamp", skip_count, skips_allowed) VALUES(%s, %s, %s, %s, %s, %s);
                """
                cursor.execute(insert_query, (dag_id, row[0], row[1], datetime.now(), 1, skips_allowed))

                logging.info(f'new data: {row}')
            else:
                logging.info('Record already exists, pushing data to update_skip_count method...')
                update_skip_count(dag_id=dag_id, task_id=row[0], conn=conn, cursor=cursor)
        

        conn.commit()
        cursor.close()
        conn.close()

        logging.info("Stored successfully....")

    except Exception as e:
        logging.error(f'Something happened....{e}')



def update_skip_count(dag_id, task_id=None, conn=None, cursor=None, **kwargs):
    
    logging.info("Updating skip_count fucntion is being run...")

    try:
        conn = psycopg2.connect(
            host=db_connection_config["host"],
            port=db_connection_config["port"],
            user=db_connection_config["username"],
            password=db_connection_config["password"],
            database=db_connection_config["database"]
        )

        cursor = conn.cursor()

        select_query=f"""
            SELECT task_id, skip_count FROM public.skipped_data WHERE dag_id='{dag.dag_id}' and state='skipped';
        """

        cursor.execute(select_query, (dag_id,))
        logging.info('Getting the task_id and skip_count from skipped table....')
        
        skipped_tasks=cursor.fetchall()

        logging.info(skipped_tasks[0])

        for task_id, skip_count in skipped_tasks:
            logging.info(f'task_id = {task_id} and skip_count = {skip_count}')
            new_skip_count = skip_count+1

            logging.info(f'updated skip count = {new_skip_count}')

            update_query=f"""
                UPDATE public.skipped_data SET skip_count = , timestamp = %s WHERE dag_id=%s AND task_id = %s;
            """
            cursor.execute(update_query, (new_skip_count, datetime.now(), dag_id, task_id))



            if new_skip_count ==skips_allowed:
                with open('error_log.txt', 'w') as file:
                    file.write(f'Dag {dag.dag_id} and task {task_id} has skipped {skip_count} times consecutively!!!')


        logging.info("Skip count updated successfully....")
    except Exception as e:
        logging.error(f'Something happened while updating the skip count function....{e}')

def printStatus(**kwargs):
    logging.info('Status: checking status...')


def skippedState(**kwargs):
    logging.info('Status: skipped...')


check_prev_status = BranchPythonOperator(
    task_id='check_prev_status',
    python_callable=check_prev_dag,
    op_kwargs={
        'dag_id': '{dag.dag_id}'
    },
    dag=dag
)

check_status = PythonOperator(
    task_id='check_status',
    python_callable=printStatus,
    dag=dag
)


skip_status = PythonOperator(
    task_id='skipped_run',
    python_callable=skippedState,
    # op_kwargs={
    #     'dag_id': dag.dag_id,
    #     'task_id': 'skipped_run_status'
    # },
    dag=dag
)


store_data = PythonOperator(
    task_id='storing_data',
    python_callable=store_skipped_state,
    op_kwargs={
        'dag_id': '{{dag.dag_id}}'
    },
    dag=dag
)

skip_update = PythonOperator(
    task_id='update_count',
    python_callable=update_skip_count,
    op_kwargs={
        'dag_id': '{{dag.dag_id}}'
    },
    dag=dag
)


start >> check_prev_status >> [check_status, skip_status]
check_status >> store_data
store_data >> skip_update
skip_update >> end