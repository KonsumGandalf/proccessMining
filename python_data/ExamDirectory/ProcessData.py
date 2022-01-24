import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter


from python_data.DataIO import EventHandler, save_file
from python_data.FilterHandler import FilterHelper
from python_data.PresentHandler import PltPresent

TEST_NAME = 'BPI_test.pkl'
FILE_NAME_OUTDATED = 'BPI_Challenge_2019.csv'
FILE_NAME = 'BPI_columns_dropped.pkl'
SESSION_DIR = 'BPI_Challenge_2019'

list_case_cat = ['3-way match, invoice after GR', '3-way match, invoice before GR', '2-way match', 'Consignment']
cum_value_for_stat = 0

# event_handler = EventHandler(additional_path=SESSION_DIR, data_name=FILE_NAME)

def get_statistics(dataframe, dataframe_name=''):
    global cum_value_for_stat
    presenter = PltPresent(data=dataframe, mode_list=['terminal'])

    empty_values_per_column = pd.DataFrame({})
    for col in dataframe:
        empty_values_per_column[col] = [pd.isnull(dataframe[col]).sum()]

    cum_value_for_stat += empty_values_per_column['case:area']
    presenter.set_data(data=empty_values_per_column)
    print(dataframe_name)
    presenter.apply()


def main():
    def advanced_filter_on_wrong_entries(event_log, df):
        def filter_on_date():
            nonlocal event_log, df
            print('filter_on_date before:\n ', len_before := len(event_log))
            start_of_submission, publication_data = "2014-01-28 23:59:59", "2019-01-28 23:59:59"
            fltr.set_log(event_log)
            event_log = fltr.filter_on_time('contained_traces', start_date=start_of_submission,
                                               end_date=publication_data)
            print('filter_on_date after:\n ', len_after := len(event_log), 'a percentage of :', (1 - len_after/len_before)*100, '%')
            len_list.append(('filter_on_date', len_before, len_after))
            event_log, df = event_log, df

        def filter_for_empty_rows():
            nonlocal event_log, df
            list_concept_name = []
            for trace in event_log:
                if not(trace.attributes['area'] == ''):
                    list_concept_name.append(trace.attributes['concept:name'])

            df = df.loc[df['case:concept:name'].isin(list_concept_name)]
            event_log = log_converter.apply(df, variant=log_converter.TO_EVENT_LOG)
            print('filter_for_empty_rows after:\n ', len_after := len(event_log))
            # len_list.append(('filter_for_empty_rows', len_before, len_after))
            event_log, df = event_log, df

        def filter_for_duplicated_id_values():
            nonlocal event_log, df
            df.drop_duplicates(subset="event:id",
                                 keep=False, inplace=True)
            event_log, df = log_converter.apply(df, variant=log_converter.TO_EVENT_LOG), df

        def filter_bpi_end_act():
            nonlocal event_log, df
            print('filter_bpi_end_act before:\n ', len_before := len(event_log))
            event_log = log_converter.apply(event_log, variant=log_converter.Variants.TO_DATA_FRAME)
            possible_actions = event_log['concept:name'].unique()
            possible_ending_actions, possible_starting_actions = [], []
            for act in possible_actions:
                for ele in ['create', 'clear', 'reactivate']:
                    if ele in act:
                        possible_starting_actions.append(act)
                for ele in ['remove', 'delete', 'clear', 'complete', 'receipt', 'Receipt', 'block']:
                    if act.lower().find(ele) != -1:
                        possible_ending_actions.append(act)
            print(possible_starting_actions, '\n', possible_ending_actions)
            fltr = FilterHelper(log=event_log)
            event_log = fltr.filter_on_activity('start_list', act_list=possible_starting_actions)
            fltr.set_log(event_log)
            print('filter_bpi_end_act after:\n ', len_after_starting := len(event_log))
            len_list.append(('filter_bpi_end_act', len_before, len_after_starting))
            event_log = fltr.filter_on_activity('end_list', act_list=possible_ending_actions)
            print('filter_bpi_end_act after:\n ', len_after_ending := len(event_log))
            len_list.append(('filter_bpi_end_act', len_after_starting, len_after_ending))
            event_log, df = event_log, df

        filter_for_empty_rows()
        filter_for_duplicated_id_values()
        filter_on_date()
        return event_log, df

    len_list = []

    cat_len_dict = {}
    cat_len_dict['after'] = 0
    cat_len_dict['before'] = 0
    cat_avg_event_per_case = {}
    for cat_str in list_case_cat:
        event_handler = EventHandler(additional_path=SESSION_DIR, data_name=f'{cat_str.replace(" ", "_")}.pkl')
        df = event_handler.read_pickle()
        fltr = FilterHelper(log=df)
        get_statistics(df, cat_str)
        log = log_converter.apply(df, variant=log_converter.TO_EVENT_LOG)

        cat_len_dict['before'] += len(log)
        log, df = advanced_filter_on_wrong_entries(event_log=log, df=df)
        save_file(df, session_dir=SESSION_DIR, name=cat_str.replace(' ', '_'), program_dir='ProcessData', add_dir_3='pkl')
        save_file(df, session_dir=SESSION_DIR, name=cat_str.replace(' ', '_'), program_dir='ProcessData', add_dir_3='csv',
                  df_format='.csv')
        get_statistics(df, cat_str)

        cat_len_dict['after'] += len(log)

        cat_avg_event_per_case[cat_str] = round(len(df)/len(log), 2)

    # print('The cumulated_value_for_stat: ', cum_value_for_stat/2)
    """
    df_len_histo = pd.DataFrame({
        'amount of cases': cat_len_dict.values(),
        'category': cat_len_dict.keys()
    })
    presenter = PltPresent(data=df_len_histo, mode_list='histogram', title='Drop of timestamp digit', col1='category', col2='amount of cases',
                           y_label='Length of the event_log', x_label='index')
    fig = presenter.histogram_dealer(horizontal=True)
    presenter.save_plt(fig, filename=f'timestamp_size_change', session_dir=SESSION_DIR,
                        diagram_type='histogram', add_dir_3='overall')
    """
    df_event_histo = pd.DataFrame({
        'average event per case': cat_avg_event_per_case.values(),
        'category': ['3-way after', '3-way before', '2-way', 'Consignment']
    })
    print(df_event_histo)
    presenter = PltPresent(data=df_event_histo, mode_list=['histogram'], title='Average event per case', col1='category',
                           col2='average event per case',
                           y_label='', x_label='index')
    fig = presenter.histogram_dealer(horizontal=False, values=(2,3))
    presenter.save_plt(fig, filename=f'average_event_per_case', session_dir=SESSION_DIR,
                       diagram_type='histogram', add_dir_3='overall')
    presenter.apply()

    # log = filter_on_date(df)
    # log = filter_bpi_end_act(log)


if __name__ == '__main__':
    main()
