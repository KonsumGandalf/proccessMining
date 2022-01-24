import pm4py
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter

from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter

from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.statistics.traces.generic.log import case_arrival

from python_data.DataIO import EventHandler
from python_data.PresentHandler import PltPresent, COMPARE

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.stats import pareto
import os

"""
Path declaration
"""

PATH_EXAM = '../../../src/data/exam_data'
PATH_COURSE = '../../../src/data/PM-Regensburg'
FILE_NAME = 'CallCenterLog.csv'
OUTPUT_PATH = '../../../src/data/output'
FILE_PATH = os.path.join(PATH_COURSE, FILE_NAME)


def prepare_data():
    log_csv = pd.read_csv(FILE_PATH, sep=',')
    log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
    log_csv.rename(
        columns={'Case ID': 'case:concept:name', 'Start Date': 'start_timestamp', 'End Date': 'time:timestamp',
                 'Activity': 'concept:name', 'Resource': 'org:resource'}, inplace=True)
    log_csv = log_csv.sort_values('start_timestamp')
    log_attribute = 'case:concept:name'
    parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: log_attribute}
    event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
    return event_log


def log_dealer(log, mode, frame_length=100):
    match mode:
        case 'variant':
            # get variants of log
            variants = variants_filter.get_variants(log)
            # statistics to variants & sorting
            variants_count = case_statistics.get_variant_statistics(log=log)
            variants_count = sorted(variants_count, key=lambda x: x['count'], reverse=True)
            # variants as DataFrame - just first 100 entries
            variants_df = pd.DataFrame.from_records(variants_count).head(frame_length)
            variants_df['frequency'] = [math.log(i, 2) for i in variants_df['count']]
            return variants_df


def present_dealer(dataframe, mode_list=['nothing'], col1='', col2='', title='', x_label='', y_label='',frame_length=100):
    dataframe = dataframe.head(frame_length)
    data = dataframe[col1]
    #if col1 != '': data = dataframe[col1]
    color_list = ['blue', 'green', 'red', 'cyan',
                  'magenta', 'yellow', 'black', 'white']

    def histogram_dealer():
        plt.figure(figsize=(15, 5))
        data_index = [str(e).replace("Case ","") for e in dataframe.index] if col2 == 'index_format' else data.index
        COMPARE.append(data_index)
        plt.bar(data_index, data, color=color_list[0], width=0.4)
        plt.xlabel(x_label), plt.ylabel(y_label), plt.title(title)
        plt.show()

    def histogram_analyser():
        count, bins_count = np.histogram(data, bins=50)

        # Probability distribution function = PDF
        # Cumulative distribution function = CDF
        pdf = count / sum(count)
        cdf = np.cumsum(pdf)

        plt.plot(bins_count[1:], pdf, color=color_list[0], label="PDF")
        plt.plot(bins_count[1:], cdf, color=color_list[1], label="CDF")
        # plt.plot(bins_count[1:], count, color=color_list[2], label="count")
        plt.legend()
        plt.show()

    def pandas_full_presentation():
        with pd.option_context('display.max_rows', 10, 'display.max_columns', None, 'display.width', None):
            print(dataframe)

    for mode in mode_list:
        match mode:
            case 'histogram':
                histogram_dealer()
            case 'cdf':
                histogram_analyser()
            case 'terminal':
                pandas_full_presentation()
            case 'full':
                histogram_dealer()
                histogram_analyser()
                pandas_full_presentation()
            case _:
                print('Mode nothing has been chosen!')


def groupby_func(log, dataframe, row: int = 0, match_type: str = 'exact'):
    """
    This function will generate a new DataFrame with additional columns,
    based on the dataframe with the most common value (of the variant col)
    :param log:
    :param dataframe:
    :param row: of the filter variant
    :param match_type: used to filter for the exact activity, otherwise substrings allowed
    -> Inbound Email, Email Outbound => nearly all since substrings of Inbound Email AND Email Outbound allowed
    :return: DataFrame
    """
    filter_attribute = dataframe['variant'][row]  # this is 'Inbound Call' - 0 vs 402
    tracefilter_log_pos = attributes_filter.apply(log, filter_attribute, parameters={
        attributes_filter.Parameters.ATTRIBUTE_KEY: "concept:name",
        attributes_filter.Parameters.POSITIVE: True})
    data_log = log_converter.apply(tracefilter_log_pos, variant=log_converter.Variants.TO_DATA_FRAME)

    """
    :type(dataframe) == dataframe
    
    Keyword arguments for .agg:
    https://pandas.pydata.org/docs/reference/api/pandas.core.groupby.DataFrameGroupBy.aggregate.html
    """

    dataframe = data_log.groupby('case:concept:name').agg(
        activity=('concept:name', 'count'),
        activity_list=('concept:name', lambda x: ', '.join(x)),
        resource=('org:resource', 'nunique'),
        delta_start_time=('start_timestamp', lambda x: x.max() - x.min()),  # some sort of duration
    )
    col_name_new, col_name_old = 'duration', 'delta_start_time'

    # Sorts the dataframe due to the activity duration
    dataframe[col_name_new] = [i.total_seconds() for i in dataframe[col_name_old]]
    dataframe = dataframe.sort_values([col_name_new], ascending=False)

    dataframe['duration'] = [i.total_seconds() for i in dataframe['delta_start_time']]
    dataframe['caseID'] = dataframe.index

    dataframe_extended = dataframe.groupby('activity_list').agg(
        avg_activity=('activity', 'mean'),
        cases=('caseID', 'nunique'),
        avg_resource=('resource', 'mean'),
        avg_duration=('duration', 'mean'),
        minimal_duration=('duration', 'min'),
        std_duration=('duration', 'std'),
    )

    # Sorts the dataframe due to the activity duration
    dataframe_extended = dataframe_extended.sort_values(['avg_duration'], ascending=False)

    if match_type == 'exact':
        exact_variant = filter_attribute.replace(',', ', ')
        dataframe = dataframe.loc[dataframe['activity_list'] == exact_variant]

    return dataframe, dataframe_extended



FRAME_LENGTH = 100
FILE_NAME = 'CallCenterLog.csv'
EVENT_LOG = prepare_data()

variant_dataframe = log_dealer(EVENT_LOG, 'variant', FRAME_LENGTH)
present_dealer(variant_dataframe, ['histogram', 'cdf', 'terminal'] , 'frequency', 'count', 'Test_Hist', 'variant', 'count'
               , frame_length=FRAME_LENGTH)

list_updated_dataframe = groupby_func(EVENT_LOG, variant_dataframe, 1, 'unexact')
P1 = PltPresent(list_updated_dataframe[1], ['histogram', 'cdf', 'terminal'], 'avg_duration',
               'bar chart of variants average duration', 'index_format', 'average duration', 'activity', frame_length=FRAME_LENGTH)
present_dealer(list_updated_dataframe[1], ['histogram', 'cdf', 'terminal'], 'avg_duration',
               'bar chart of variants average duration', 'index_format', 'average duration', 'activity', frame_length=FRAME_LENGTH)

P1.apply()
