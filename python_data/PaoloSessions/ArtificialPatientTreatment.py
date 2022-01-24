from python_data.DataIO import EventHandler
from python_data.PresentHandler import PltPresent
from python_data.Pm4pyHandler import Pm4pyHandler
from pm4py.algo.discovery.heuristics import algorithm as heuristic_miner
import pm4py

def actions_on_event_dataframe(data, case: int):
    match case:
        case 0:
            # Create a pivot table of the start and end timestamps associated with each case
            # - automatically ordered alphabetically
            case_starts_ends = data.pivot_table(index='case:concept:name', aggfunc={'time:timestamp': ['min', 'max']})
            case_starts_ends = case_starts_ends.reset_index()
            case_starts_ends.columns = ['case:concept:name', 'cases_end', 'case_start']
            data = data.merge(case_starts_ends, on='case:concept:name')
            # duration to this point
            data['cumulative_timestamp'] = data['time:timestamp'] - data['case_start']
            """
            5 days 05:53:55
            - days part: 5 days
            - datetime part: 05:53:55
            data['cumulative_timestamp'].dt.seconds -> converts the whole datetime part
            """
            data['cumulative_seconds'] = data['cumulative_timestamp'].dt.seconds + (60 * 60 * 24) * data[
                'cumulative_timestamp'].dt.days  #
            data['cumulative_days'] = data['cumulative_timestamp'].dt.days
            return data

        case 1:
            patientnums = [int(e) for e in log_csv['case:concept:name'].apply(lambda x: x.strip('patient'))]
            P1 = PltPresent(data=data, col1='cumulative_seconds', col2='case:concept:name', hue='concept:name',
                            mode_list=['sns'], size=(10, 10), y_ticks=patientnums, frame_length=700)
            P1.apply()
            P1.set_data(data, 'case:concept:name', 'concept:name', ['heatmap'])
            P1.apply()


FRAME_LENGTH = 100
SESSION_DIR = 'ArtificialPatientTreatment'
FILE_NAME = 'ArtificialPatientTreatment.csv'
columns = {'datetime': 'time:timestamp', 'patient': 'case:concept:name',
           'action': 'concept:name', 'resource': 'org:resource'}
EVENT_LOG = EventHandler(FILE_NAME).prepare_data('dataframe', True, columns=columns, sorting_col='time:timestamp')

log_csv = actions_on_event_dataframe(EVENT_LOG, case=0)
actions_on_event_dataframe(log_csv, case=1)

filtered_log = pm4py.filter_case_size(log_csv, 2, 10)
filtered_log = pm4py.filter_between(filtered_log, "Inbound Call", "Handle Case")

log_csv = EVENT_LOG
pmHandler = Pm4pyHandler(log_csv)

dfg = pmHandler.dfg_processing()
pmHandler.dfg_visualization(dfg)

alpha_net = pmHandler.alpha_processing()
pmHandler.petri_net_visualization(alpha_net)

p_tree = pmHandler.inductive_processing(mode_detail='process_tree')
pmHandler.inductive_visualization(p_tree)

petri_net_tree_converted = pmHandler.inductive_processing(mode_detail='convert', tree=p_tree)
pmHandler.petri_net_visualization(petri_net_tree_converted)



"""
From Here a Review of the CallCenter Data starts
compare with Session 1
"""




def main():
    pmHandler.rating_best_model(session_dir=SESSION_DIR, file_name='first_try')

if __name__ == '__main__':
    main()
