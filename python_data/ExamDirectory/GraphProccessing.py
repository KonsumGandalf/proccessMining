import pandas as pd
from pm4py.objects.conversion.log import converter as log_converter


from python_data.DataIO import EventHandler, save_file
from python_data.FilterHandler import FilterHelper
from python_data.PresentHandler import PltPresent
from python_data.Pm4pyHandler import Pm4pyHandler
from python_data.LogHandler import LogHandler

TEST_NAME = 'BPI_test.pkl'
FILE_NAME_OUTDATED = 'BPI_Challenge_2019.csv'
FILE_NAME = 'BPI_columns_dropped.pkl'
SESSION_DIR = 'BPI_Challenge_2019'

list_case_cat = ['3-way match, invoice after GR', '3-way match, invoice before GR', '2-way match', 'Consignment']
cum_value_for_stat = 0


def variant_helper(event_log, df, io_name):
    FRAME_LENGTH = 100
    size = (30, 5)
    LogHandler1 = LogHandler(log=event_log, mode='variant', frame_length=FRAME_LENGTH, dataframe=df)
    variant_native, variant_dataframe, dataframe_extended = LogHandler1.groupby_func(0, 'exact', display_df=False)

    PresentationHandler1 = PltPresent(data=variant_native, mode_list=['plt'], col1='index_format', col2='percentage',
                                      title='Top 100 values - bar chart of variants percentage', x_label='variant', y_label='count'
                                      , frame_length=FRAME_LENGTH, size=size)

    PresentationHandler1.pandas_full_presentation()
    fig = PresentationHandler1.cum_pdf_chart()
    fig2 = PresentationHandler1.histogram_dealer()
    PresentationHandler1.save_plt(fig, filename=f'{io_name}_percentage_per_case', session_dir=SESSION_DIR,
                       diagram_type='histogram', add_dir_3=io_name)
    PresentationHandler1.save_plt(fig2, filename=f'{io_name}_percentage_per_case', session_dir=SESSION_DIR,
                                  diagram_type='histogram', add_dir_3=io_name)

    # difference to his diagram he forgets to use frame_length => lost dimension
    PresentationHandler2 = PltPresent(dataframe_extended, mode_list=['plt'], col1='index_format',
                                      col2='avg_duration',
                                      title='Top 100 values - bar chart of variants average duration', x_label='cases',
                                      y_label='avg_duration',
                                      frame_length=FRAME_LENGTH, size=size)

    PresentationHandler2.pandas_full_presentation()
    fig1 = PresentationHandler2.cum_pdf_chart()
    fig2 = PresentationHandler2.histogram_dealer()
    PresentationHandler2.save_plt(fig1, filename=f'{io_name}_avg_duration_per_case', session_dir=SESSION_DIR,
                                  diagram_type='histogram', add_dir_3=io_name)
    PresentationHandler2.save_plt(fig2, filename=f'{io_name}_avg_duration_per_case', session_dir=SESSION_DIR,
                                  diagram_type='histogram', add_dir_3=io_name)

    PresentationHandler3 = PltPresent(dataframe_extended, mode_list=['plt'], col1='index_format',
                                      col2='avg_duration',
                                      title='Top 100 values - bar chart of events per variant', x_label='cases',
                                      y_label='avg_duration',
                                      frame_length=FRAME_LENGTH, size=size)

    PresentationHandler3.pandas_full_presentation()
    fig1 = PresentationHandler3.cum_pdf_chart()
    fig2 = PresentationHandler3.histogram_dealer()
    PresentationHandler3.save_plt(fig1, filename=f'{io_name}_average_event_per_case', session_dir=SESSION_DIR,
                                  diagram_type='histogram', add_dir_3=io_name)
    PresentationHandler3.save_plt(fig2, filename=f'{io_name}_average_event_per_case', session_dir=SESSION_DIR,
                                  diagram_type='histogram', add_dir_3=io_name)

    PresentationHandler4 = PltPresent(dataframe_extended, mode_list=['plt'], col1='index_format',
                                      col2='sum_duration',
                                      title='Top 100 values - bar chart of variants sum duration', x_label='cases',
                                      y_label='total duration',
                                      frame_length=400, size=size)

    PresentationHandler4.pandas_full_presentation()
    fig1 = PresentationHandler4.cum_pdf_chart()
    fig2 = PresentationHandler4.histogram_dealer()
    PresentationHandler4.save_plt(fig1, filename=f'{io_name}_sum_duration_per_case', session_dir=SESSION_DIR,
                                  diagram_type='histogram', add_dir_3=io_name)
    PresentationHandler4.save_plt(fig2, filename=f'{io_name}_sum_duration_per_case', session_dir=SESSION_DIR,
                                  diagram_type='histogram', add_dir_3=io_name)



def for_all_categories():
    for cat_str in list_case_cat:
        io_name = cat_str.replace(" ", "_")
        event_handler = EventHandler(additional_path=SESSION_DIR, data_name=f'{io_name}.pkl')
        df = event_handler.read_pickle()
        event_log = log_converter.apply(df, variant=log_converter.TO_EVENT_LOG)
        pmHandler = Pm4pyHandler(event_log, session_dir=SESSION_DIR, format_img='svg')
        # pmHandler.rating_best_model(output_full=True, file_name='rating_model', session_dir=SESSION_DIR,add_suffix=io_name)
        # pmHandler.visualize_diagram(session_dir=SESSION_DIR,add_suffix=io_name, add_dir_2=io_name)
        variant_helper(event_log, df, io_name+'test')
        # pmHandler.local_visualization(io_name)

def main():
    for_all_categories()

if __name__ == '__main__':
    main()
