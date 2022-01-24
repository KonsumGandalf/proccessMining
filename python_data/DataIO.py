from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.objects.log.obj import EventLog
import pm4py

import pandas as pd
import matplotlib

import os

PATH_EXAM = '../../src/data/exam_data'
PATH_COURSE = '../../src/data/course_data'  # Alternative: PM-Regensburg
OUTPUT_PATH = '../../src/data/output'

class EventHandler:


    def __init__(self, data_name: str, additional_path: str='', separator=','):
        self.FILE_PATH = os.path.join(PATH_COURSE, additional_path, data_name)
        self.separator = separator

    def update(self, data_name: str, additional_path: str = '', separator=','):
        self.FILE_PATH = os.path.join(PATH_COURSE, additional_path, data_name)
        self.separator = separator

    def get_file_path(self):
        return self.FILE_PATH

    def prepare_data(self, data_format: str, sort=True, columns={}, sorting_col: str = 'start_timestamp'):
        log_csv = pd.read_csv(self.FILE_PATH, sep=self.separator, encoding="ISO-8859-1")
        log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
        if sort:
            log_csv.rename(
                columns=columns, inplace=True)
            log_csv = log_csv.sort_values(sorting_col)
            log_attribute = 'case:concept:name'
            parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: log_attribute}
        else:
            parameters = {}
        match data_format:
            case 'event_log':
                event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
                return event_log
            case 'dataframe':
                event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_DATA_FRAME)
                return event_log

    def read_pickle(self):
        return pd.read_pickle(self.FILE_PATH)

def save_file(file, name: str, session_dir=None, program_dir=None, diagram_type='', df_format='.pkl', add_dir_3=None, mode=None):
    """
    heuristic nets cant be saved!
    :param file: type str or graphic
    :param name:
    :param program_dir:
    :return:
    """
    # SVG_NAME = name + ".png"
    if type(file) == EventLog:
        file = log_converter.apply(file, variant=log_converter.Variants.TO_EVENT_LOG)
    FILE_NAME = OUTPUT_PATH
    if session_dir:
        FILE_NAME = os.path.join(FILE_NAME, session_dir)
        if not os.path.isdir(FILE_NAME):
            os.mkdir(FILE_NAME)
    if program_dir:
        FILE_NAME = os.path.join(FILE_NAME, program_dir)
        if not os.path.isdir(FILE_NAME):
            os.mkdir(FILE_NAME)
    if diagram_type:
        FILE_NAME = os.path.join(FILE_NAME, diagram_type)
        if not os.path.isdir(FILE_NAME):
            os.mkdir(FILE_NAME)
    if add_dir_3:
        FILE_NAME = os.path.join(FILE_NAME, add_dir_3)
        if not os.path.isdir(FILE_NAME):
            os.mkdir(FILE_NAME)
    if type(file) == str:
        FILE_NAME = os.path.join(FILE_NAME, name+'.text')
        with open(FILE_NAME, "w") as text_file:
            text_file.write(file)
    elif diagram_type:
        FILE_NAME = os.path.join(FILE_NAME, name+'.svg')
        file.savefig(FILE_NAME, bbox_inches='tight') #
    elif type(file) == pd.DataFrame:
        FILE_NAME = os.path.join(FILE_NAME, name+df_format)
        if df_format == '.pkl':
            file.to_pickle(FILE_NAME)
        else:
            file.to_csv(FILE_NAME)
    else:
        FILE_NAME = os.path.join(FILE_NAME, name+'.svg')
        match mode:
            case 'petri_net':
                pm4py.save_vis_petri_net(file[0], file[1], file[2], FILE_NAME)
            case 'process_tree':
                pm4py.save_vis_process_tree(file, FILE_NAME)
            case 'heuristic_net':
                pm4py.save_vis_heuristics_net(file, FILE_NAME)
            case _:  dfg_visualizer.save(file, FILE_NAME)


