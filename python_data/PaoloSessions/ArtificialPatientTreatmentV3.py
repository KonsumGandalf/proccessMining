from pm4py.algo.discovery.heuristics import algorithm as heuristic_miner

from python_data.DataIO import EventHandler
from python_data.Pm4pyHandler import Pm4pyHandler



def session_3_6():
    pmHandler.update_variant('FREQUENCY')
    pmHandler.petri_net_visualization(pmHandler.alpha_processing())

    parameters = {heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.6,
                  heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 3,
                  heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 3}
    pmHandler.update_parameters(parameters, replace=True)
    pmHandler.petri_net_visualization(heu_model:=pmHandler.heuristic_processing(mode_detail='petri_net'))

    p_tree = pmHandler.inductive_processing(mode_detail='process_tree', variant='im')
    petri_compose = pmHandler.inductive_processing(mode_detail='convert', tree=p_tree, variant='im')
    gviz = pmHandler.petri_net_visualization(petri_compose)


    pmHandler.petri_net_visualization(inductive_model:=pmHandler.inductive_processing('petri_net'))

    # pmHandler.rating_best_model(output_full=True, file_name='Test', session_dir=SESSION_DIR, is)
    # pmHandler.visualize_diagram(session_dir=SESSION_DIR)

    # pmHandler.petri_net_visualization(pmHandler.inductive_processing(mode_detail='convert', tree=pmHandler.inductive_processing('process_tree')))



FRAME_LENGTH = 100
FILE_NAME = 'ArtificialPatientTreatmentV3.csv'
SESSION_DIR = 'ArtificialPatientTreatmentV3'
columns = {'datetime': 'time:timestamp', 'patient': 'case:concept:name',
           'action': 'concept:name', 'resource': 'org:resource'}
EVENT_LOG = EventHandler(FILE_NAME).prepare_data('event_log', True, columns=columns, sorting_col='time:timestamp')
pmHandler = Pm4pyHandler(EVENT_LOG, format_img='svg')


def main():
    session_3_6()


if __name__ == '__main__':
    main()
