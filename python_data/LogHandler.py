from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.objects.log.obj import EventLog
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.filtering.log.attributes import attributes_filter
from IPython.display import display

import math

import pandas as pd

class LogHandler:
    frame_length = 100

    def __init__(self, log, mode: str, frame_length: int, dataframe=None):
        if frame_length:
            self.frame_length = frame_length
        if dataframe is not None:
            self.dataframe = dataframe

        if type(log) == pd.DataFrame:
            self.log = log_converter.apply(log, variant=log_converter.Variants.TO_EVENT_LOG)
        elif type(log) == EventLog:
            self.log = log
        self.mode = mode

    def variant_helper(self) -> pd.DataFrame:
        # print('In Handler', self.log, '\n', self.mode, '\n', self.frame_length, '\n', self.frame_length)
        # get variants of log
        variants = variants_filter.get_variants(self.log)
        # statistics to variants & sorting
        variants_count = case_statistics.get_variant_statistics(log=self.log)
        variants_count = sorted(variants_count, key=lambda x: x['count'], reverse=True)
        # variants as DataFrame - just first 100 entries
        variants_df = pd.DataFrame.from_records(variants_count).head(self.frame_length)
        variants_df['frequency'] = [math.log(i, 2) for i in variants_df['count']]
        variants_df['percentage'] = [(i/len(self.log))*100 for i in variants_df['count']]

        list_cum = []
        for idx in range(len(variants_df['percentage'])):
            if idx-1 >= 0:
                list_cum.append(variants_df['percentage'][idx] + list_cum[idx-1])
            else:
                list_cum.append(variants_df['percentage'][idx])
        variants_df['cum_percentage'] = list_cum
        return variants_df

    def apply(self, log = None, mode: str = '', frame_length: int = 0):
        if log:
            self.log = log
        if mode:
            self.mode = mode
        if frame_length:
            self.frame_length = frame_length
        match self.mode:
            case 'variant':
                return self.variant_helper()

    def groupby_func(self, row: int = 0, match_type: str = 'exact', display_df=False):
        """
        This function will generate a new DataFrame with additional columns,
        based on the dataframe with the most common value (of the variant col)
        :param row: of the filter variant
        :param match_type: used to filter for the exact activity, otherwise substrings allowed
        -> Inbound Email, Email Outbound => nearly all since substrings of Inbound Email AND Email Outbound allowed
        :return: DataFrame
        """
        variant_dataframe_native = self.variant_helper()

        filter_attribute = variant_dataframe_native['variant'][row]  # this is 'Inbound Call' - 0 vs 402


        tracefilter_log_pos = attributes_filter.apply(self.log, filter_attribute, parameters={
            attributes_filter.Parameters.ATTRIBUTE_KEY: "concept:name",
            attributes_filter.Parameters.POSITIVE: True})
        data_log = log_converter.apply(tracefilter_log_pos, variant=log_converter.Variants.TO_DATA_FRAME)


        """
        :type(dataframe) == dataframe

        Keyword arguments for .agg:
        https://pandas.pydata.org/docs/reference/api/pandas.core.groupby.DataFrameGroupBy.aggregate.html
        """

        variant_dataframe = data_log.groupby('case:concept:name').agg(
            activity=('concept:name', 'count'),
            activity_list=('concept:name', lambda x: ', '.join(x)),
            resource=('org:resource', 'nunique'),
            delta_start_time=('time:timestamp', lambda x: x.max() - x.min()),  # some sort of duration
        )

        col_name_new, col_name_old = 'duration', 'delta_start_time'

        # Sorts the dataframe due to the activity duration
        variant_dataframe[col_name_new] = [i.total_seconds() for i in variant_dataframe[col_name_old]]
        variant_dataframe = variant_dataframe.sort_values(['activity'], ascending=False)

        variant_dataframe['duration'] = [i.total_seconds() for i in variant_dataframe['delta_start_time']]
        variant_dataframe['caseID'] = variant_dataframe.index
        index_col = pd.Series([i for i in range(len(variant_dataframe.index))])
        variant_dataframe = variant_dataframe.set_index(index_col)

        dataframe_extended = variant_dataframe.groupby('activity_list').agg(
            avg_activity=('activity', 'mean'),
            cases=('caseID', 'nunique'),
            avg_resource=('resource', 'mean'),
            avg_duration=('duration', 'mean'),
            minimal_duration=('duration', 'min'),
            std_duration=('duration', 'std'),
        )

        # Sorts the dataframe due to the activity duration
        dataframe_extended['sum_duration'] = [dataframe_extended['avg_duration'][idx]*dataframe_extended['cases'][idx] for idx in range(len(dataframe_extended))]
        dataframe_extended = dataframe_extended.sort_values(['cases'], ascending=False)
        dataframe_extended['variant'] = dataframe_extended.index
        dataframe_extended = dataframe_extended.set_index(pd.Series([i for i in range(len(dataframe_extended.index))]))

        if match_type == 'exact':
            exact_variant = filter_attribute.replace(',', ', ')
            variant_dataframe = variant_dataframe.loc[variant_dataframe['activity_list'] == exact_variant]

        if display_df:
            print('#####\n#\t#\n#####\n'
                  'In the following the dataframes variant_dataframe and dataframe_extended '
                  'are displayed: ')
            pd.set_option("display.max_columns", 6)
            display(variant_dataframe_native)
            display(variant_dataframe)
            display(dataframe_extended)
        return variant_dataframe_native.head(self.frame_length), variant_dataframe.head(self.frame_length), dataframe_extended.head(self.frame_length)
