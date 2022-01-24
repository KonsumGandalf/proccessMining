import pandas as pd
import os

import pm4py
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter

"""
Importing all filtering functions
"""
from pm4py.algo.filtering.log.timestamp import timestamp_filter
from pm4py.algo.filtering.log.cases import case_filter
from pm4py.algo.filtering.log.start_activities import start_activities_filter

"""
Declaration of used data files
"""
PATH_EXAM = '../src/data/exam_data'
PATH_COURSE = '../src/data/PM-Regensburg'
FILE_NAME = 'scenario1_DepL.csv'
OUTPUT_PATH = '../src/data/output'

"""
As I just will need to import CSV not XES Files for the process mining seminar ill just apply this
@:var log_csv - dataframe 
"""
FILE_PATH = os.path.join(PATH_COURSE, 'CCex2', FILE_NAME)
log_csv = pd.read_csv(FILE_PATH, sep=',')
log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
# setting column names to default pm4py terms -> later less code
log_csv.rename(columns={'timestamp': 'time:timestamp', 'case': 'case:concept:name', 'activity': 'concept:name',
                        'resource': 'org:resource'}, inplace=True)
log_attribute = 'concept:name'
log_csv = log_csv.sort_values('time:timestamp')

parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: log_attribute}
event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
event_log = timestamp_filter.filter_traces_contained(event_log, "2020-06-05 01:00:00", "2020-07-05 08:59:59")


def filter_helper(log, mode: int):
    """
    @:param event_log log: Used data
    @:param int mode: The mode presents which of the filtering methods are applied
    """
    match mode:
        case 1: return timestamp_filter.filter_traces_contained(event_log, "2020-06-05 01:00:00", "2020-07-05 08:59:59")
        case 2: return case_filter.filter_case_performance(log, 86400, 86400*60)
        case 3:
            # Here a specific list is used which determines the starting_options
            filter_list = ['Activity P', 'Activity A']
            print(start_activities_filter.get_start_activities(log))
            return start_activities_filter.apply(log, filter_list)
        case 4:
            """
            @:parameter DECREASING_FACTOR: percentage of Activity occurring
            --> 700/1000 = 0.7
            --> 400/1000 = 0.4
            """
            filter_list_any = start_activities_filter.get_start_activities(
                log, parameters={start_activities_filter.Parameters.DECREASING_FACTOR: 1.1})
            filter_list = []
            for f in filter_list_any:
               filter_list.append(f[0])
            print(filter_list_any)
            return start_activities_filter.apply(log, filter_list)
    print(f"Wrong value of mode {mode} min is 1, max 3\n Error is passed no filter applied")
    return log

event_log = filter_helper(event_log, 4)

for event in event_log:
    print(event)

"""
DATAFRAME_PATH = os.path.join(OUTPUT_PATH, 'test1')
dataframe = log_converter.apply(event_log, variant=log_converter.Variants.TO_DATA_FRAME)
dataframe.to_csv(DATAFRAME_PATH)
"""
