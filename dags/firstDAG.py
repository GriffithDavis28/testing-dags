from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

def push_state(**kwargs):
    state = {'step': 'data_fetched', 'status': 'success'},
    kwargs['ti'].xcom_push(key='state', value=state)


def pull_and_log(**kwargs):
    state = kwargs['ti'].xcom_pull(key='state', task_ids='get_state')
    print(f'State of dag is: {state}')

default_args = {
    'owner': 'ariflow',
    'retires': 5,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='status_dag_1',
    default_args=default_args,
    description='Checking stats',
    schedule_interval=None
) as dag:
    task1 = PythonOperator(
        task_id='get_state',
        python_callable=push_state,
        provide_context=True
    )

    task2 = PythonOperator(
        task_id='read_state',
        python_callable=pull_and_log,
        provide_context=True
    )


    task1>>task2

    