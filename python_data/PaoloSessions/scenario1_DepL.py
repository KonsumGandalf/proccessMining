from python_data.DataIO import EventHandler
from python_data.Pm4pyHandler import Pm4pyHandler
from python_data.PresentHandler import PltPresent
from pm4py.algo.discovery.heuristics import algorithm as heuristic_miner
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.statistics.traces.generic.log import case_statistics
from math import floor
import math
import pandas as pd
import pm4py
from IPython.display import display


def alignments_3_7(pmHandler, FRAME_LENGTH):
    #petri_net = pmHandler.heuristic_processing(mode_detail='petri_net')
    #petri_net = pmHandler.inductive_processing(mode_detail='petri_net', variant='imd')
    from pm4py.objects.petri_net.importer import importer as pnml_importer
    petri_net = pnml_importer.apply(EventHandler('scenario1.pnml').get_file_path())
    regular_traces, irregular_traces, align_str = pmHandler.conformance_checking(petri_net, conformance_mode='alignments', just_string=False)
    #"""
    regular_traces_df, irregular_traces_df = pd.DataFrame(regular_traces), pd.DataFrame(irregular_traces)
    regular_traces_df_count = pd.DataFrame({
        'Mode': [regular_traces_df[x].mode()[0] for x in regular_traces_df],
        'Mode freq.':[regular_traces_df[x].isin(regular_traces_df[x].mode()).sum() for x in regular_traces_df],
        'Mode freq. %':[(regular_traces_df[x].isin(regular_traces_df[x].mode()).sum())/(len(regular_traces_df))*100 for x in regular_traces_df]
    })



    irregular_traces_df_count = pd.DataFrame({
        'Mode': [irregular_traces_df[x].mode()[0] for x in irregular_traces_df],
        'Mode freq.': [irregular_traces_df[x].isin(irregular_traces_df[x].mode()).sum() for x in irregular_traces_df],
        'Mode freq. %': [(irregular_traces_df[x].isin(irregular_traces_df[x].mode()).sum()) / (len(irregular_traces_df)) * 100
                         for x in irregular_traces_df]
    })

    # regular_traces_df_count.set_index('Mode')
    # displaying the DataFrame
    display(regular_traces_df_count)
    display(irregular_traces_df_count)



    presenter = PltPresent(data=regular_traces_df_count, mode_list=['histogram', 'terminal'], col2='Mode freq. %', col1='index_format',
                           x_label='Index', y_label='Share of each activity in the consensus sequence', frame_length=FRAME_LENGTH)
    presenter.apply()
    events_list = []
    for event in pmHandler.log:
        events_list.append(event[1])

    events_list_df = pmHandler.get_data('dataframe')
    presenter.set_data(data=events_list_df, col1='case:concept:name', col2='concept:name', mode_list=['terminal', 'heatmap'])
    presenter.apply()



def main():
    FRAME_LENGTH = 100
    FILE_NAME = 'scenario1_DepL.csv'
    SESSION_DIR = 'scenario1_DepL'
    columns = {'timestamp': 'time:timestamp', 'case': 'case:concept:name',
               'activity': 'concept:name', 'resource': 'org:resource'}
    currently_best_param = {
        heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.9,
        heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 35.533,
        heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 35.533,
    }
    EVENT_LOG = EventHandler(FILE_NAME).prepare_data('event_log', True, columns=columns, sorting_col='time:timestamp')
    pmHandler = Pm4pyHandler(EVENT_LOG, format_img='svg')

    pmHandler.update_parameters(parameters=currently_best_param)

    """pmHandler.rating_best_model(output_full=True, file_name='Test', session_dir=SESSION_DIR, add_suffix='_2')
    pmHandler.visualize_diagram(session_dir=SESSION_DIR, add_suffix='_2')"""
    pmHandler.search_best_para_heu_prepare(SESSION_DIR)

    #alignments_3_7(pmHandler, FRAME_LENGTH)




