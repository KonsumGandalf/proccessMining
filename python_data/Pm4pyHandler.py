"""
Importing non pm4py functions
"""
import pandas as pd
import math

"""
Base import
"""

"""
Importing all converting functions
"""
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.conversion.log import converter as log_converter

"""
Importing all statistics
"""
from pm4py.statistics.traces.generic.log import case_statistics

"""
Importing all mining functions
"""
from pm4py.algo.discovery.alpha import algorithm as alpha_miner
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.heuristics import algorithm as heuristic_miner
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.objects.conversion.dfg import converter as bpmn_converter_dfg
from pm4py.objects.conversion.process_tree import converter as bpmn_converter_tree
from pm4py.objects.conversion.heuristics_net import converter as bpmn_converter_heu
from pm4py.objects.bpmn.layout import layouter


from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
from pm4py.algo.conformance.tokenreplay import algorithm as token_based_replay
from pm4py.algo.conformance.tokenreplay.diagnostics import duration_diagnostics
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments

"""
Importing visualization tools
"""
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer

"""
Importing evaluation functions
"""
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator

"""
This File will container all algo & visualisation made by PM4PY
- for saving the method in data_handler is used
"""
from python_data.DataIO import save_file


class EntryRating:
    def __init__(self, name: str):
        self.name = name
        self.results, self.alignments = '', ''
        self.score = 0
        self.conformance = None

    def add_to_score(self, score: float):
        self.score += score

    def get_score(self):
        return self.score

    def extend_results(self, results):
        if type(results) == tuple:
            results = str(results)
        self.results += results + '\n'

    def set_conformance(self, conformance_str):
        self.conformance = conformance_str

    def set_alignments(self, alignments_str):
        self.alignments = alignments_str

    def __getitem__(self, full=False):
        if full:
            return '#' * 40 + f'\n\nThe score of {self.name}: {self.score}\n{self.results}\n{self.conformance}\n{self.alignments}\n'
        else:
            return f'\nThe score of {self.name}: {self.score}'


class Pm4pyHandler:
    module_dir = 'Pm4Py'
    """
    Miner Options: ['Alpha', 'Inductive', 'Heuristic']
    :var log: data used for process mining
    :var variant: applies the variant which is used in the visualisers
    Options
        NATIVE = native
        FREQUENCY = native
        PERFORMANCE = performance
        FREQUENCY_GREEDY = native
        PERFORMANCE_GREEDY = performance
        FREQ_TRIPLES = freq_triples
        CASE_ATTRIBUTES = case_attributes
    :var format_img: applies the format which is used for saving - Options ['svg', 'png'] - I dont implement this
    """

    def __init__(self, log, variant='FREQUENCY', format_img='svg', session_dir='', parameters=None):
        if type(log) == pd.DataFrame:
            parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'case:concept:name'}
            self.log = log_converter.apply(log, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)
        else:
            self.log = log
        self.variant = variant
        self.parameters = parameters
        self.session_dir = session_dir
        """
        This feature is temporarily disabled since it doesnt work correctly
        
        match format_img:
            case 'svg': self.parameters = {dfg_visualizer.Variants.PERFORMANCE.value.Parameters.FORMAT: "svg",
                                           pn_visualizer.Variants.PERFORMANCE.value.Parameters.FORMAT: "svg"}
            case 'png': self.parameters = {dfg_visualizer.Variants.PERFORMANCE.value.Parameters.FORMAT: "png",
                                           pn_visualizer.Variants.PERFORMANCE.value.Parameters.FORMAT: "png"}
        
        self.parameters = self.parameters | parameters                                   
        """

    def update_log(self, log) -> None:
        self.log = log

    def update_variant(self, variant) -> None:
        """
        :param variant: Options: ['FREQUENCY', 'PERFORMANCE']
        :return:
        """

        self.variant = variant

    def update_parameters(self, parameters, replace=True) -> None:
        """
        Merge parameters - dict
        https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-take-union-of-dictionari
        """
        if replace:
            self.parameters = parameters
        else:
            self.parameters = self.parameters | parameters

    def get_data(self, variant):
        match variant.lower():
            case 'dataframe':
                return log_converter.apply(self.log, parameters=self.parameters,
                                           variant=log_converter.Variants.TO_DATA_FRAME)
            case 'event_log':
                return log_converter.apply(self.log, parameters=self.parameters,
                                           variant=log_converter.Variants.TO_EVENT_LOG)

    def alpha_processing(self, version='base'):
        """
        Finds
        A Petri net model where all the transitions are visible
        and unique and correspond to classified events (for example, to activities).

        initial and final marking

        variants:
            Variants.ALPHA_VERSION_CLASSIC - shows everything
            Variants.ALPHA_VERSION_PLUS - cuts down to the most important ones
        """
        match version.lower():
            case 'base':
                net, initial_marking, final_marking = alpha_miner.apply(self.log,
                                                                        variant=alpha_miner.Variants.ALPHA_VERSION_CLASSIC)
            case 'plus':
                net, initial_marking, final_marking = alpha_miner.apply(self.log,
                                                                        variant=alpha_miner.Variants.ALPHA_VERSION_PLUS)
            case _:
                net, initial_marking, final_marking = alpha_miner.apply(self.log,
                                                                        variant=alpha_miner.Variants.ALPHA_VERSION_CLASSIC)

        return net, initial_marking, final_marking

    def alpha_visualization(self, net, ini_mark, fin_mark):
        return self.petri_net_visualization((net, ini_mark, fin_mark))


    def petri_net_visualization(self, petri_compose):
        """
        :param net
        :param ini_mark
        :param fin_mark
        :return: processes the diagram - gviz, visualises and shows it
        """
        net, ini_mark, fin_mark = petri_compose
        match self.variant:
            case 'PERFORMANCE':
                local_variant = pn_visualizer.Variants.PERFORMANCE
            case 'FREQUENCY':
                local_variant = pn_visualizer.Variants.FREQUENCY
            case _:
                local_variant = pn_visualizer.Variants.PERFORMANCE_GREEDY
        gviz = pn_visualizer.apply(net, ini_mark, fin_mark,
                                   variant=local_variant, parameters=self.parameters, log=self.log)
        pn_visualizer.view(gviz)
        return gviz

    def inductive_processing(self, mode_detail: str = 'process_tree', tree=None, variant: str = ""):
        """
           The basic idea of Inductive Miner is about detecting a 'cut' in the self.log
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
        match variant.lower():
            case 'im':
                variant = inductive_miner.Variants.IM
            case 'imf':
                variant = inductive_miner.Variants.IMf
            case 'imd':
                variant = inductive_miner.Variants.IMd
            case _:
                variant = inductive_miner.Variants.IM
        match mode_detail.lower():
            case 'petri_net':
                net, initial_marking, final_marking = inductive_miner.apply(self.log,
                                                                            variant=variant)
                return net, initial_marking, final_marking
            case 'process_tree':
                # Process Tree
                tree = inductive_miner.apply_tree(self.log, variant=variant)
                return tree
            case 'convert':
                if tree:
                    # Converting a tree in a net
                    net, initial_marking, final_marking = pt_converter.apply(tree=tree,
                                                                             variant=pt_converter.Variants.TO_PETRI_NET)
                    return net, initial_marking, final_marking
                    # Converting a net in a tree - no found resource - please add

    def inductive_visualization(self, tree):
        """
        :return: processes the diagram - gviz, visualises and shows it
        """
        # Possible net, ini_mark, fin_mark = pt_converter.apply(tree, variant=pt_converter.Variants.TO_PETRI_NET)
        gviz = pt_visualizer.apply(tree, parameters=self.parameters)
        pt_visualizer.view(gviz)
        return gviz

    def heuristic_processing(self, mode_detail: str = 'heuristic_net'):
        """
            Finds Petri-Net - Directly-Follows Graph - dependency graph
                        Noise Tolerant

            mode_detail options:
                'petri_net' - useful to combine with a petri visualization
                'heu_net' - default due to the heuristic visualization flow

            Possible Parameters:
                DEPENDENCY_THRESH	dependency threshold of the Heuristics Miner (default: 0.5) - Abhängigkeitsschwelle
                AND_MEASURE_THRESH	AND measure threshold of the Heuristics Miner (default: 0.65) - AND-Maßnahmeschwelle
                MIN_ACT_COUNT	minimum number of occurrences of an activity to be considered (default: 1) - Mindestanzahl Aktivitäten
                MIN_DFG_OCCURRENCES	minimum number of occurrences of an edge to be considered (default: 1) - Mindestanzahl Kanten
                DFG_PRE_CLEANING_NOISE_THRESH	cleaning threshold of the DFG (in order to remove weaker edges, default 0.05) - Reinigungsschwelle der DFG
                LOOP_LENGTH_TWO_THRESH	thresholds for the loops of length 2 - Schwellenwerte für Schleifenlänge

    """
        # default parameter - iterables shouldn't be in the function head
        match mode_detail:
            case 'petri_net':
                net, im, fm = heuristic_miner.apply(self.log, parameters=self.parameters)
                return net, im, fm
            case 'heuristic_net':
                heu_net = heuristic_miner.apply_heu(self.log, parameters=self.parameters)
                return heu_net

    def heuristic_visualization(self, heu_net):
        """
        :return: processes the diagram - gviz, visualises and shows it
        """
        gviz = hn_visualizer.apply(heu_net, parameters=self.parameters)
        hn_visualizer.view(gviz)
        return gviz

    def dfg_processing(self, variant=None):
        """
        Directly-Follows Graph

        :returns processes the diagram - gviz, visualises and shows it
        """
        if variant:
            self.variant = variant
        match self.variant:
            case 'PERFORMANCE':
                dfg = dfg_discovery.apply(self.log, variant=dfg_discovery.Variants.PERFORMANCE,
                                          parameters=self.parameters)
            case 'FREQUENCY':
                dfg = dfg_discovery.apply(self.log, variant=dfg_discovery.Variants.FREQUENCY,
                                          parameters=self.parameters)
            case _:
                dfg = dfg_discovery.apply(self.log, variant=dfg_discovery.Variants.NATIVE, parameters=self.parameters)
        return dfg

    def dfg_visualization(self, dfg_variant):
        """
        :return: processes the diagram - gviz, visualises and shows it
        """
        match self.variant:
            case 'PERFORMANCE':
                gviz = dfg_visualizer.apply(dfg_variant, log=self.log, variant=dfg_visualizer.Variants.PERFORMANCE,
                                            parameters=self.parameters)
            case 'FREQUENCY':
                gviz = dfg_visualizer.apply(dfg_variant, log=self.log, variant=dfg_visualizer.Variants.FREQUENCY,
                                            parameters=self.parameters)
            case _:
                gviz = dfg_visualizer.apply(dfg_variant, log=self.log, variant=dfg_visualizer.Variants.PERFORMANCE,
                                            parameters=self.parameters)
        dfg_visualizer.view(gviz)
        return gviz

    def save_file(self, file, filename: str, session_dir=None, add_dir=None, add_dir_2=None,  mode=''):
        """
        heuristic nets cant be saved!
        :param self.format already determines in apply the format
        :param filename:
        :param file: file which is saved
        :return:
        """
        if session_dir:
            self.session_dir = session_dir

        if add_dir:
            self.module_dir = add_dir

        save_file(file, filename, self.session_dir, self.module_dir, add_dir_3=add_dir_2, mode=mode)

    def rating_net_model(self, p_net_compose, name: str = '', output=True, isConformance=False, isAlignments=False,
                         isScore=False):
        """
        This function should give an overview of the performance of the petri_net
        :param p_net_compose:
        :param output: print the returned objects
        :param isConformance -> conformance calculated
        :param isAlignments -> Alignment calculated
        :return: the fitness, precision, generalization, simplicity
        """

        net, im, fm = p_net_compose

        fitness = replay_fitness_evaluator.apply(self.log, net, im, fm,
                                                 variant=replay_fitness_evaluator.Variants.TOKEN_BASED)

        prec = precision_evaluator.apply(self.log, net, im, fm,
                                         variant=precision_evaluator.Variants.ETCONFORMANCE_TOKEN)

        gen = generalization_evaluator.apply(self.log, net, im, fm)

        simp = simplicity_evaluator.apply(net)

        fitness = replay_fitness_evaluator.apply(self.log, net, im, fm,
                                                 variant=replay_fitness_evaluator.Variants.TOKEN_BASED)

        e1 = EntryRating(name=name)

        result = [('Fitness: ', fitness), ('Precision: ', prec), ('Generalization ', gen), ('Simplicity ', simp)]

        for ele in result:
            e1.extend_results(ele)
            if type(ele[1]) == float:
                e1.add_to_score(ele[1])
            else:
                # fitness contains 4 values => /4
                e1.add_to_score(sum(item if item < 1 else item / 100 for item in ele[1].values()) / 4)
        if isConformance:
            e1.set_conformance(
                self.conformance_checking(p_net_compose, just_string=True, conformance_mode='token-based-replay'))
        if isAlignments:
            e1.set_alignments(self.conformance_checking(p_net_compose, just_string=True, conformance_mode='alignments'))

        if output:
            print(e1.__getitem__(full=True))
            if isConformance: print('Conformance', e1.conformance)
            if isAlignments: print('Alignment', e1.alignments)

        if isScore == True:
            return e1.get_score(), e1.__getitem__(full=True)

        return result

    def rating_best_model(self, output_full=False, focus_attr='all', file_name=None, session_dir=None, add_suffix=''):
        """
        Uses the Models of Alpha, Inductive and Heuristic Processing
        - > returns the outputs to console and csv
        - > returns also a winner
        :param file_name: saves the result using save_file(filename) - using it as param
        :param add_dir: above - optional param
        :param focus_attr: stresses one object - which is then the only focused on
        :param output_full: print the returned objects with all attributes
        :var petri_net_list: contains the net, ini and final marking with the name
            -> set (net, ini_mark and fin_mark)
        """
        petri_net_list = []

        """
        :var heu_parameter_list: heuristic miner applies different number-based Parameters -> pre_defined_list
        alpha & inductive does not have
        """

        heu_parameter_list = [
            ('0-6_3_3',
             {
                 heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.6,
                 heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 3,
                 heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 3
             }),
            ('0-8_30_30', {
                heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.9,
                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 30,
                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 30
            }),
            ('0-9_300_300', {
                heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.90,
                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 300,
                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 300
            }),
            ('0-99_3000_3000', {
                heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.99,
                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 3000,
                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 3000
            })
        ]

        for name, par in heu_parameter_list:
            self.update_parameters(par, replace=True)
            petri_net_list.append((f'heuristic+{name}', self.heuristic_processing('petri_net')))
        petri_net_list.append(('alpha', self.alpha_processing()))
        petri_net_list.append(('inductive_im', self.inductive_processing(mode_detail='petri_net', variant='im')))
        petri_net_list.append(('inductive_imd', self.inductive_processing(mode_detail='petri_net', variant='imf')))
        petri_net_list.append(('inductive_imf', self.inductive_processing(mode_detail='petri_net', variant='imd')))

        rating_list = []

        for idx, (model_name, petri_net) in enumerate(petri_net_list):
            e1 = EntryRating(name=model_name)
            print('for1')
            for result in self.rating_net_model(petri_net, name=model_name, output=False):
                e1.extend_results(result)
                if focus_attr == 'all' or focus_attr in result[0].lower():
                    if type(result[1]) == float:
                        e1.add_to_score(result[1])
                    else:
                        # fitness contains 4 values => /4
                        e1.add_to_score(sum(item if item < 1 else item / 100 for item in result[1].values()) / 4)
            # e1.set_conformance(
            #    self.conformance_checking(petri_net, just_string=True, conformance_mode='token-based-replay'))
            # e1.set_alignments(self.conformance_checking(petri_net, just_string=True, conformance_mode='alignments'))

            print('for2')
            rating_list.append(e1)
        rating_list = sorted(rating_list, key=lambda item: item.score, reverse=True)

        print('for3')
        if output_full:
            for item in rating_list:
                print(item.__getitem__(full=output_full))

        if file_name:
            from datetime import date
            self.save_file(file=''.join(item.__getitem__(full=True) + '\n' for item in rating_list),
                           filename=f'{date.today()}_{file_name}{add_suffix}', session_dir=session_dir,
                           add_dir='Pm4Py',add_dir_2='Rating')

        return rating_list

    def bpmn_dealer(self,io_name,tree):
        gviz = layouter.apply(bpmn_converter_tree.apply(tree=tree, variant=bpmn_converter_tree.Variants.TO_BPMN))
        gviz2 = bpmn_converter_tree.apply(tree=tree, variant=bpmn_converter_tree.Variants.TO_BPMN)
        self.save_file(gviz, filename=io_name+'_process_tree', add_dir_2=io_name, mode='bpmn')
        self.save_file(gviz2, filename=io_name + '_process_tree2', add_dir_2=io_name, mode='bpmn')


    def local_visualization(self, io_name, inductive_variant='', alpha=False, heu_set=(), pareto_log=False):
        if pareto_log:
            petri_net = self.inductive_processing(mode_detail='petri_net', variant=inductive_variant)
            gviz = self.petri_net_visualization(petri_net)
            self.save_file(gviz, filename=f'pareto_petri_net_{inductive_variant}', add_dir_2=io_name)
        else:
            if inductive_variant:
                petri_net = self.inductive_processing(mode_detail='petri_net', variant=inductive_variant)
                gviz = self.petri_net_visualization(petri_net)
                self.save_file(gviz, filename=f'petri_net_{inductive_variant}', add_dir_2=io_name)
            if alpha:
                petri_net = self.alpha_processing('base')
                gviz = self.petri_net_visualization(petri_net)
                self.save_file(gviz, filename='petri_net_alpha', add_dir_2=io_name)
            if len(heu_set):
                try:
                    print(heu_set)
                    self.update_parameters({heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: heu_set[0],
                                        heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: heu_set[1],
                                        heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: heu_set[2]},
                                       replace=True)
                    petri_net = self.heuristic_processing(mode_detail='petri_net')
                    gviz = self.petri_net_visualization(petri_net)
                    self.save_file(gviz, filename=f'petri_net_{heu_set[1]}_{heu_set[2]}', add_dir_2=io_name)
                except UnboundLocalError:
                    print('petri_net failed due to the high MIN_ACT')

        process_tree = self.inductive_processing(mode_detail='process_tree', variant=inductive_variant)
        gviz = self.inductive_visualization(process_tree)
        self.save_file(gviz, filename='process_tree', add_dir_2=io_name)

        variant_dfg = 'FREQUENCY'
        dfg = self.dfg_processing(variant=variant_dfg)
        gviz = self.dfg_visualization(dfg)
        self.save_file(gviz, filename='dfg', add_dir_2=io_name)
        self.bpmn_dealer(io_name, process_tree)



    def visualize_diagram(self, session_dir, add_dir_2='', add_suffix=''):
        """
        This Methode is supposed to simulate the difference of the various diagrams

        heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: Defines the Activity
        :return:
        """

        self.update_parameters({heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.6,
                                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: 30,
                                heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: 30},
                               replace=True)

        """
        Inductive_processing: Variant IM vs IMf vs IMd of 
        """
        variant_list = ['IM', 'IMf', 'IMd']
        for var in variant_list:
            p_tree = self.inductive_processing(mode_detail='process_tree', variant=var)
            gviz = self.inductive_visualization(p_tree)
            self.save_file(gviz, filename=f'{var}', session_dir=session_dir, add_dir_2=add_dir_2,
                           add_dir=f'Inductive_processing{add_suffix}')

        """
        Inductive_processing: Petri net == Petri net out of a process tree  
        """
        self.petri_net_visualization(self.inductive_processing('petri_net'))
        self.petri_net_visualization(
            self.inductive_processing(mode_detail='convert',
                                      tree=self.inductive_processing(f'process_tree{add_suffix}')))

        """
        Heuristic_processing: petri_net vs heuristic_net
        heuristic nets cant be saved!
        """
        heu_petri_net = self.heuristic_processing('petri_net')
        gviz = self.petri_net_visualization(heu_petri_net)
        self.save_file(gviz, filename=f'petri_net', session_dir=session_dir, add_dir_2=add_dir_2,
                       add_dir=f'Heuristic_processing{add_suffix}')

        heuristic_net = self.heuristic_processing('heuristic_net')
        gviz = self.heuristic_visualization(heuristic_net)
        """heuristic nets cant be saved!
        self.save_graphic(gviz, filename=f'Heuristic_processing_heuristic_net')"""

        """
        Alpha vs Heuristic Processing: Petri-net
        """
        alpha_petri_net = self.alpha_processing()
        # heu_petri_net = self.heuristic_processing('petri_net') - above
        gviz = self.petri_net_visualization(alpha_petri_net)
        self.save_file(gviz, filename=f'petri_net', session_dir=session_dir, add_dir=f'Alpha_processing{add_suffix}'
                       , add_dir_2=add_dir_2)
        self.petri_net_visualization(heu_petri_net)

        """
        DFG Processing: PERFORMANCE vs FREQUENCY
        """
        dfg_performance = self.dfg_processing('PERFORMANCE')
        dfg_frequency = self.dfg_processing('FREQUENCY')
        gviz = self.dfg_visualization(dfg_performance)
        self.save_file(gviz, filename=f'performance', session_dir=session_dir, add_dir=f'DFG_processing{add_suffix}'
                       , add_dir_2=add_dir_2)
        gviz = self.dfg_visualization(dfg_frequency)
        self.save_file(gviz, filename=f'frequency', session_dir=session_dir, add_dir=f'DFG_processing{add_suffix}'
                       , add_dir_2=add_dir_2)

    def conformance_checking(self, model, conformance_mode='all', just_string=True):
        """
        Documentation: https://pm4py.fit.fraunhofer.de/documentation#conformance

        Conformance checking - process model vs event log -> Discover odd behaviour
        token-based replay and alignments
        :param just_string
        :param model which is used for checking
            -> match type -> decides over later steps

        Types of models:
            tuple - petri net - print(type(self.alpha_processing()))
            pm4py.objects.heuristics_net.obj.HeuristicsNet - print(type(self.heuristic_processing('heuristic_net')))
            pm4py.objects.process_tree.obj.ProcessTree - print(type(self.inductive_processing('process_tree')))
            collections.Counter - dfg - print(type(self.dfg_processing()))

        Token-based replay matches a trace and a Petri net model
        :return an attribute_dict of = ['trace_is_fit', 'activated_transitions', 'reached_marking', 'missing_tokens',
                                        'consumed_tokens', 'remaining_tokens', 'produced_tokens'] - keys in list_format
        -> remaining
        -> missing tokens dont fit
            formula:
            (p)roduced tokens, (r)emaining tokens, (m)issing tokens, and (c)onsumed tokens - petri net (n) and a trace (t) are given as input:
            fitness(n, t)=1⁄2(1-r⁄p)+1⁄2(1-m⁄c)

            between 2 transition:
            -> visible
            -> hidden - fired in order to enable the visible transition. The hidden transitions are then fired and a marking that permits to enable the visible transition is reached.
        """
        if type(model) == tuple:
            net, initial_marking, final_marking = model
            match conformance_mode.lower():
                case 'token-based-replay':
                    replayed_traces = token_replay.apply(self.log, net, initial_marking, final_marking)

                    anomalous_traces_dict = {}
                    case_list_str = ''
                    identifier_str = 'none'
                    anomalous_counter = 1
                    for idx, item in enumerate(replayed_traces):
                        if item["trace_fitness"] != 1.0:
                            # check if the transition issue has be tracked once
                            if identifier_str in anomalous_traces_dict:
                                missing_token_counter = item['missing_tokens'] + anomalous_traces_dict['missing_tokens']
                                anomalous_counter = anomalous_traces_dict['counter_anomalous_traces'] + 1
                                case_list_str += ', ' + str(self.log[idx].attributes['concept:name'])
                            else:
                                missing_token_counter = item['missing_tokens']
                                anomalous_counter = 1
                                case_list_str = str(self.log[idx].attributes['concept:name'])
                                for ele in item['transitions_with_problems']:
                                    identifier_str += str(ele) + ' '
                            anomalous_traces_dict = {identifier_str: identifier_str,
                                                     'missing_tokens': missing_token_counter,
                                                     'case_list': case_list_str,
                                                     'counter_anomalous_traces': anomalous_counter}
                        if idx == (case_log_length := len(self.log)) - 1:
                            percentage = str(anomalous_counter / case_log_length * 100) + '%'
                            anomalous_traces_dict['percentage_anomalous_traces'] = percentage

                    if just_string:
                        anomalous_traces_str = 'Conformance_checking: ' + '\n'
                        for key in anomalous_traces_dict.keys():
                            anomalous_traces_str += str(key) + ': ' + str(anomalous_traces_dict[key]) + '\n'
                        return anomalous_traces_str

                    return replayed_traces, anomalous_traces_dict
                case 'diagnostics':
                    """
                    detailed information about until thursday - skipped
                    """
                    parameters_tbr = {token_based_replay.Variants.TOKEN_REPLAY.value.Parameters.DISABLE_VARIANTS: True,
                                      token_based_replay.Variants.TOKEN_REPLAY.value.Parameters.ENABLE_PLTR_FITNESS: True}
                    replayed_traces, place_fitness, trans_fitness, unwanted_activities = token_based_replay \
                        .apply(self.log, net, initial_marking, final_marking, parameters=parameters_tbr)
                    print('replayed\n', replayed_traces, 'place_fitness\n', place_fitness, 'trans_fitness\n',
                          trans_fitness, 'unwanted_activities\n', unwanted_activities)

                    trans_diagnostics = duration_diagnostics.diagnose_from_trans_fitness(self.log, trans_fitness)
                    for trans in trans_diagnostics:
                        print('trans', trans, trans_diagnostics[trans])

                case 'alignments':
                    """
                    Linear solvers: PuLP, CVXOPT
                    Classification system via Alignment-based replay
                    - > 'Sync move': transition label; trace and the model advance same way => FITS
                    - > 'Move on log': replay move in the trace that is not presented in the model
                    - > 'Move on model': replay move in the model that is not presented in the trace
                        - > Moves on model involving hidden transitions: NOT a sync move, but move FITS
                        - > Moves on model involving not involving hidden transitions: NOT a sync move, move NOT FITS
                       => signals a deviation between the trace and the model.
                       
                    
                    """
                    try:
                        aligned_traces = alignments.apply_log(self.log, net, initial_marking, final_marking)

                    except Exception:
                        print(Exception("trying to apply alignments on a Petri net that is not a easy sound net!!"))
                    anomalous_traces_dict = {}
                    case_list_str = ''
                    identifier_str = 'none'
                    anomalous_counter = 1
                    """
                    lowest_cost_no_fit: lowest cost of not fitting
                    idx_lowest_cost_no_fit: idx of lowest cost of not fitting
                    lowest_fitness_no_fit: lowest fitness of not fitting
                    idx_lowest_fitness_no_fit: idx of cost of lowest fitting 
                    sum_cost_no_fit: later dedicated with average cost
                    """
                    import sys
                    (lowest_cost_no_fit, idx_lowest_cost_no_fit), (lowest_fitness_no_fit, idx_lowest_fitness_no_fit) = (
                                                                                                                           sys.maxsize,
                                                                                                                           0), (
                                                                                                                           sys.maxsize,
                                                                                                                           0)
                    sum_cost_no_fit, list_no_fit = 0, []
                    (highest_cost_no_fit, idx_highest_cost_no_fit), (
                        highest_fitness_no_fit, idx_highest_fitness_no_fit) = (0, 0), (0, 0)
                    (lowest_cost_fit, idx_lowest_cost_fit) = (sys.maxsize, 0)
                    (highest_cost_fit, idx_highest_cost_fit) = (0, 0)
                    sum_cost_fit, list_fit = 0, []
                    case_list_str = ''
                    regular_traces, irregular_traces = [], []
                    for idx, item in enumerate(aligned_traces):

                        if item["fitness"] == 1.0:
                            sum_cost_fit += item['cost']
                            list_fit.append(self.log[idx].attributes['concept:name'])
                            regular_traces.append(item['alignment'])

                            if item['cost'] < lowest_cost_fit:
                                lowest_cost_fit = item['cost']
                                idx_lowest_cost_fit = idx
                            elif item['cost'] > highest_cost_fit:
                                highest_cost_fit = item['cost']
                                idx_highest_cost_fit = idx

                        elif item["fitness"] != 1.0:
                            sum_cost_no_fit += item['cost']
                            list_no_fit.append(self.log[idx].attributes['concept:name'])
                            irregular_traces.append(item['alignment'])

                            if item['cost'] < lowest_cost_no_fit:
                                lowest_cost_no_fit = item['cost']
                                idx_lowest_cost_no_fit = idx
                            elif item['cost'] > highest_cost_no_fit:
                                highest_cost_no_fit = item['cost']
                                idx_highest_cost_no_fit = idx

                            if item['fitness'] < lowest_fitness_no_fit:
                                lowest_fitness_no_fit = item['fitness']
                                idx_lowest_fitness_no_fit = idx
                            elif item['fitness'] > highest_fitness_no_fit:
                                highest_fitness_no_fit = item['fitness']
                                idx_highest_fitness_no_fit = idx


                    def get_dict_col(temp_dict, col):
                        new_dict = {}
                        for key in temp_dict.keys():
                            if key in col:
                                new_dict[key] = temp_dict[key]
                        return new_dict

                    print_col_list = ['cost', 'visited_states', 'queued_states', 'traversed_arcs', 'lp_solved',
                                      'fitness', 'bwc']

                    """
                    Important to exclude the size of 0
                    """
                    if (len_list_fit := 1) < len(list_fit):
                        len_list_fit = len(list_fit)
                    if (len_list_no_fit := 1) < len(list_no_fit):
                        len_list_no_fit = len(list_no_fit)
                    anomalous_traces_list = [(
                        f'The following presents the fitting data. Average cost: {sum_cost_fit / len_list_fit}.\nNumber of anomalous traces {len_list_fit}\n'
                        f'Percentage of anomalous traces {len_list_fit / len(aligned_traces) * 100}%\nList of regular data: {list_fit}\n',
                        {'idx_lowest_cost_fit': self.log[idx_lowest_cost_fit].attributes[
                            'concept:name'],
                         'lowest_cost': get_dict_col(aligned_traces[idx_lowest_cost_fit],
                                                     print_col_list)},
                        {'idx_highest_cost_fit': self.log[idx_highest_cost_fit].attributes[
                            'concept:name'],
                         'highest_cost': get_dict_col(aligned_traces[idx_highest_cost_fit],
                                                      print_col_list)}
                    ),
                        (
                            f'The following presents the NOT fitting data. \nAverage cost: {sum_cost_no_fit / len_list_no_fit}.\nNumber of anomalous traces {len_list_no_fit}'
                            f'\nPercentage of anomalous traces {len_list_no_fit / len(aligned_traces) * 100}%\nList of anomalous data: {list_no_fit}\n',
                            {'idx_lowest_cost_no_fit': self.log[idx_lowest_cost_no_fit].attributes[
                                'concept:name'],
                             'lowest_cost': get_dict_col(aligned_traces[idx_lowest_cost_no_fit],
                                                         print_col_list)},
                            {'idx_highest_cost_no_fit': self.log[idx_highest_cost_no_fit].attributes[
                                'concept:name'],
                             'highest_cost': get_dict_col(aligned_traces[idx_highest_cost_no_fit],
                                                          print_col_list)},
                            {'idx_lowest_fitness_no_fit':
                                 self.log[idx_lowest_fitness_no_fit].attributes['concept:name'],
                             'lowest_cost': get_dict_col(aligned_traces[idx_lowest_fitness_no_fit],
                                                         print_col_list)},
                            {'idx_highest_fitness_no_fit':
                                 self.log[idx_highest_fitness_no_fit].attributes['concept:name'],
                             'highest_cost': get_dict_col(aligned_traces[idx_highest_fitness_no_fit],
                                                          print_col_list)},
                        )]

                    anomalous_traces_str = 'Alignments: ' + '\n'
                    for ele in anomalous_traces_list:
                        anomalous_traces_str += '\n'
                        for line in ele:
                            if type(line) == dict:
                                anomalous_traces_str += '\t' + str(line) + '\n'
                            elif type(line) == str:
                                anomalous_traces_str += line
                    if just_string:
                        return anomalous_traces_str
                    else:
                        return regular_traces, irregular_traces, anomalous_traces_str

    def search_best_para_heu_prepare(self, session_dir, io_name=''):
        """
        Requires search_best_parameters_heuristic_recursive!

        Functions search for the best possible heuristic parameters
        logic:
        :var min_act_count is the activity with least of appearances
        :var max_act_count max appearance possible

        -> used is a list sorted due to the activity count -> the most often used acc 0 - last entry == -1 vgl. python list

        later :var min_dfg_count, max_dfg_count are really introduced but normally an act that is started has about the same
        incoming dfg as act itself => param not the same but similar

        :var multiplier - defined by the formula variants_count[floor(len(variants_count) * 0.1)] was suiteable in THIS case
        has to be applied to the other logs - the 10% most used activity
        """

        variants_count = case_statistics.get_variant_statistics(log=self.log)
        variants_count = sorted(variants_count, key=lambda x: x['count'], reverse=True)
        min_act_count, max_act_count = variants_count[-1]['count'], variants_count[0]['count']
        min_dfg_count, max_dfg_count = min_act_count, max_act_count
        multiplier: int = variants_count[math.floor(len(variants_count) * 0.1)]['count']

        score_result = self.search_best_parameters_heuristic_recursive(multiplier, min_act_count, max_act_count
                                                            , min_dfg_count, max_dfg_count,
                                                            (min_act_count, min_dfg_count, 0),
                                                            isinspect=True)
        output_str = f'The best score: {score_result[0]} with the min_act: {score_result[1]} and the min_occ: {score_result[2]}' \
                     f'\nSingle categorizes:\n {score_result[3]}'
        print(output_str)
        """
        All diagrams which can be provided by the pmHandler are visualized 
        """
        try:
            from datetime import date
            self.save_file(file=output_str,
                            filename=f'{io_name}_{date.today()}_heuristic_approximation', session_dir=session_dir,
                            add_dir='Pm4Py', add_dir_2='Rating')
            self.visualize_diagram(session_dir, add_suffix=f'{math.floor(score_result[1])}_{math.floor(score_result[2])}')
        except:
            print('not all defined')

    def search_best_parameters_heuristic_recursive \
                    (self, multiplier: float, min_act, max_act, min_dfg, max_dfg, best_score_and_par: tuple,
                     isinspect=False) -> tuple:
        if isinspect:
            print('multiplier: ', multiplier, '|min act: ', min_act, '|max_act: ', max_act, '|min dfg: ', min_dfg,
                  '|max_dfg: ', max_dfg)
        if (cur_act := min_act) * multiplier < max_act:
            cur_act = min_act * multiplier
        if (cur_dfg := min_act) * multiplier < max_dfg:
            cur_dfg = min_dfg * multiplier
        param = {
            heuristic_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.9,
            heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_ACT_COUNT: cur_act,
            heuristic_miner.Variants.CLASSIC.value.Parameters.MIN_DFG_OCCURRENCES: cur_dfg,
        }
        self.update_parameters(param, replace=True)
        model = self.heuristic_processing('petri_net')
        cur_score, score_str = self.rating_net_model(model, output=True, isConformance=False, isAlignments=False,
                                               isScore=True)
        if cur_score > best_score_and_par[0]:
            return self.search_best_parameters_heuristic_recursive(multiplier, cur_act, max_act, cur_dfg, max_dfg,
                                                                   (cur_score, cur_act, cur_dfg, score_str),
                                                                   isinspect=isinspect)
        else:
            if multiplier < 1.3:
                return best_score_and_par
            multiplier = math.sqrt(multiplier)
            return self.search_best_parameters_heuristic_recursive(multiplier, min_act, max_act, min_dfg, max_dfg,
                                                              best_score_and_par, isinspect=isinspect)


    def apply_pareto_principle(self, percentage_to_hold=0.2):
        from pm4py.algo.filtering.log.variants import variants_filter
        return variants_filter.filter_log_variants_percentage(self.log, percentage=percentage_to_hold)

"""elif type(model) == pm4py.objects.heuristics_net.obj.HeuristicsNet:

    
    
elif type(model) == pm4py.objects.process_tree.obj.ProcessTree:

elif type(model) == collections.Counter:"""
