import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter

from python_data.DataIO import EventHandler, save_file
from python_data.FilterHandler import FilterHelper
from python_data.PresentHandler import PltPresent

TEST_NAME = 'BPI_test.pkl'
FILE_NAME_OUTDATED = 'BPI_Challenge_2019.csv'
FILE_NAME = 'pkl/BPI_columns_dropped.pkl'
SESSION_DIR = 'BPI_Challenge_2019'
event_handler = EventHandler(FILE_NAME, additional_path=SESSION_DIR)

columns_rename = {'event time:timestamp': 'time:timestamp', 'event concept:name': 'concept:name',
                  'case concept:name': 'case:concept:name', 'case Vendor': 'org:resource',

                  'case Company': 'case:sub_company', 'case Document Type': 'case:doc_type',
                  'case Spend area text': 'case:area', 'case Sub spend area text': 'case:sub_area',
                  'case Purchasing Document': 'case:doc_id',
                  'case Item Type': 'item:type', 'case Item Category': 'case:item:cat',
                  'case Name': 'case:vendor:name', 'case GR-Based Inv. Verif.': 'case:inv_verif',
                  'case Item': 'item:id', 'event org:resource': 'event:org:resource', 'eventID ': 'event:id',
                  'case Goods Receipt': 'case:goods_receipt', 'event Cumulative net worth (EUR)': 'event:cum'}
present_col = columns_rename.values()

list_case_cat = ['2-way match',
                 'Consignment', '3-way match, invoice after GR', '3-way match, invoice before GR']


def main():
    def first_init_dataframe():
        FILE_NAME = 'BPI_Challenge_2019.csv'
        # Renaming all columns. The upper 2 rows define the basic cols of an event log while the others a additional ones
        event_handler = EventHandler(FILE_NAME, additional_path=SESSION_DIR)
        dataframe = event_handler.prepare_data('dataframe', sort=True, columns=columns_rename,
                                               sorting_col='time:timestamp')

        # drop columns with no further meaning
        dataframe = dataframe.drop(
            columns=['case Purch. Doc. Category name', 'case Spend classification text', 'event User',
                     'case Source'])

        save_file(dataframe, session_dir=SESSION_DIR, name='BPI_columns_dropped')
        save_file(dataframe, session_dir=SESSION_DIR, name='BPI_columns_dropped', df_format='.csv')

    def group_to_cat():

        def invoice_is_after_GR(df, event_log, parameter_wished=''):
            list_concept_name = []
            print('invoice_is_after_GR starts ')
            if parameter_wished == 'after':
                is_para = True
            else:
                is_para = False
            for trace in event_log:
                is_after = None
                for event in trace:
                    match event['concept:name']:
                        case 'Record Invoice Receipt':
                            is_after = False
                            break
                        case 'Record Goods Receipt':
                            is_after = True
                            break
                if is_para == is_after:
                    list_concept_name.append(trace.attributes['concept:name'])
            df = df.loc[df['case:concept:name'].isin(list_concept_name)]
            print('invoice_is_after_GR ends ')
            return df

        def cum_zero(df, event_log):
            list_concept_name = []

            print('cum_zero starts')
            for trace in event_log:
                cum_value = 0
                for event in trace:
                    match event['concept:name']:
                        case 'Record Invoice Receipt':
                            cum_value += 1
                        case 'Record Goods Receipt':
                            cum_value -= 1
                if cum_value == 0:
                    list_concept_name.append(trace.attributes['concept:name'])
            df = df.loc[df['case:concept:name'].isin(list_concept_name)]
            print('cum_zero ends')
            return df

        def sum_goods(df, event_log):
            print('sum_goods starts')
            list_concept_name = []
            for trace in event_log:
                for event in trace:
                    match event['concept:name']:
                        case 'Record Goods Receipt':
                            list_concept_name.append(trace.attributes['concept:name'])
                            break

            print('sum_goods ends')
            return df.loc[df['case:concept:name'].isin(list_concept_name)]

        def sum_invs(df, event_log):
            list_concept_name = []
            print('sum_inv starts')
            for trace in event_log:
                for event in trace:
                    match event['concept:name']:
                        case 'Record Invoice Receipt':
                            list_concept_name.append(trace.attributes['concept:name'])
                            break
            print('sum_inv ends')
            return df.loc[df['case:concept:name'].isin(list_concept_name)]

        def sum_clear(df, event_log):
            list_concept_name = []
            for trace in event_log:
                for event in trace:
                    match event['concept:name']:
                        case 'Clear Invoice':
                            list_concept_name.append(trace.attributes['concept:name'])
                            break

            return df.loc[df['case:concept:name'].isin(list_concept_name)]

        event_handler = EventHandler(additional_path=SESSION_DIR, data_name=FILE_NAME)
        df = event_handler.read_pickle()
        for ele_str in list_case_cat:
            df = event_handler.read_pickle()
            fltr = FilterHelper(log=df)
            event_log = fltr.filter_on_attr(mode='attr_single_events', attr_list=[ele_str],
                                            attr_col='case:item:cat')
            df = log_converter.apply(event_log, variant=log_converter.Variants.TO_DATA_FRAME)

            match ele_str:
                case '3-way match, invoice after GR':
                    df = sum_clear(sum_goods(sum_invs(cum_zero(invoice_is_after_GR(df,event_log, 'after'), event_log), event_log), event_log), event_log)
                case '3-way match, invoice before GR':
                    df = sum_clear(sum_goods(sum_invs(cum_zero(invoice_is_after_GR(df,event_log, 'before'), event_log), event_log), event_log), event_log)
                case '2-way match':
                    df = sum_clear(sum_invs(df, event_log), event_log)
                case 'Consignment':
                    df = sum_goods(df, event_log)

            save_file(df, session_dir=SESSION_DIR, name=ele_str.replace(' ', '_'))
            save_file(df, session_dir=SESSION_DIR, name=ele_str.replace(' ', '_'),
                      df_format='.csv')

    def get_statistics(dataframe, dataframe_name=''):
        presenter = PltPresent(data=dataframe, mode_list=['terminal'])

        unique_values_per_column = pd.DataFrame({})
        for col in dataframe:
            unique_values_per_column[col] = [len(dataframe[col].unique())]

        for ele in present_col:
            try:
                data = dataframe[ele].value_counts(normalize=False)
                if len(data.index) < 2000:
                    fig = presenter.pie_dealer(mode='pie', loc_title=f"{dataframe_name}_{ele}", value_list=data.tolist(),
                                               label_list=data.index.tolist())
                    presenter.save_plt(figure=fig, filename=f"{dataframe_name.replace(':', '_')}_{ele.replace(':', '_')}",
                                       session_dir=SESSION_DIR,
                                       diagram_type='pie_2', add_dir_3=dataframe_name)
            except KeyError:
                print(KeyError(f'{ele} is not defined'))

        presenter.set_data(data=unique_values_per_column)
        presenter.apply()

    def get_statistics_helper():
        global list_case_cat
        for ele in list_case_cat:
            event_handler.update(additional_path=SESSION_DIR, data_name=f"{ele.replace(' ', '_')}.pkl")
            df = event_handler.read_pickle()
            get_statistics(df, dataframe_name=ele.replace(' ', '_'))

        event_handler.update(additional_path=SESSION_DIR, data_name=FILE_NAME)
        df = event_handler.read_pickle()
        get_statistics(df, dataframe_name='overall')

    def filter_for_case_class_compliant(log):
        """

        This Funtcion is broken!
        """
        global list_case_cat
        event_handler = EventHandler(additional_path=SESSION_DIR, data_name=FILE_NAME)
        df_full = event_handler.read_pickle()
        fltr = FilterHelper(log=df_full)
        len_list = []
        for ele_str in list_case_cat:
            event_category_log = fltr.filter_on_attr(mode='attr_single_events', attr_list=[ele_str],
                                                     attr_col='case:item:cat')
            filter_case = fltr.filter_on_attr(mode='attr_single_events', attr_list=[ele_str],
                                              attr_col='case:item:cat')
            fltr.set_log(filter_case)
            print('filter_for_case_class_compliant before:\n ', len_before := len(filter_case))
            print(106, len(filter_case))
            inv_bool, gr_bool = '', ''
            match ele_str:
                case '3-way match, invoice after GR':
                    inv_bool, gr_bool = True, True
                case '3-way match, invoice before GR':
                    inv_bool, gr_bool = False, True
                case '2-way match':
                    inv_bool, gr_bool = False, False
                case 'Consignment':
                    inv_bool, gr_bool = False, True
            filter_case = fltr.filter_on_attr(mode='attr_single_events', attr_list=[inv_bool],
                                              attr_col='case:inv_verif')
            fltr.set_log(filter_case)
            filter_case = fltr.filter_on_attr(mode='attr_single_events', attr_list=[gr_bool],
                                              attr_col='case:goods_receipt')
            fltr.set_log(filter_case)
            print('filter_for_case_class_compliant after:\n ', len_after := len(filter_case))

            filter_case = log_converter.apply(filter_case,
                                              variant=log_converter.Variants.TO_DATA_FRAME)
            print(ele_str, ' single length: ', len(list_case_cat), '\n')
            save_file(filter_case, session_dir=SESSION_DIR, name=ele_str.replace(' ', '_'))
            save_file(filter_case, session_dir=SESSION_DIR, name=ele_str.replace(' ', '_'),
                      df_format='.csv')
            len_list.append((f'filter_for_case_class_compliant_{ele_str}', len_before, len_after))

    def present_len_dif():
        def cat_as_pie_dia():
            df_len_pie = pd.DataFrame({
                'amount of cases': cat_len_dict.values(),
                'category': cat_len_dict.keys()
            })
            presenter = PltPresent(data=df_len_pie, mode_list='pie')
            fig = presenter.pie_dealer(mode='pie', loc_title='ratio of the categories', value_list=df_len_pie['amount of cases'].to_list(),
                                       label_list=df_len_pie['category'].to_list(), others=False)
            presenter.save_plt(figure=fig, filename=f"{'ratio of the categories'.replace(':', '_')}",
                               session_dir=SESSION_DIR,
                               diagram_type='pie', add_dir_3='overall')
            fig = presenter.pie_dealer(mode='donut', loc_title='ratio of the categories', value_list=df_len_pie['amount of cases'].to_list(),
                                       label_list=df_len_pie['category'].to_list(), others=False)
            presenter.save_plt(figure=fig, filename=f"{'ratio of the categories'.replace(':', '_')}",
                               session_dir=SESSION_DIR,
                               diagram_type='donut', add_dir_3='overall')

        global list_case_cat
        event_handler = EventHandler(additional_path=SESSION_DIR, data_name=FILE_NAME)
        df_full = event_handler.read_pickle()
        cat_len_dict = {}
        fltr = FilterHelper(log=df_full)
        for ele_str in list_case_cat:
            io_name = ele_str.replace(' ', '_')
            """event_log_category = fltr.filter_on_attr(mode='attr_single_events', attr_list=[ele_str],
                                                     attr_col='case:item:cat')"""
            eve_hand_cat = EventHandler(additional_path=SESSION_DIR, data_name=f"{io_name}.pkl")
            df_category_filtered = eve_hand_cat.read_pickle()
            """event_log_category_filtered = log_converter.apply(df_category_filtered,
                                                              variant=log_converter.Variants.TO_EVENT_LOG)
            len_unfiltered, len_filtered = len(event_log_category), len(event_log_category_filtered)
            cat_len_dict[ele_str] = len_filtered
            df = pd.DataFrame({
                'len': [len_filtered, len_unfiltered - len_filtered],
                'name': ['compliant', 'incompliant']
            })
            presenter = PltPresent(data=df, mode_list='histogram', title=ele_str, col1='name', col2='len',
                                   y_label='Length of the event_log')
            fig = presenter.histogram_dealer()
            presenter.save_plt(fig, filename=f'{io_name}_size_change', session_dir=SESSION_DIR,
                               diagram_type='histogram')"""

            get_statistics(df_category_filtered, dataframe_name=ele_str)

        cat_as_pie_dia()



    global list_case_cat
    """for ele_str in list_case_cat:
        event_handler.update(additional_path=SESSION_DIR, data_name=f"{ele_str.replace(' ','_')}.pkl")
        df = event_handler.read_pickle()
        log = log_converter.apply(df, variant=log_converter.Variants.TO_EVENT_LOG)
        fltr = FilterHelper(log=log)
        filter_for_case_class_compliant(log)"""
    # first_init_dataframe()
    # group_to_cat()
    # present_len_dif()
    """event_handler.update(additional_path=SESSION_DIR, data_name=FILE_NAME)
    df = event_handler.read_pickle()
    presenter = PltPresent(data=df, mode_list=['terminal'])
    presenter.apply()"""

    # filter_conditional_conform_cases()
    # filter_bpi_end_act()

    # filter_on_wrong_entries()


    get_statistics_helper()

if __name__ == '__main__':
    main()
