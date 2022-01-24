import pandas as pd
from IPython.display import display
from pm4py.algo.discovery.heuristics import algorithm as heuristic_miner
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.objects.conversion.log import converter as log_converter

from python_data.DataIO import EventHandler
from python_data.FilterHandler import FilterHelper
from python_data.LogHandler import LogHandler
from python_data.Pm4pyHandler import Pm4pyHandler
from python_data.PresentHandler import PltPresent

"""
Path declaration
"""


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

    if type(log) == pd.DataFrame:
        log = log_converter.apply(log, variant=log_converter.Variants.TO_EVENT_LOG)

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
    index_col = pd.Series([i for i in range(len(dataframe.index))])
    dataframe = dataframe.set_index(index_col)

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


def main():
    def plt_component_use():
        LogHandler1 = LogHandler(EVENT_LOG, 'variant', FRAME_LENGTH)
        variant_dataframe = LogHandler1.apply()
        list_updated_dataframe = groupby_func(EVENT_LOG, variant_dataframe, 1, 'unexact')

        PresentationHandler1 = PltPresent(data=variant_dataframe, mode_list=['plt'], col1='variant', col2='frequency',
                                          title='bar chart of variants frequency', x_label='variant', y_label='count'
                                          , frame_length=FRAME_LENGTH)
        PresentationHandler1.apply()

        display(list_updated_dataframe)

        # difference to his diagram he forgets to use frame_length => lost dimension
        PresentationHandler2 = PltPresent(list_updated_dataframe[0], mode_list=['plt'], col1='index_format',
                                          col2='duration',
                                          title='bar chart of variants average duration', x_label='cases',
                                          y_label='duration',
                                          frame_length=400)
        PresentationHandler2.apply()

        PresentationHandler3 = PltPresent(list_updated_dataframe[1], mode_list=['plt'], col1='index_format',
                                          col2='avg_duration',
                                          title='bar chart of variants average duration', x_label='cases',
                                          y_label='avg_duration',
                                          frame_length=FRAME_LENGTH)
        PresentationHandler3.apply()

    def pm_component_use_1():
        """
        This is the part which uses the default log :
        CallCenterLog.csv

        heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: Defines the Activity
        :return:
        """

        pmHandler.update_parameters({heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.6,
                                     heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 30,
                                     heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 30},
                                    replace=True)

        """
        Inductive_processing: Variant IM vs IMf vs IMd of 
        """
        variant_list = ['IM', 'IMf', 'IMd']
        for var in variant_list:
            p_tree = pmHandler.inductive_processing(mode_detail='process_tree', variant=var)
            gviz = pmHandler.inductive_visualization(p_tree)
            pmHandler.save_file(gviz, filename=f'{var}', session_dir=SESSION_DIR, add_dir='Inductive_processing')

        """
        Inductive_processing: Petri net == Petri net out of a process tree  
        """
        pmHandler.petri_net_visualization(pmHandler.inductive_processing('petri_net'))
        pmHandler.petri_net_visualization(
            pmHandler.inductive_processing(mode_detail='convert', tree=pmHandler.inductive_processing('process_tree')))

        """
        Heuristic_processing: petri_net vs heuristic_net
        heuristic nets cant be saved!
        """
        heu_petri_net = pmHandler.heuristic_processing('petri_net')
        gviz = pmHandler.petri_net_visualization(heu_petri_net)
        pmHandler.save_file(gviz, filename=f'petri_net', session_dir=SESSION_DIR, add_dir='Heuristic_processing')

        heuristic_net = pmHandler.heuristic_processing('heuristic_net')
        gviz = pmHandler.heuristic_visualization(heuristic_net)
        """heuristic nets cant be saved!
        pmHandler.save_graphic(gviz, filename=f'Heuristic_processing_heuristic_net')"""

        """
        Alpha vs Heuristic Processing: Petri-net
        """
        alpha_petri_net = pmHandler.alpha_processing()
        # heu_petri_net = pmHandler.heuristic_processing('petri_net') - above
        gviz = pmHandler.petri_net_visualization(alpha_petri_net)
        pmHandler.save_file(gviz, filename=f'petri_net', session_dir=SESSION_DIR, add_dir='Alpha_processing')
        pmHandler.petri_net_visualization(heu_petri_net)

        """
        DFG Processing: PERFORMANCE vs FREQUENCY
        """
        dfg_performance = pmHandler.dfg_processing('PERFORMANCE')
        dfg_frequency = pmHandler.dfg_processing('FREQUENCY')
        gviz = pmHandler.dfg_visualization(dfg_performance)
        pmHandler.save_file(gviz, filename=f'performance', session_dir=SESSION_DIR, add_dir='DFG_processing')
        gviz = pmHandler.dfg_visualization(dfg_frequency)
        pmHandler.save_file(gviz, filename=f'frequency', session_dir=SESSION_DIR, add_dir='DFG_processing')

    def pm_component_use_2():
        """
        This Section is dedicated to show the difference between using different parameters
        -> rating in the end
        """
        para_list = [({heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.90,
                       heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 0,
                       heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 0},
                      '_090_30_30'),
                     ({heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.90,
                       heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 300,
                       heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 300},
                      '_099_300_300')]

        for (par, suffix) in para_list:
            pmHandler.update_parameters(par, replace=True)
            gviz = pmHandler.petri_net_visualization(pmHandler.alpha_processing())
            pmHandler.save_file(gviz, f'petri_net{suffix}')
            # pmHandler.save_graphic(pmHandler.heuristic_visualization(pmHandler.heuristic_processing()),f'heuristic{suffix}')
            gviz = pmHandler.heuristic_visualization(pmHandler.heuristic_processing())
            # pmHandler.save_graphic(gviz, f'heuristic{suffix}')
            # pmHandler.save_graphic(pmHandler.inductive_visualization(pmHandler.inductive_processing('process_tree')),f'inductive{suffix}')
            gviz = pmHandler.inductive_visualization(pmHandler.inductive_processing('process_tree'))
            pmHandler.save_file(gviz, f'inductive{suffix}')
            # pmHandler.save_graphic(pmHandler.dfg_visualization(pmHandler.dfg_processing()),f'dfg{suffix}')
            gviz = pmHandler.dfg_visualization(pmHandler.dfg_processing())
            pmHandler.save_file(gviz, f'dfg{suffix}')

    def pm_component_use_3_5():
        pmHandler.update_parameters({heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.90,
                                     heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 30,
                                     heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 30},
                                    replace=True)

        heu_net = pmHandler.heuristic_processing('heuristic_net')
        pmHandler.heuristic_visualization(heu_net)

        petri_net_heuristic = pmHandler.heuristic_processing('petri_net')
        pmHandler.petri_net_visualization(petri_net_heuristic)
        p_tree_filtered = pmHandler.inductive_processing(mode_detail='process_tree')
        pmHandler.inductive_visualization(p_tree_filtered)

        p_net_IMF = pmHandler.inductive_processing(mode_detail='convert', tree=p_tree_filtered)
        pmHandler.petri_net_visualization(p_net_IMF)
        petri_net_heuristic = pmHandler.heuristic_processing('petri_net')
        pmHandler.petri_net_visualization(petri_net_heuristic)

        pmHandler.rating_net_model(petri_net_heuristic, 'heuristic petri net')

        petri_net_heuristic = pmHandler.heuristic_processing('petri_net')
        pmHandler.petri_net_visualization(petri_net_heuristic)

        pmHandler.rating_net_model(petri_net_heuristic, 'heuristic petri net changes values')

    def session_3_6():
        pmHandler.update_variant('FREQUENCY')
        pmHandler.petri_net_visualization(pmHandler.alpha_processing())

        parameters = {heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.6,
                      heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 3,
                      heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 3}
        pmHandler.update_parameters(parameters)
        pmHandler.petri_net_visualization(pmHandler.heuristic_processing(mode_detail='petri_net'))

    def filter_conditional_conform_cases(dataframe):
        fltr = FilterHelper(log=dataframe)
        start_of_submission, publication_data = "2010-03-27 00:00:00", "2019-01-28 23:59:59"
        filter_trace = fltr.filter_on_time('contained_traces', start_date=start_of_submission,
                                           end_date=publication_data)
        fltr.set_log(filter_trace)

        counter = 0
        for trace in filter_trace:
            print('Trace in round ', counter)
            counter += 1

            if counter == 3:
                break
            for event in trace:
                print(event)

        filter_trace_whole = fltr.filter_on_attr(mode='attr_whole_events', attr_list=['Handle Case'],
                                                 attr_col='concept:name')
        print(filter_trace_whole)
        filter_trace_single = fltr.filter_on_attr(mode='attr_single_events', attr_list=['Handle Case'],
                                                  attr_col='concept:name')
        print(filter_trace_single)
        filter_whole_dataframe = log_converter.apply(filter_trace_whole, variant=log_converter.Variants.TO_DATA_FRAME)
        filter_single_dataframe = log_converter.apply(filter_trace_single, variant=log_converter.Variants.TO_DATA_FRAME)

        print('whole length: ', len(filter_whole_dataframe), '\n')
        print('single length: ', len(filter_single_dataframe), '\n')

        presenter = PltPresent(data=dataframe, mode_list=['terminal'])
        presenter.apply()
        presenter.set_data(data=filter_whole_dataframe)
        presenter.apply()
        presenter.set_data(data=filter_single_dataframe)
        presenter.apply()

    FRAME_LENGTH = 100
    SESSION_DIR = 'CallCenterLog'
    FILE_NAME = 'CallCenterLog.csv'
    columns = {'Case ID': 'case:concept:name', 'Start Date': 'start_timestamp', 'End Date': 'time:timestamp',
               'Activity': 'concept:name', 'Resource': 'org:resource'}
    EVENT_LOG = EventHandler(FILE_NAME).prepare_data('event_log', True, columns=columns, sorting_col='time:timestamp')

    pmHandler = Pm4pyHandler(EVENT_LOG, format_img='svg')

    filter_conditional_conform_cases(EVENT_LOG)

    counter = 0
    for trace in EVENT_LOG:
        print('Trace in round ', counter)
        counter += 1
        if counter == 3:
            break
        for event in trace:
            print(event)

    # plt_component_use()

    # pm_component_use_3_5()
    # pmHandler.rating_best_model(session_dir=SESSION_DIR, file_name='first_try')

len_list_local = [('titt',12,6), ('no gitt', 12,12),('gitt',12,1)]

for ele in len_list_local:
    name, len_b, len_a = ele
    df = pd.DataFrame({
        'len': [len_a, len_b - len_a],
        'name': ['log fit', 'log unfit']
    })
    presenter = PltPresent(data=df, mode_list='histogram', title=name, col1='name', col2='len',
                           y_label='Length of the frame')
    fig = presenter.histogram_dealer()
    presenter.save_plt(fig, filename=f'{name}_size_change', session_dir='123', diagram_type='histogram')

if __name__ == '__main__':
    main()
