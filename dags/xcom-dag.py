from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

import requests
import json

url = 'https://covidtracking.com/api/v1/states/'
state = 'wa'

def get_testing_increase(state, ti):
    """
    Gets totalTestResultsIncrease field from Covid API for given state and returns value
    """
    res = requests.get(url+'{0}/current.json'.format(state))
    testing_increase = json.loads(res.text)['totalTestResultsIncrease']
    # xcom_push() method to specify a key name, 
    ti.xcom_push(key='testing_increase', value=testing_increase) 
    
    # alternatively we could have returned testing_increase
    # return testing_increase
    # ti.xcom_push(key='returned_value', value=testing_increase) 
    


def analyze_testing_increases(state, ti):
    """
    Evaluates testing increase results 
    """
    # xcom pull method. Soecify "key" and task_ids associated with
    # xcom we want to retrieve. Any xcom or even multiple xcoms is possible
    # it does not need to be from a task immediately prior
    testing_increases=ti.xcom_pull(key='testing_increase', task_ids='get_testing_increase_data_{0}'.format(state))
    print('Testing increases for {0}:'.format(state), testing_increases)
    #run some analysis here


# Default settings applied to all tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

#current day covid increase data
# with is the within a context manager
with DAG('xcom_dag',
         start_date=datetime(2021, 1, 1),
         max_active_runs=2,
         schedule_interval=timedelta(minutes=30),
         default_args=default_args,
         catchup=False
         ) as dag:
    # This code is running inside a context
    opr_get_covid_data = PythonOperator(
        task_id = 'get_testing_increase_data_{0}'.format(state),
        python_callable=get_testing_increase,
        op_kwargs={'state':state}
    )

    opr_analyze_testing_data = PythonOperator(
        task_id = 'analyze_data',
        python_callable=analyze_testing_increases,
        op_kwargs={'state':state}
    )

    opr_get_covid_data >> opr_analyze_testing_data