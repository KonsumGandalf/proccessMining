"""
Importing all filtering functions
"""
import pandas as pd
import pm4py
from pm4py.algo.filtering.log.timestamp import timestamp_filter
from pm4py.algo.filtering.log.cases import case_filter
from pm4py.algo.filtering.log.start_activities import start_activities_filter
from pm4py.algo.filtering.log.end_activities import end_activities_filter
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventLog

class FilterHelper:

    log: EventLog

    start_date: str
    end_date: str
    duration_min: int
    duration_max: int

    attr_list: list
    attr_col: str
    lower_bound: int
    upper_bound: int

    act_list: list

    def __init__(self, log):
        self.set_log(log)

    def set_log(self, log):
        if type(log) == pd.DataFrame:
            self.log = log_converter.apply(log, variant=log_converter.Variants.TO_EVENT_LOG)
        else:
            self.log = log

    def set_time(self, start_date=None, end_date=None, duration_min=None, duration_max=None):
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        if duration_min:
            self.duration_min = duration_min
        if duration_max:
            self.duration_max = duration_max

    def filter_on_time(self, mode, start_date=None, end_date=None, duration_min=None, duration_max=None):
        self.set_time(start_date, end_date, duration_min, duration_max)
        match mode:
            case 'contained_traces':
                # Filtering on a Time date contained - start AND end in set
                # Starting & Ending activity can NOT be different
                return timestamp_filter.filter_traces_contained(self.log, self.start_date, self.end_date)
            case 'intersect_traces':
                # Filtering on a Time date intersecting - start OR end in set
                # Starting & Ending activity can NOT be different
                return timestamp_filter.filter_traces_intersecting(self.log, self.start_date, self.end_date)
            case 'contained_events':
                # Filtering on a Time date contained
                # Starting & Ending activity can be different
                return timestamp_filter.apply_events(self.log, self.start_date, self.end_date)
            case 'performace':
                # Filtering on a Time range
                return case_filter.filter_case_performance(self.log, self.duration_min, self.duration_max)
        return print(Exception('No mode applied'))

    def set_activity_list(self, act_list=None):
        if act_list:
            self.act_list = act_list


    def filter_on_activity(self, mode_detail, act_list=None):
        self.set_activity_list(act_list)
        match mode_detail:
            case 'start_list':
                    # Here a specific list is used which determines the starting_options
                    # print(start_activities_filter.get_start_activities(log))
                    return start_activities_filter.apply(self.log, self.act_list)
            case 'frequent_list':
                    """
                    @:parameter DECREASING_FACTOR: percentage of Activity occurring - help!
                    --> 700/1000 = 0.7
                    --> 400/1000 = 0.4
                    """
                    filter_list_any = start_activities_filter.get_start_activities(
                        self.log, parameters={start_activities_filter.Parameters.DECREASING_FACTOR: 10000})
                    filter_list = []
                    for f in filter_list_any.keys():
                        filter_list.append(f)
                    return start_activities_filter.apply(self.log, self.act_list)
            case 'end_list':
                    # filter on end activities
                    return end_activities_filter.apply(self.log, self.act_list)

    def set_attr(self, attribute_list=[], attr_col='', lower_bound=0, upper_bound=0):
        if attribute_list:
            if type(attribute_list) == str:
                self.attr_list = [].append(attribute_list)
            else:
                self.attr_list = attribute_list
        if attr_col:
            self.attr_col = attr_col
        if lower_bound:
            self.lower_bound = lower_bound
        if upper_bound:
            self.upper_bound = upper_bound

    def filter_on_attr(self, mode, attr_list=[], attr_col='', lower_bound=0, upper_bound=0):
        self.set_attr(attr_list, attr_col, lower_bound, upper_bound)
        match mode:
            case 'attr_whole_events':
                # filters the event_log where parameter=['Gerald'] is included - str
                # returns THE WHOLE event_log
                return attributes_filter.apply(self.log, self.attr_list,
                                               parameters={attributes_filter.Parameters.ATTRIBUTE_KEY: self.attr_col,
                                                           attributes_filter.Parameters.POSITIVE: True})
            case 'attr_single_events':
                # filters the event_log where parameter=['Gerald'] is included - str
                # returns single_events (PART) of event_logs
                return attributes_filter.apply_events(self.log, self.attr_list,
                                                      parameters={
                                                          attributes_filter.Parameters.ATTRIBUTE_KEY: self.attr_col,
                                                          attributes_filter.Parameters.POSITIVE: True})
            case 'lower_upper_whole_events':
                # filters the event for the range between lower_bound and upper_bound (INCLUDING BOTH) - int
                # returns THE WHOLE event_log
                return attributes_filter.apply_numeric(self.log, self.lower_bound, self.upper_bound,
                                                       parameters={
                                                           attributes_filter.Parameters.ATTRIBUTE_KEY: self.attr_col})
            case 'lower_upper_single_events':
                # filters the event for the range between lower_bound and upper_bound (INCLUDING BOTH) - int
                # returns single_events (PART) of event_logs
                return attributes_filter.apply_numeric_events(self.log, self.lower_bound, self.upper_bound,
                                                              parameters={
                                                                  attributes_filter.Parameters.ATTRIBUTE_KEY: self.attr_col})


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
        activities: dict[any, int] = attributes_filter.get_attribute_values(log, "concept:name")
        resources = attributes_filter.get_attribute_values(log, "org:resource")
        actors = attributes_filter.get_attribute_values(log, "actor")
        labels = attributes_filter.get_attribute_values(log, "label")
        descriptions = attributes_filter.get_attribute_values(log, "description")
        return activities, resources, actors, labels, descriptions

    match mode.lower():

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
                        return pm4py.filter_trace(lambda x: len(x["concept:name"]) % 2 == 0, filtered_case)
            # generic filtering on
    print(f'Wrong value of mode {mode_detail} min is 1, max 7\n Error is passed no filter applied')
    raise ValueError(f'Wrong value of mode {mode_detail} min is 1, max 7\n Error is passed no filter applied')