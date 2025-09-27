import commonfunctions as cf
from file_list_config import file_list_config


directory = 'datafiles/latestresults'
table_name='latest_results'


#cf.load_csvs_to_mysql(directory,table_name)
fn=['datafiles/latest-results.csv']
cf.copy_files(fn,None,file_list_config)

