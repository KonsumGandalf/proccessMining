import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from pm4py.objects.log.obj import EventLog
from pm4py.objects.conversion.log import converter as log_converter

from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization

from python_data.DataIO import save_file

COMPARE = []

class PltPresent:
    """
    mode_list - Options: ['histogram', 'cdf', 'terminal', 'full', 'nothing']
    """
    Mode_list = []
    COLOR_LIST = ['darkorchid', 'limegreen', 'salmon', 'sienna', 'blue', 'green', 'red', 'cyan',
                  'magenta', 'yellow', 'black', 'white']
    cmap_list = plt.colormaps['Pastel2']

    cmap_list = cmap_list(np.arange(2) * 4)

    Dataframe: pd.DataFrame
    X_Col: list = []
    Y_Col: list = []

    Title: str = ''
    X_label: str = ''
    Y_label: str = ''
    cmap: str = ''

    hue: any = None
    x_ticks: list = []
    y_ticks: list = []
    sns_cmap: str

    def __init__(self, data, mode_list, col1='', col2='', title='', x_label='', y_label='', frame_length=100, size=(15, 5), hue='', x_ticks=None, y_ticks=None, cmap='Pastel2', sns_cmap=''):
        self.FRAME_LENGTH = frame_length
        self.size = size

        self.set_data(data=data, mode_list=mode_list, col1=col1, col2=col2)
        self.set_labels(title=title, x_label=x_label, y_label=y_label, cmap=cmap)
        self.set_labels(title=title, x_label=x_label, y_label=y_label, cmap=cmap)
        self.set_ticks(x_ticks=x_ticks,  y_ticks=y_ticks, col1=col1, col2=col2)
        self.set_sns(hue, sns_cmap)

        plt.figure(figsize=size, dpi=80)
        plt.style.use('ggplot')


    def set_labels(self, title='', x_label='', y_label='', cmap='') -> None:
        if title:
            self.Title = title
        if x_label:
            self.X_label = x_label
        if y_label:
            self.Y_label = y_label
        if cmap:
            self.cmap = cmap


    def set_data(self, data, col1='', col2='', mode_list=None):
        """
                Updates the dataframe
                :param col1:
                :param col2:
                :param mode_list
                :param data: Accepts an EventLog or DataFrame as new Dataframe
                :return:
                """
        if type(data) == EventLog:
            self.Dataframe = pd.DataFrame.from_records(data).head(self.FRAME_LENGTH)
        elif type(data) == list:
            self.Dataframe = pd.DataFrame(data).head(self.FRAME_LENGTH)
        else:
            self.Dataframe = data.head(self.FRAME_LENGTH)
        if col1:
            self.X_Col = [str(e).replace("Case ", "") for e in
                      self.Dataframe.index] if col1 == 'index_format' else self.Dataframe[col1]
        if col2:
            self.Y_Col = [str(e).replace("Case ", "") for e in
                      self.Dataframe.index] if col2 == 'index_format' else self.Dataframe[col2]
        if mode_list:
            if type(mode_list) == str:
                mode_list = [].append(mode_list)
            self.Mode_list = mode_list

    def set_ticks(self, x_ticks, y_ticks, col1, col2):
        from math import floor
        def round_down(n, decimals=0):
            multiplier = 10 ** decimals
            return floor(n * multiplier) / multiplier
        if x_ticks:
            self.x_ticks = x_ticks
        """elif col1 == 'index_format':
            len_content = len(self.X_Col)
            steps = round_down(len_content, decimals=len(str(len_content)))
            self.x_ticks = [ele for idx,ele in enumerate(self.X_Col) if (idx%steps)==0]
            print(self.x_ticks)"""
        if y_ticks:
            self.y_ticks = y_ticks
        """
        elif col2 == 'index_format':
            steps = round(len(self.Y_Col) / 10)
            self.y_ticks = [ele for idx, ele in enumerate(self.Y_Col) if (idx % steps) == 0]
            print(self.y_ticks)"""

    def set_sns(self, hue, cmap):
        if hue:
            self.hue = hue
        if cmap:
            self.sns_cmap = sns.color_palette('deeper')

    def save_plt(self, figure, filename: str, session_dir=None, add_dir='plt', diagram_type='', add_dir_3=''):
        """
        :param self.format already determines in apply the format
        :param figure file thats saved
        :param filename: name of file
        :param session_dir directory name of current session
        :param add_dir possible additional directory a hierarchy under the session_dir:
        :param diagram_type
        :var plt.gcf(): current plot figure
        :return:
        """
        save_file(figure, filename, session_dir, program_dir=add_dir, diagram_type=diagram_type, add_dir_3=add_dir_3)

    def addlabels(self):
        for i in range(len(self.X_Col)):
            plt.text(i, self.Y_Col[i], self.Y_Col[i], ha='center')

    def histogram_dealer(self, horizontal=False, two_color_mode=False, values=(0,1)):
        fig, ax = plt.subplots()

        colors = [self.COLOR_LIST[values[0]] if (idx % 2) == 0 else self.COLOR_LIST[values[1]] for idx in range(len(self.X_Col))]
        if horizontal:
            plt.barh(self.X_Col, self.Y_Col, height=0.4, color=colors)
            if two_color_mode:
                plt.barh(self.X_Col, self.Y_Col, height=0.4, color=colors)
        else:
            plt.bar(self.X_Col, self.Y_Col, width=0.4, color=colors)
            if two_color_mode:
                plt.bar(self.X_Col, self.Y_Col, width=0.4, color=colors)
        print(self.X_label, self.Y_label,self.Title)
        plt.xlabel(self.X_label), plt.ylabel(self.Y_label), plt.title(self.Title)
        if horizontal:
            self.addlabels()

        # plt.xticks(self.x_ticks)
        ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=15))
        plt.show()
        return fig


    def cum_pdf_chart(self):
        fig, ax = plt.subplots()
        count, bins_count = np.histogram(self.Y_Col, bins=50)

        # Probability distribution function = PDF
        # Cumulative distribution function = CDF
        pdf = count / sum(count)
        cdf = np.cumsum(pdf)

        plt.plot(bins_count[1:], pdf, color=self.COLOR_LIST[0], label="PDF")
        plt.plot(bins_count[1:], cdf, color=self.COLOR_LIST[1], label="CDF")
        # plt.plot(bins_count[1:], count, color=color_list[2], label="count")
        plt.legend()
        plt.show()

        return fig


    def pie_dealer(self, mode='normal', loc_title='', value_list=None, label_list=None, others=True):
        """
        temporarily just developed for the case 2 list are handed over not a list with 2 values
        """
        self.Title = loc_title
        fig, ax = plt.subplots(figsize=(8, 3), subplot_kw=dict(aspect="equal"))
        if not (value_list and label_list):
            raise KeyError
            # self.set_data(col1=percentage_list, col2=label_list)

        """
        others is part of the standard procedure - but can be disabled for important values
        group the smallest amount of values together the smallest percentage should be shown is 5 % since then the group
        has then a significant impact and the the digit of % is presented smoothly
        """
        if others:
            threshold = sum(value_list) * 0.05
            others_value, v_list, l_list = 0, [], []
            for idx in range(len(value_list)):
                if value_list[idx] >= threshold:
                    v_list.append(value_list[idx]), l_list.append(label_list[idx])
                else:
                    others_value += value_list[idx]
            v_list.append(others_value), l_list.append('others')
            value_list, label_list = v_list, l_list
        match mode.lower():
            case 'pie':
                wedges, texts, autotexts = ax.pie(value_list, autopct='%1.1f%%',
                                                  textprops=dict(color='w'))

                ax.legend(wedges, label_list,
                          title="Ingredients",
                          bbox_to_anchor=(1, 0, 0.5, 1))

                plt.setp(autotexts, size=6, weight="bold")

            case 'donut':
                wedges, texts = ax.pie(value_list, wedgeprops=dict(width=0.5), startangle=0)

                bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
                kw = dict(arrowprops=dict(arrowstyle="-"),
                          bbox=bbox_props, zorder=0, va="center")

                for i, p in enumerate(wedges):
                    ang = (p.theta2 - p.theta1) / 2. + p.theta1
                    y = np.sin(np.deg2rad(ang))
                    x = np.cos(np.deg2rad(ang))
                    horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
                    connectionstyle = "angle,angleA=0,angleB={}".format(ang)
                    kw["arrowprops"].update({"connectionstyle": connectionstyle})
                    ax.annotate(label_list[i], xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                                horizontalalignment=horizontalalignment, **kw)

        plt.title(self.Title)
        plt.show()
        return fig

    def scatterplot(self, x_ticks=None, y_ticks=None):
        """
        Options:
            :param - hue
        :return:
        """
        if x_ticks:
            plt.xticks(x_ticks)
        else:
            plt.yticks(np.arange(min(self.y_ticks), max(self.y_ticks) + 1, 5))
        ax = sns.scatterplot(x=self.X_Col,
                             y=self.Y_Col, hue=self.Dataframe[self.hue])
        plt.show()

    def heatmap(self):
        """
        documentation: https://seaborn.pydata.org/generated/seaborn.heatmap.html
        Options:
            :param - data
            :param - vmin, vmax - Highest/Lowest value
            :param - cmap - sns.color_palette(value)
                value = {"tab10", "rocket", "muted", pastel, bright, dark, colorblind}
                as_cmap=True/False

        :return:
        """
        patient_events = pd.crosstab(index=self.X_Col,
                    columns=self.Y_Col)
        sns.heatmap(data=patient_events, cmap=self.sns_cmap)
        plt.show()

    """    def violin_dealer(self):
        plt.violinplot()"""

    def pandas_full_presentation(self):
        with pd.option_context('display.max_rows', 10, 'display.max_columns', None, 'display.width', None):
            print(self.Dataframe)

    def apply(self):
        for mode in self.Mode_list:
            match mode:
                case 'histogram':
                    self.histogram_dealer()
                case 'cdf':
                    self.cum_pdf_chart()
                case 'terminal':
                    self.pandas_full_presentation()
                case 'plt':
                    self.histogram_dealer()
                    self.cum_pdf_chart()
                    self.pandas_full_presentation()
                case 'pie':
                    self.pie_dealer()
                case 'sns':
                    self.scatterplot()
                case 'heatmap':
                    self.heatmap()
                case 'full':
                    self.histogram_dealer()
                    self.cum_pdf_chart()
                    self.pandas_full_presentation()
                    self.scatterplot()
                    self.heatmap()
                case _:
                    print('Mode nothing has been chosen!')


