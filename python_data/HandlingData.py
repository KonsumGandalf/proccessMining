from typing import Dict, Any

import pandas as pd
import os
from datetime import datetime

import pm4py
from pm4py.objects.log.util import dataframe_utils
"""
Importing all util - tool functions
"""
from pm4py.util.business_hours import BusinessHours
from pm4py.objects.log.util import interval_lifecycle
from datetime import datetime

"""
Importing all converting functions
"""
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.conversion.heuristics_net import converter as hn_converter
from pm4py.objects.log.util import insert_classifier

# from pm4py.objects.
"""
Importing all filtering functions
"""
from pm4py.algo.filtering.log.timestamp import timestamp_filter
from pm4py.algo.filtering.log.cases import case_filter
from pm4py.algo.filtering.log.start_activities import start_activities_filter
from pm4py.algo.filtering.log.end_activities import end_activities_filter
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter

"""
Importing all mining functions
"""
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristic_miner
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.algo.discovery.temporal_profile import algorithm as temporal_profile_discovery

"""
Importing visualization tools
"""
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
from pm4py.visualization.dfg import visualizer as dfg_visualizer

"""
Importing all statistic functions
"""
from pm4py.statistics.traces.generic.pandas import case_statistics
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.statistics.traces.generic.log import case_arrival


"""
#############
Handling data
#############
Declaration of used data files
"""
PATH_EXAM = '../src/data/exam_data'
PATH_COURSE = '../src/data/PM-Regensburg'
FILE_NAME = 'scenario1_DepL.csv'
OUTPUT_PATH = '../src/data/output'

"""
As I just will need to import CSV not XES Files for the process mining seminar ill just apply this
@:var log_csv - dataframe 
"""
FILE_PATH = os.path.join(PATH_COURSE, 'CCex2', FILE_NAME)
log_csv = pd.read_csv(FILE_PATH, sep=',')
log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
# setting column names to default pm4py terms -> later less code
log_csv.rename(columns={'timestamp': 'time:timestamp', 'case': 'case:concept:name', 'activity': 'concept:name',
                        'resource': 'org:resource'}, inplace=True)

"""
##############
Filtering data
##############
"""
log_attribute = 'concept:name'
log_csv = log_csv.sort_values('time:timestamp')

parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: log_attribute}
event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
event_log = timestamp_filter.filter_traces_contained(event_log, "2020-06-05 01:00:00", "2020-07-05 08:59:59")

"""
try of implementing a Classifier - didnt work #error#help
event_log, activity_key = insert_classifier.insert_activity_classifier_attribute(event_log, "org:resource")
for trace in event_log:
 for event in trace:
  event["customClassifier"] = str(event["timestamp"]) + str(event["case"])
"""

def filter_helper(log, mode: str, mode_detail: int):
    """
    @:param event_log log: Used data
    @:param int mode: The mode presents which of the filtering methods are applied
    """
    start_date, end_date = "2020-06-05 02:00:00", "2020-07-05 08:00:59"
    time_min, time_max = 86400, 86400 * 60
    filter_list = ['Activity P', 'Activity A']
    actor_filter_list = ['Brian', 'Gerald']
    lower_bound, upper_bound = 40, 51
    start_act, end_act = 'Activity A', 'Activity A'
    reoccurring_act, count_reoccurring = start_act, 4
    """
    @:returns a list of attributes of the logs -> f.e. resources
    """

    def list_get_all_attributes():
        activities: dict[Any, int] = attributes_filter.get_attribute_values(log, "concept:name")
        resources = attributes_filter.get_attribute_values(log, "org:resource")
        actors = attributes_filter.get_attribute_values(log, "actor")
        labels = attributes_filter.get_attribute_values(log, "label")
        descriptions = attributes_filter.get_attribute_values(log, "description")
        return activities, resources, actors, labels, descriptions

    match mode.lower():
        case 'time':
            match mode_detail:
                case 1:
                    # Filtering on a Time date contained - start AND end in set
                    # Starting & Ending activity can NOT be different
                    return timestamp_filter.filter_traces_contained(event_log, start_date, end_date)
                case 2:
                    # Filtering on a Time date intersecting - start OR end in set
                    # Starting & Ending activity can NOT be different
                    return timestamp_filter.filter_traces_intersecting(event_log, start_date, end_date)
                case 3:
                    # Filtering on a Time date contained
                    # Starting & Ending activity can be different
                    return timestamp_filter.apply_events(event_log, start_date, end_date)
                case 4:
                    # Filtering on a Time range
                    return case_filter.filter_case_performance(log, time_min, time_max)
        case 'activity':
            match mode_detail:
                case 1:
                    # Here a specific list is used which determines the starting_options
                    # print(start_activities_filter.get_start_activities(log))
                    return start_activities_filter.apply(log, filter_list)
                case 2:
                    """
                    @:parameter DECREASING_FACTOR: percentage of Activity occurring - help!
                    --> 700/1000 = 0.7
                    --> 400/1000 = 0.4
                    """
                    filter_list_any = start_activities_filter.get_start_activities(
                        log, parameters={start_activities_filter.Parameters.DECREASING_FACTOR: 10000})
                    filter_list = []
                    for f in filter_list_any.keys():
                        filter_list.append(f)
                    print(filter_list)
                    return start_activities_filter.apply(log, filter_list)
                case 3:
                    # filter on end activities
                    return end_activities_filter.apply(log, filter_list)
        case 'variant' | 'variants':
            match mode_detail:
                case 1:
                    # filters for all variants - occurrences of those
                    variants = variants_filter.get_variants(log)
                    # use the found filter -> nonsense but in the one example of all events
                    # return variants_filter.apply(log, variants)
                    # use the variants to filter out all positive entries
                    return variants_filter.apply(log, variants, parameters={variants_filter.Parameters.POSITIVE: False,
                                                                            variants_filter.Parameters.DECREASING_FACTOR: 0.6})
                case 2:
                    # filter for the most common variants
                    # -> 0 - just the most common kept
                    # -> 0.5 - half of the variants kept
                    # default=0.6
                    return variants_filter.filter_log_variants_percentage(log, percentage=0)
                case 3:
                    # returns just the 1 to the k-most often used variant
                    return variants_filter.filter_variants_top_k(log, k=10)
                case 4:
                    # filters for the percentage a variant is used:
                    # -> A: 400/1000 = 0.4 | B: 50/1000 = 0.05 | min_coverage_percentage=0.1
                    # -> output: A
                    return variants_filter.filter_variants_by_coverage_percentage(log, min_coverage_percentage=0.1)
        case 'attribute':
            match mode_detail:
                case 1:
                    # filters the event_log where parameter=['Gerald'] is included - str
                    # returns THE WHOLE event_log
                    return attributes_filter.apply(log, actor_filter_list,
                                                   parameters={attributes_filter.Parameters.ATTRIBUTE_KEY: 'actor',
                                                               attributes_filter.Parameters.POSITIVE: True})
                case 2:
                    # filters the event_log where parameter=['Gerald'] is included - str
                    # returns single_events (PART) of event_logs
                    return attributes_filter.apply_events(log, actor_filter_list,
                                                          parameters={
                                                              attributes_filter.Parameters.ATTRIBUTE_KEY: 'actor',
                                                              attributes_filter.Parameters.POSITIVE: True})
                case 3:
                    # filters the event for the range between lower_bound and upper_bound (INCLUDING BOTH) - int
                    # returns THE WHOLE event_log
                    return attributes_filter.apply_numeric(log, lower_bound, upper_bound,
                                                           parameters={
                                                               attributes_filter.Parameters.ATTRIBUTE_KEY: "org:resource"})
                case 4:
                    # filters the event for the range between lower_bound and upper_bound (INCLUDING BOTH) - int
                    # returns single_events (PART) of event_logs
                    return attributes_filter.apply_numeric_events(log, lower_bound, upper_bound,
                                                                  parameters={
                                                                      attributes_filter.Parameters.ATTRIBUTE_KEY: "org:resource"})

        case 'between':
            # Filters for cases with start activity and ending activity
            # This is useful to analyse in detail the behavior in the log between such couple of activities
            return pm4py.filter_between(log, start_act, end_act)
        case 'case_size':
            # Filters for number of cases - lower_bound & upper_bound including
            # This can have two purposes: eliminating cases that are too short
            # (which are obviously incomplete or outliers), or are too long (too much rework).
            return pm4py.filter_case_size(log, lower_bound, upper_bound)
        case 'rework':
            # Filters for cases with reoccurring_activity at least count_reoccurring
            # f.e. reoccurring_act = 'Activity A', count_reoccurring = 4
            return pm4py.filter_activities_rework(log, reoccurring_act, count_reoccurring)
        case 'paths_performance':
            # Filters for Time range between 2 cases and a starting_act and ending_act
            # This can be useful to identify the cases in which a large amount of time is passed between two activities.
            # combines performance and between - I guess
            return pm4py.filter_paths_performance(log, (start_act, end_act), 0, time_max * 10000000)
        case 'generic':
            # Filter with lambda functions
            match mode_detail:
                case 1:
                    # Filter the cases of the event log which have a number of events greater than 600
                    return pm4py.filter_log(lambda x: len(x) > 600, log)
                case 2:
                    # Filter the events with even activity length
                    for case in log:
                        filtered_case = pm4py.filter_trace(lambda x: len(x["concept:name"]) % 2 == 0, case)
                        print(len(case), len(filtered_case))
                        return pm4py.filter_trace(lambda x: len(x["concept:name"]) % 2 == 0, filtered_case)
            # generic filtering on
    print(f'Wrong value of mode {mode_detail} min is 1, max 7\n Error is passed no filter applied')
    raise ValueError(f'Wrong value of mode {mode_detail} min is 1, max 7\n Error is passed no filter applied')


def print_str_dict(local_dict: dict, key_entry: str, value_entry: str) -> str:
    print_out = ''
    for key, value in local_dict.items():
        if key == key_entry and value == value_entry:
            print_out += str(local_dict)
    return print_out


def print_event_log(log, mode=0):
    printout_list = []
    """
    Possible values for:
    mode_list = ['time', 'activity', 'variant', 'attributes', 'between', 
    'case_size', 'rework', 'paths_performance', 'generic']
    mode_detail = 1-4
    """

    if mode == 0:
        """printout_list.append(filter_helper(log, 1))
        printout_list.append(filter_helper(log, 2))"""
        for i in range(1, 3):
            printout_list.append(filter_helper(log, 'generic', i))

        for idx, log in enumerate(printout_list):
            print('#' * 20 + '\n' + f'This is the log of Index {idx} and has a length of {len(log)}' + '\n' + '#' * 20)
            for idx2, case in enumerate(log):
                """
                @:var counter_print_out represent the number 1 case contains single_events which fit to the params
                """
                counter_print_out = 0
                last_idx = len(case) - 1
                print(f'{(idx2 + 1)}. event log starts here')
                for idx3, event in enumerate(case):
                    # print(event)
                    if idx3 == 0: print(f'starting_activity {event}')
                    if idx3 == last_idx: print(f'ending_activity {event}')

    if mode == 1:
        printout_list.append(filter_helper(log, 'attribute', 1))
        printout_list.append(filter_helper(log, 'attribute', 2))
        for idx, log in enumerate(printout_list):
            print('#' * 20 + '\n' + f'This is the log of Index {idx} and has a length of {len(log)}' + '\n' + '#' * 20)
            for idx2, case in enumerate(log):
                """
                @:var counter_print_out represent the number 1 case contains single_events which fit to the params
                """
                counter_print_out = 0
                for idx3, event in enumerate(case):
                    if len(print_out := print_str_dict(event, key_entry='actor', value_entry='Gerald')) > 1:
                        counter_print_out += 1
                        print(print_out, counter_print_out)
                print(f'The case entry had: {counter_print_out} the attribute \n \n \n')


# print_event_log(event_log, 0)


def statistics_helper(log, mode: int):
    """
    @:param event_log log: Used data
    @:param int mode: The mode presents which of the filtering methods are applied
    """
    match mode:
        case 1:
            # doesnt work in the example
            print(log)
            variants_count = case_statistics.get_variant_statistics(log)
            return sorted(variants_count, key=lambda x: x['case'], reverse=True)

    print(f"Wrong value of mode {mode} min is 1, max 3\n Error is passed no filter applied")
    return log


def print_statistics(log):
    printout_list = []

    printout_list.append(statistics_helper(log, 1))


# print_statistics(event_log)


"""
DATAFRAME_PATH = os.path.join(OUTPUT_PATH, 'test1')
dataframe = log_converter.apply(event_log, variant=log_converter.Variants.TO_DATA_FRAME)
dataframe.to_csv(DATAFRAME_PATH)
"""

"""
The following part presents way of mining information
"""


def process_discovery_helper(log, mode: str, mode_detail: int = 0, visualizer: str=pn_visualizer.Variants.PERFORMANCE):
    """
    :param log: data used for processing
    :param mode: determines the miner used for processing
    :param mode_detail: determines mode of the chosen miner
    :param visualizer: determines visualization method for nets
    :return:
    """
    match mode.lower():
        case 'alpha':
            """
            Finds 
                A Petri net model where all the transitions are visible 
                and unique and correspond to classified events (for example, to activities).
                
                initial and final marking
            """
            net, initial_marking, final_marking = alpha_miner.apply(log,
                                                                    variant=alpha_miner.Variants.ALPHA_VERSION_PLUS)
            return net, initial_marking, final_marking
        case 'inductive':
            """
            The basic idea of Inductive Miner is about detecting a 'cut' in the log 
            Deutsch:
            Gebrauch von verborgenen Übergängen, insbesondere beim Überspringen eines Teils des Modells. 
            Außerdem hat jeder sichtbare Übergang eine eindeutige Bezeichnung (es gibt keine Übergänge im Modell,
            Output:
                Petri Net
                Process Tree
            variant options:
                Variants.IM	    Produces a model with perfect replay fitness.
                Variants.IMf	Produces a more precise model, without fitness guarantees, by eliminating some behavior.
                Variants.IMd	A variant of inductive miner that considers only the directly-follows graph, for maximum performance. However, replay fitness guarantees are lost.
                    
            """
            match mode_detail:
                case 1:
                    net, initial_marking, final_marking = inductive_miner.apply(log,
                                                                                variant=inductive_miner.Variants.IM)
                    return net, initial_marking, final_marking
                case 2:
                    # Process Tree
                    tree = inductive_miner.apply_tree(log)
                    return tree
                case 3:
                    # Converting a tree in a net
                    net, initial_marking, final_marking = pt_converter.apply(tree=pt_converter.Variants.TO_PETRI_NET)
                    return net, initial_marking, final_marking
                    # Converting a net in a tree - no found resource - please add
        case 'heuristic':
            """
                Finds Petri-Net - Directly-Follows Graph - dependency graph
                Noise Tolerant
               
                Possible Parameters:
                    DEPENDENCY_THRESH	dependency threshold of the Heuristics Miner (default: 0.5) - Abhängigkeitsschwelle
                    AND_MEASURE_THRESH	AND measure threshold of the Heuristics Miner (default: 0.65) - AND-Maßnahmeschwelle 
                    MIN_ACT_COUNT	minimum number of occurrences of an activity to be considered (default: 1) - Mindestanzahl Aktivitäten
                    MIN_DFG_OCCURRENCES	minimum number of occurrences of an edge to be considered (default: 1) - Mindestanzahl Kanten
                    DFG_PRE_CLEANING_NOISE_THRESH	cleaning threshold of the DFG (in order to remove weaker edges, default 0.05) - Reinigungsschwelle der DFG
                    LOOP_LENGTH_TWO_THRESH	thresholds for the loops of length 2 - Schwellenwerte für Schleifenlänge
               
            """
            match mode_detail:
                case 1:
                    net, im, fm = heuristic_miner.apply(log, parameters={
                        heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.99})
                    return net, im, fm
                case 2:
                    heu_net = heuristic_miner.apply_heu(log, parameters={
                        heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.99})
                    return heu_net

        case 'dfg':
            """
            Directly-Follows Graph
            
            Variants:
                NATIVE = native
                FREQUENCY = native
                PERFORMANCE = performance
                FREQUENCY_GREEDY = native
                PERFORMANCE_GREEDY = performance
                FREQ_TRIPLES = freq_triples
                CASE_ATTRIBUTES = case_attributes
            """
            dfg_nat = dfg_discovery.apply(log, variant=dfg_discovery.Variants.NATIVE) # here frequency
            dfg_freq = dfg_discovery.apply(log, variant=dfg_discovery.Variants.FREQUENCY)
            dfg_perf = dfg_discovery.apply(log, variant=dfg_discovery.Variants.PERFORMANCE)
            return dfg_nat, dfg_freq, dfg_perf



        case '':
            return ''
    raise ValueError('Mode u entered with doenst exist')


def visualize_helper(log, mode_list: list, variant=dfg_visualizer.Variants.PERFORMANCE, format_img="png"):
    """
    :param log: data used for process mining
    :param mode_list: applied to the miner - Options: ['Alpha', 'Inductive', 'Heuristic']
    :param variant: applies the variant which is used in the visualisers - Options ['FREQUENCY', 'PERFORMANCE']
    :param format_img: applies the format which is used for saving - Options ['svg', 'png'] - I dont implement this
    :return:
    """

    """
    This method is supposed to save the svg of a model
    requirement: parameters={dfg_visualizer.Variants.PERFORMANCE.value.Parameters.FORMAT: "svg"} in apply
    Visualizers dont have to match
    """
    def save_img(graphic_svg, name):
        SVG_NAME = name + ".svg"
        SVG_PATH = os.path.join(OUTPUT_PATH, SVG_NAME)
        dfg_visualizer.save(graphic_svg, SVG_PATH)

    """
    There are a couple of possible Variants - all visualizers work:
        FREQUENCY
        PERFORMANCE
    """

    for mode in mode_list:
        # additional behaviour
        match mode.lower():
            case 'inductive':
                tree = process_discovery_helper(log, mode, 2)
                # Possible net, ini_mark, fin_mark = pt_converter.apply(tree, variant=pt_converter.Variants.TO_PETRI_NET)
                pt_visualizer.view(pt_visualizer.apply(tree))
            case 'heuristic':
                heu_net = process_discovery_helper(log, mode, 2)
                hn_visualizer.view(hn_visualizer.apply(heu_net))
            case 'dfg':
                for idx, dfg_mode in enumerate(process_discovery_helper(log, mode)):
                    gviz = dfg_visualizer.apply(dfg_mode, log=log, variant=dfg_visualizer.Variants.PERFORMANCE,
                                                parameters={dfg_visualizer.Variants.PERFORMANCE.value.Parameters.FORMAT: "svg"})
                    dfg_visualizer.view(gviz)

                    save_img(gviz, 'test')
                continue
            case 'temporal_profile_disc':
                print(process_discovery_helper(event_log))

        # for all miners the same
        net, ini_mark, fin_mark = process_discovery_helper(log, mode, 1)
        gviz = pn_visualizer.apply(net, ini_mark, fin_mark)
        pn_visualizer.view(gviz)
        save_img(gviz, '123')


list_full = ['Alpha', 'Inductive', 'Heuristic', 'dfg']
#visualize_helper(event_log, ['alpha'], dfg_visualizer.Variants.PERFORMANCE, "png")


def get_average_deviation_time(log):
    """
    A temporal profile measures
        the average duration
        the average standard deviation

    implemented in algorithms but in my perception to be assigned to statistics

    :param log:
    :return: (init_activity, ending_activity): (average duration, average standard deviation)
    """
    temporal_profile = temporal_profile_discovery.apply(event_log)
    return temporal_profile

def statistic_helper(log, mode, mode_detail):
    match mode:
        case 'time':
            match mode_detail:
                case 1:
                    # duration time of all single cases - list
                    all_case_durations = case_statistics.get_all_casedurations(log, parameters={
                        case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
                    return all_case_durations
                case 2:
                    # duration the median time of all cases - int
                    median_case_duration = case_statistics.get_median_caseduration(log, parameters={
                        case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
                    return median_case_duration
                case 3:
                    # Falleröffnungsdurchschnitt erhalten - int
                    case_arrival_ratio = case_arrival.get_case_arrival_avg(log, parameters={
                        case_arrival.Parameters.TIMESTAMP_KEY: "time:timestamp"})
                    return case_arrival_ratio
                case 4:
                    # Mittelwert der Fallstreuung ermitteln - int
                    case_dispersion_ratio = case_arrival.get_case_dispersion_avg(log, parameters={
                        case_arrival.Parameters.TIMESTAMP_KEY: "time:timestamp"})
                    return case_dispersion_ratio
                case 5:
                    # Business hours vs Normal hours
                    """
                    
                    start_time, end_time = event_log[0][0]['time:timestamp'], event_log[0][len(event_log[0]) - 1]['time:timestamp']
                    start_time, end_time = datetime.fromtimestamp(st), datetime.fromtimestamp(et)"""
                    second_number = 60 * 60 * 24
                    st = datetime.fromtimestamp(second_number)
                    et = datetime.fromtimestamp(second_number*31)
                    bh_object = BusinessHours(st, et, worktiming=[8, 16], weekends=[5, 6, 7])
                    worked_time = bh_object.gethours() # different possible
                    return worked_time, (second_number*31 - second_number)/24

                case 6:
                    """
                    The Lead Time: the overall time | start - end | NOT considering if it was actively worked or not.
                    The Cycle Time: the overall time | start - end | considering only the times where it was actively worked.
                    -> just business hours in this concept
                    interval_lifecycle.Parameters: 
                        start_timestamp_key, 
                        timestamp_key, 
                        worktiming, 
                        weekends
                        
                    :returns additionally:
                    @@approx_bh_partial_cycle_time	Incremental cycle time associated to the event (the cycle time of the last event is the cycle time of the instance)
                    @@approx_bh_partial_lead_time	Incremental lead time associated to the event
                    @@approx_bh_overall_wasted_time	Difference between the partial lead time and the partial cycle time values
                    @@approx_bh_this_wasted_time	Wasted time ONLY with regards to the activity described by the ‘interval’ event
                    @@approx_bh_ratio_cycle_lead_time	Measures the incremental Flow Rate (between 0 and 1).
                    """
                    enriched_log = interval_lifecycle.assign_lead_cycle_time(log, parameters={interval_lifecycle.Parameters.WEEKENDS: [1]})
                    return enriched_log

                case 7:
                    """
                    Sojourn Time -> work just for log with start_timestamp & time:timestamp
                    """


def statistics_visualizer(log):
    mode_list = [('time', 6)]
    for mode, mode_detail in mode_list:
        print(mode)
        for i in range(mode_detail):
            print(f'{i+1}: {statistic_helper(log, mode, i+1)}')

statistics_visualizer(event_log)
"""
for trace in event_log:
    for event in trace:
        #print(event)"""



