import PySimpleGUI as sg

import matplotlib
matplotlib.use("Agg")  # Set backend to Agg to prevent figure from appearing as a separate window
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np
import math
from scipy.stats import weibull_min
import textwrap
import random
import pandas as pd

from tqdm import tqdm
import warnings
import logging
import os

'''
change status of red to orange to avoid confusion with CM
'''

# Create the folder for saving the figures
figure_results_save_folder_name = 'figure_results_save'
figure_results_save_folder_path = os.path.join(os.getcwd(), figure_results_save_folder_name)
if not os.path.exists(figure_results_save_folder_path):
    os.makedirs(figure_results_save_folder_name)

figure_path_inv_map = os.path.join(os.getcwd(), 'figure_inv_map')
if not os.path.exists(figure_path_inv_map):
    os.makedirs(figure_path_inv_map)

logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
'''
# logging level
# logger.debug('Here you have some information for debugging.')
# logger.info('Everything is normal. Relax!')
# logger.warning('Something unexpected but not important happend.')
# logger.error('Something unexpected and important happened.')
# logger.critical('OMG!!! A critical error happend and the code cannot run!')
'''
# our first handler is a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler_format = '%(asctime)s | %(levelname)s: %(message)s'
console_handler.setFormatter(logging.Formatter(console_handler_format))
logger.addHandler(console_handler)

# the second handler is a file handler
file_handler = logging.FileHandler('Log_GUI.log')
file_handler.setLevel(logging.DEBUG)
file_handler_format = '%(asctime)s | %(levelname)s | %(lineno)d: %(message)s'
file_handler.setFormatter(logging.Formatter(file_handler_format))
logger.addHandler(file_handler)


EUR_population = 0.0148
scale_population = 2598.1437157518835

sites = pd.read_excel('site_location.xlsx')
status_table_invID = [x for x in range(1,11)]
status_table_color = ['green']*10
status_table_RUL = [2100]*10
status_table_maint = [1800]*10
# for it in range(len(status_table_color)):
#     if status_table_RUL[it] <=400:
#         status_table_color[it] = 'orange'
#     elif status_table_RUL[it] <= 1000:
#         status_table_color [it] = 'yellow'
#     else:
#         status_table_color [it] = 'green'

status_table_df = pd.DataFrame(
    {'INV_ID': status_table_invID,
     'Status': status_table_color,
     'RUL': status_table_RUL,
     'Maint.': status_table_maint
    })

from inv_simulation import inv_simulation, dist_prep, dmc_prep
from draw_plot import draw_plot_f1, draw_plot_f2, draw_plot_skip, draw_plot_status, draw_plot_map



# Choose a Theme for the Layout
sg.theme('DefaultNoMoreNagging')
# sg.theme('Python')
# sg.set_options(scaling=0.8)

# Define the layout of the GUI

NAME_SIZE = 30
def name(name):
    dots = NAME_SIZE-len(name)+10
    return sg.Text(name + ' ' + ' '*dots, size=(NAME_SIZE,1), justification='l',pad=(0,0), font=('Helvetica', 10))

# Define the list of preventive cost
preventive_maintenance_cost_list = [1500, 3000, 4500, 6000, 7500, 9000]
corrective_maintenance_cost_list = [1500, 3000, 4500, 6000, 7500, 9000]

figsize = (6, 4)
inv_title_size = 12
slider_size = (14, 15)  # (width, height)



# Create the first window
while True:

    # Define the layout for the first window
    layout1 = [
        [sg.Push(), sg.Text('Fleet Management Tool for Solar Inverters - Input', font=('Helvetica', 24), justification='c', expand_x=True), sg.Push()],
        [sg.HSep()],
        [sg.Push(), sg.Text('Scenario Setup', font=("Helvetica", 18, "bold")), sg.Push()],
        [name('Preventive Maintenance Cost ($)'), sg.Combo(preventive_maintenance_cost_list, default_value=preventive_maintenance_cost_list[0], s=(15, 20), enable_events=False, readonly=True, k='-pmc_inv1-')],
        [name('Corrective Maintenance Cost ($)'), sg.Combo(corrective_maintenance_cost_list, default_value=corrective_maintenance_cost_list[3], s=(15, 20), enable_events=False, readonly=True, k='-cmc_inv1-')],
        [sg.HSep()],

        [sg.Push(), sg.Button("Start Simulation", size=(30, 2), key="-window_next-"), sg.Push()],

        [sg.Push(), sg.Button("Start Simulation (skip visualization)", size=(30, 2), key="-window_skip-"), sg.Push()],

        [sg.Sizer(1, 40)],
        [sg.HSep()],
        [sg.Text(
            'This tool is based upon work supported by the U.S. Department of Energy',
            font=('Helvetica', 10), justification='r', expand_x=True)],
        [sg.Text(
            'Office of Energy Efficiency and Renewable Energy (EERE)',
            font=('Helvetica', 10), justification='r', expand_x=True)],
        [sg.Text(
            'under the Solar Energy Technologies Office Award Number 39640.',
            font=('Helvetica', 10), justification='r', expand_x=True)],
    ]

    window1 = sg.Window('Fleet Management Tool for Solar Inverters - Input', layout1, resizable=True)

    # event1, values1 = window1.read(timeout=1000)
    event1, values1 = window1.read()

    # If the "Open Window B" button is clicked, close the first window and open the second window
    if event1 == '-window_next-':
        # window1.close()       # KEEP window1 open, so that the input can be compared with output

        # use a while loop to keep trying the function call until no RuntimeWarning is raised.
        while True:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                try:
                    # parameter preset before start of simulations
                    na_days_pm = 1
                    na_days_cm = 65
                    simulation_end_days = 100 * 219
                    simulation_step_days = 100
                    simulation_step_len = simulation_end_days / simulation_step_days
                    # parameter preset before start of simulations
                    inv_num_range = range(1, 11)
                    inv_num_range_show = range(1, 3)
                    day = 0

                    plot_data = {}
                    day_it = {}
                    for inv_num in inv_num_range:
                        day_it[f'i{inv_num}'] = 0
                        plot_data[f'i{inv_num}'] = []

                    # specific for almost global variables
                    maint_day = {}
                    maint_type = {}
                    maint_na_days = {}
                    maint_cost = {}
                    ft_sample = {}
                    for inv_num in inv_num_range:
                        maint_day[f'i{inv_num}'] = []
                        maint_type[f'i{inv_num}'] = []
                        maint_na_days[f'i{inv_num}'] = 0
                        maint_cost[f'i{inv_num}'] = 0
                        ft_sample[f'i{inv_num}'] = 2100

                    # parameter preset before start of simulation in window2
                    # EUR_population = values1['-drift_inv1-']
                    input_eur = EUR_population
                    input_scale = scale_population
                    input_c_p = values1['-pmc_inv1-']
                    input_c_f = values1['-cmc_inv1-']

                    '''
                    # test code
                    input_c_p = 1500
                    input_c_f = 6000
                    '''

                    break  # Exit the loop if no warning is raised

                except RuntimeWarning as e:
                    logger.info(f'Caught a RuntimeWarning: {e}, re-start the simulation. ')
                    continue  # Continue to the next iteration if warning is raised

        # Initialize looping control variables
        looping = False


        # Define the layout for the second window
        layout2 = [
            [sg.Push(), sg.Text('Fleet Management Tool for Solar Inverters - Output ', font=('Helvetica', 18), justification='c', expand_x=True), sg.Push()],
            [sg.HSep()],
            [sg.Canvas(key="-inv_status-")],
            [sg.HSep()],
            # [sg.Push(), sg.Text('Inverter 1', font=("Helvetica", inv_title_size, "bold")), sg.Push()],
            [sg.Col([[sg.Canvas(key="-inv1_fig1-")]], p=0), sg.VSep(),
             sg.Col([[sg.Canvas(key="-inv1_fig2-")]], p=0), sg.VSep(),
             sg.Col([[sg.Image(size=(600, 400), key='-inv_map_dynamic-')]], p=0)],
            [sg.HSep()],
            # [sg.Push(), sg.Text('Inverter 2', font=("Helvetica", inv_title_size, "bold")), sg.Push()],
            [sg.Col([[sg.Canvas(key="-inv2_fig1-")]], p=0), sg.VSep(),
             sg.Col([[sg.Canvas(key="-inv2_fig2-")]], p=0), sg.VSep(),
             sg.Col([[sg.Canvas(key="-inv_log-")]], p=0)],
            [sg.HSep()],
            # [sg.Push(), sg.Text('Inverter 3', font=("Helvetica", inv_title_size, "bold")), sg.Push()],
            # [sg.Col([[sg.Text('Inverter 3', font=("Helvetica", inv_title_size, "bold"))]], p=0), sg.VSep(),
            #  sg.Col([[sg.Image(filename=I3_fig1[0], size=image_size, key="-inv3_fig1-")]], p=0), sg.VSep(),
            #  sg.Col([[sg.Image(filename=I3_fig2[0], size=image_size, key="-inv3_fig2-")]], p=0), sg.VSep(),
            #  sg.Col([[sg.Image(filename=I3_fig3[0], size=image_size, key="-inv3_fig3-")]], p=0)],
            # [sg.HSep()],

            [sg.Push(), sg.Button("Start/Stop", size = (30,2), key="-STARTSTOP-"), sg.Push()],

            # [sg.Sizer(1, 40)],
            [sg.HSep()],
            [sg.Text(
                'This tool is based upon work supported by the U.S. Department of Energy Office of Energy Efficiency and Renewable Energy (EERE) under the Solar Energy Technologies Office Award Number 39640.',
                font=('Helvetica', 10), justification='r', expand_x=True)],
        ]

        window2 = sg.Window('Fleet Management Tool for Solar Inverters - Output', layout2, resizable=True, finalize=True)

        # Initialize the canvas and figure
        canvas_fig_ax_dict = {}
        for inv_num in inv_num_range_show:
            for canvas_num in range (1,3):
                canvas_fig_ax_dict [f'canvas_i{inv_num}_f{canvas_num}'] = window2[f'-inv{inv_num}_fig{canvas_num}-'].TKCanvas
                canvas_fig_ax_dict [f'fig_i{inv_num}_f{canvas_num}'] , canvas_fig_ax_dict [f'ax_i{inv_num}_f{canvas_num}'] = plt.subplots(figsize=figsize)
                canvas_fig_ax_dict [f'plot_canvas_i{inv_num}_f{canvas_num}'] = FigureCanvasTkAgg(canvas_fig_ax_dict[f'fig_i{inv_num}_f{canvas_num}'], master=canvas_fig_ax_dict[f'canvas_i{inv_num}_f{canvas_num}'])
                canvas_fig_ax_dict [f'plot_canvas_i{inv_num}_f{canvas_num}'].draw()
                canvas_fig_ax_dict [f'plot_canvas_i{inv_num}_f{canvas_num}'].get_tk_widget().pack(side="top", fill="both", expand=True)

        canvas_fig_ax_dict['canvas_inv_status'] = window2['-inv_status-'].TKCanvas
        canvas_fig_ax_dict['fig_inv_status'], canvas_fig_ax_dict['ax_inv_status'] = plt.subplots(figsize=(18, 2))
        canvas_fig_ax_dict['plot_canvas_inv_status'] = FigureCanvasTkAgg(canvas_fig_ax_dict['fig_inv_status'],
                                                                          master=canvas_fig_ax_dict['canvas_inv_status'])
        canvas_fig_ax_dict['plot_canvas_inv_status'].draw()
        canvas_fig_ax_dict['plot_canvas_inv_status'].get_tk_widget().pack(side="top", fill="both", expand=True)

        canvas_fig_ax_dict['canvas_inv_log'] = window2['-inv_log-'].TKCanvas
        canvas_fig_ax_dict['fig_inv_log'], canvas_fig_ax_dict['ax_inv_log'] = plt.subplots(figsize=(6, 4))
        canvas_fig_ax_dict['plot_canvas_inv_log'] = FigureCanvasTkAgg(canvas_fig_ax_dict['fig_inv_log'],
                                                                      master=canvas_fig_ax_dict['canvas_inv_log'])
        canvas_fig_ax_dict['plot_canvas_inv_log'].draw()
        canvas_fig_ax_dict['plot_canvas_inv_log'].get_tk_widget().pack(side="top", fill="both", expand=True)

        while True:
            event2, values2 = window2.read(timeout=0)
            # event2, values2 = window2.read()

            # If the second window is closed, exit the program
            if event2 == sg.WINDOW_CLOSED:
                window1.close()
                window2.close()
                break


            if event2 == "-STARTSTOP-":
                if not looping:
                    window2['-STARTSTOP-'].update('Stop')
                    looping = True
                else:
                    window2['-STARTSTOP-'].update('Start')
                    looping = False

            if looping:
                try:  # Update the image to the next one in the list
                    # logger.info(f'started day {day}')
                    for inv_num in inv_num_range:
                        '''
                        # test code
                        inv_num = 1
                        '''

                        # give a bit randomized underlying failure time distribution, stil limited to average population
                        input_scale = random.randrange(2529, 2667)
                        '''
                        EUR_record = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.0148]
                        scale_record = [2667.491938616467, 2523.0164743152513, 2378.541010014036, 2234.0655457128205, 2089.590081411605, 1945.1146171103892, 1800.6391528091735, 1656.163688507958, 1511.6882242067425, 1367.212759905527, 2598.1437157518835]
                        '''

                        plot_data [f'i{inv_num}'], [maint_day, maint_type, maint_na_days, maint_cost, ft_sample, day_it] = inv_simulation(
                            inv_num, input_scale, input_c_p, input_c_f, na_days_pm, na_days_cm,
                            simulation_end_days, simulation_step_days, day, day_it, maint_day, maint_type,
                            maint_na_days, maint_cost, ft_sample)

                        # get updated RUL and maint for status_table_df
                        status_table_df.loc[status_table_df['INV_ID'] == inv_num, 'RUL'] = plot_data [f'i{inv_num}'] [2]
                        status_table_df.loc[status_table_df['INV_ID'] == inv_num, 'Maint.'] = plot_data[f'i{inv_num}'][5] - 301
                        if plot_data [f'i{inv_num}'] [2] <= 400:
                            status_table_df.loc[status_table_df['INV_ID'] == inv_num, 'Status'] = 'tab:orange'
                        elif plot_data [f'i{inv_num}'] [2] <= 1000:
                            status_table_df.loc[status_table_df['INV_ID'] == inv_num, 'Status'] = 'yellow'
                        else:
                            status_table_df.loc[status_table_df['INV_ID'] == inv_num, 'Status'] = 'green'
                            
                        # logger.info(f'completed day {day} - inv {inv_num} - simulation')

                        # almost global variables
                        # maint_day[f'i{inv_num}'] = plot_data [f'i{inv_num}'][10][f'i{inv_num}']
                        # maint_type[f'i{inv_num}'] = plot_data [f'i{inv_num}'][11][f'i{inv_num}']
                        # maint_na_days[f'i{inv_num}'] = plot_data [f'i{inv_num}'][12][f'i{inv_num}']
                        # maint_cost[f'i{inv_num}'] = plot_data [f'i{inv_num}'][13][f'i{inv_num}']
                        # ft_sample[f'i{inv_num}'] = plot_data [f'i{inv_num}'][14][f'i{inv_num}']



                    # combine table for window-skip drawing
                    plot_data_table_combine = plot_data['i1']
                    plot_data_table_combine_nadays = float(0)
                    plot_data_table_combine_maintcost = float(0)

                    for inv_num in inv_num_range:
                        plot_data_table_combine[9][0][1] += plot_data[f'i{inv_num}'][9][0][1]  # number of PM
                        plot_data_table_combine[9][1][1] += plot_data[f'i{inv_num}'][9][1][1]  # number of CM

                        temp = plot_data[f'i{inv_num}'][9][2][1][:-3]
                        temp = float(temp)
                        plot_data_table_combine_nadays += temp  # N/a Days

                        temp = plot_data[f'i{inv_num}'][9][3][1][1:-6]
                        temp = float(temp)
                        plot_data_table_combine_maintcost += temp  # Maint. Cost

                    plot_data_table_combine_nadays = plot_data_table_combine_nadays / len(
                        inv_num_range)  # get average
                    plot_data_table_combine_maintcost = plot_data_table_combine_maintcost / len(inv_num_range)

                    plot_data_table_combine[9][2][1] = f'{round(plot_data_table_combine_nadays, 2)}/yr'
                    plot_data_table_combine[9][3][1] = f'${round(plot_data_table_combine_maintcost, 2)}/kW-yr'
                    ## plot the maintenance history
                    draw_plot_skip(inv_num, canvas_fig_ax_dict, day, day_it, plot_data_table_combine, maint_na_days,
                                   maint_cost, EUR_population)

                    status_table_df_sort = status_table_df.sort_values(['RUL'], ascending=True, inplace=False,
                                                                       ignore_index=True)
                    ## plot the inverter status
                    draw_plot_status(canvas_fig_ax_dict, day, status_table_df_sort)
                    '''
                    # test code - to check fig in agg mode
                    canvas_fig_ax_dict['fig_inv_status'].savefig('test.png')
                    '''

                    inv_num_show_1 = status_table_df_sort['INV_ID'].iloc[0]
                    colorstyle_1 = status_table_df_sort['Status'].iloc[0]
                    fig_location_num = 'i1'
                    ## plot the f1 and f2 of show_inv_number_1
                    draw_plot_f1(inv_num_show_1, canvas_fig_ax_dict, day, day_it, plot_data, colorstyle_1, fig_location_num)
                    draw_plot_f2(inv_num_show_1, canvas_fig_ax_dict, day, day_it, plot_data, colorstyle_1, fig_location_num)


                    inv_num_show_2 = status_table_df_sort['INV_ID'].iloc[1]
                    colorstyle_2 = status_table_df_sort['Status'].iloc[1]
                    fig_location_num = 'i2'
                    ## plot the f1 and f2 of show_inv_number_2
                    draw_plot_f1(inv_num_show_2, canvas_fig_ax_dict, day, day_it, plot_data, colorstyle_2, fig_location_num)
                    draw_plot_f2(inv_num_show_2, canvas_fig_ax_dict, day, day_it, plot_data,colorstyle_2, fig_location_num)


                    site_plot = sites.copy()
                    site_plot = site_plot.set_index('ID')
                    site_plot = site_plot.reindex(index=status_table_df_sort['INV_ID'])
                    site_plot = site_plot.reset_index()

                    filepath_dynamic_map = os.path.join(figure_path_inv_map, 'inverter_map_dynamic.png')
                    ## plot the inverter map
                    draw_plot_map(site_plot, status_table_df_sort, filepath_dynamic_map)
                    window2['-inv_map_dynamic-'].update(filepath_dynamic_map)

                    if day == simulation_end_days:
                        looping = False
                        window2['-STARTSTOP-'].update('Start')

                        # specific for almost global variables
                        maint_day = {}
                        maint_type = {}
                        maint_na_days = {}
                        maint_cost = {}
                        ft_sample = {}
                        for inv_num in inv_num_range:
                            maint_day[f'i{inv_num}'] = []
                            maint_type[f'i{inv_num}'] = []
                            maint_na_days[f'i{inv_num}'] = 0
                            maint_cost[f'i{inv_num}'] = 0
                            ft_sample[f'i{inv_num}'] = 2100

                        day = 0

                        # import time
                        # timestr = time.strftime("%Y%m%d-%H%M%S")


                        # for inv_num in inv_num_range:
                        #     day_it[f'i{inv_num}'] = 0
                        #
                        #     canvas_fig_ax_dict[f'fig_i{inv_num}_f3'].savefig(
                        #         f'./figure_results_save/VIS_eur_{EUR_population}_time_' + timestr + f'_inv_{inv_num}.png')





                    else:
                        day = day + simulation_step_days
                        for inv_num in inv_num_range:
                            day_it[f'i{inv_num}'] = day_it[f'i{inv_num}'] + simulation_step_days
                        # day_it[f'i{inv_num}'] = (day_it[f'i{inv_num}'] + 1) % simulation_step_len  # Wrap around to the start if we've reached the end


                except Exception as Argument:
                    logging.exception("Error in window 2 operation")

                    sg.popup_error('Something is not Correct, Exiting...')
                    window2['-STARTSTOP-'].update('Start')
                    looping = False

            # time.sleep(0.1)  # Wait for a short period to avoid using too much CPU time

    if event1 == '-window_skip-':
        # window1.close()       # KEEP window1 open, so that the input can be compared with output

        # use a while loop to keep trying the function call until no RuntimeWarning is raised.
        while True:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                try:
                    # parameter preset before start of simulations
                    na_days_pm = 1
                    na_days_cm = 65
                    simulation_end_days = 100 * 219
                    simulation_step_days = 100
                    simulation_step_len = simulation_end_days / simulation_step_days
                    # parameter preset before start of simulations
                    inv_num_range = range(1, 11)
                    inv_num_range_show = range(1, 3)
                    day = 0

                    plot_data = {}
                    day_it = {}
                    for inv_num in inv_num_range:
                        day_it[f'i{inv_num}'] = 0
                        plot_data[f'i{inv_num}'] = []

                    # specific for almost global variables
                    maint_day = {}
                    maint_type = {}
                    maint_na_days = {}
                    maint_cost = {}
                    ft_sample = {}
                    for inv_num in inv_num_range:
                        maint_day[f'i{inv_num}'] = []
                        maint_type[f'i{inv_num}'] = []
                        maint_na_days[f'i{inv_num}'] = 0
                        maint_cost[f'i{inv_num}'] = 0
                        ft_sample[f'i{inv_num}'] = 2100

                    # parameter preset before start of simulation in window2
                    # EUR_population = values1['-drift_inv1-']
                    input_eur = EUR_population
                    input_scale = scale_population
                    input_c_p = values1['-pmc_inv1-']
                    input_c_f = values1['-cmc_inv1-']

                    '''
                    # test code
                    input_c_p = 1500
                    input_c_f = 6000
                    '''

                    for day in tqdm(range (0, simulation_end_days+simulation_step_days, simulation_step_days)):
                        for inv_num in inv_num_range:
                            '''
                            # test code
                            inv_num = 1
                            '''

                            plot_data[f'i{inv_num}'], [maint_day, maint_type, maint_na_days, maint_cost, ft_sample,
                                                       day_it] = inv_simulation(inv_num, input_scale, input_c_p,
                                                                                input_c_f, na_days_pm, na_days_cm,
                                                                                simulation_end_days,
                                                                                simulation_step_days, day, day_it,
                                                                                maint_day, maint_type, maint_na_days,
                                                                                maint_cost, ft_sample)

                        for inv_num in inv_num_range:
                            day_it[f'i{inv_num}'] = day_it[f'i{inv_num}'] + simulation_step_days

                    # combine table for window-skip draing
                    plot_data_table_combine = plot_data['i1']
                    plot_data_table_combine_nadays = float(0)
                    plot_data_table_combine_maintcost = float(0)

                    for inv_num in inv_num_range:
                        plot_data_table_combine[9][0][1] += plot_data[f'i{inv_num}'][9][0][1]  # number of PM
                        plot_data_table_combine[9][1][1] += plot_data[f'i{inv_num}'][9][1][1]  # number of CM

                        temp = plot_data[f'i{inv_num}'][9][2][1][:-3]
                        temp = float(temp)
                        plot_data_table_combine_nadays += temp  # N/a Days

                        temp = plot_data[f'i{inv_num}'][9][3][1][1:-6]
                        temp = float(temp)
                        plot_data_table_combine_maintcost += temp  # Maint. Cost

                    plot_data_table_combine_nadays = plot_data_table_combine_nadays / len(inv_num_range)  # get average
                    plot_data_table_combine_maintcost = plot_data_table_combine_maintcost / len(inv_num_range)

                    plot_data_table_combine[9][2][1] = f'{round(plot_data_table_combine_nadays, 2)}/yr'
                    plot_data_table_combine[9][3][1] = f'${round(plot_data_table_combine_maintcost, 2)}/kW-yr'

                    break  # Exit the loop if no warning is raised

                except RuntimeWarning as e:
                    logger.info(f'Caught a RuntimeWarning: {e}, re-start the simulation. ')
                    continue  # Continue to the next iteration if warning is raised

        # Initialize looping control variables
        looping = False


        # Define the layout for the second window
        layout3 = [
            [sg.Push(), sg.Text('Fleet Management Tool for Solar Inverters - Output', font=('Helvetica', 18), justification='c', expand_x=True), sg.Push()],
            [sg.HSep()],
            [sg.Push(), sg.Canvas(key="-inv_log-"), sg.Push()],
            [sg.HSep()],
            [sg.Push(), sg.Image(size=(600, 400), key='-inv_map_static-'), sg.Push()],

            # [sg.Sizer(1, 40)],
            [sg.HSep()],
            [sg.Text(
                'This tool is based upon work supported by the U.S. Department of Energy Office of Energy Efficiency and Renewable Energy (EERE) under the Solar Energy Technologies Office Award Number 39640.',
                font=('Helvetica', 10), justification='r', expand_x=True)],
        ]

        window3 = sg.Window('Fleet Management Tool for Solar Inverters - Output', layout3, resizable=True, finalize=True)

        # Initialize the canvas and figure
        canvas_fig_ax_dict = {}
        canvas_fig_ax_dict ['canvas_inv_log'] = window3['-inv_log-'].TKCanvas
        canvas_fig_ax_dict['fig_inv_log'], canvas_fig_ax_dict['ax_inv_log'] = plt.subplots(figsize=(6,4))
        canvas_fig_ax_dict ['plot_canvas_inv_log'] = FigureCanvasTkAgg(canvas_fig_ax_dict['fig_inv_log'], master=canvas_fig_ax_dict['canvas_inv_log'])
        canvas_fig_ax_dict ['plot_canvas_inv_log'].draw()
        canvas_fig_ax_dict ['plot_canvas_inv_log'].get_tk_widget().pack(side="top", fill="both", expand=True)


        while True:
            event3, values3 = window3.read(timeout=50)
            # event2, values2 = window2.read()

            # If the second window is closed, exit the program
            if event3 == sg.WINDOW_CLOSED:
                import time
                timestr = time.strftime("%Y%m%d-%H%M%S")
                for inv_num in inv_num_range:
                    canvas_fig_ax_dict['fig_inv_log'].savefig(
                        f'./figure_results_save/skip_time_' + timestr + '.png')

                window1.close()
                window3.close()
                break

            try:


                draw_plot_skip(inv_num, canvas_fig_ax_dict, day, day_it, plot_data_table_combine, maint_na_days, maint_cost, EUR_population)

                window3['-inv_map_static-'].update(os.path.join(figure_path_inv_map, 'inverter_map_static.png'))

            except Exception as Argument:
                logging.exception("Error in window 3 operation")

                sg.popup_error('Something is not Correct, Exiting...')


    # If the first window is closed, exit the program
    if event1 == sg.WINDOW_CLOSED:
        break

# Close all windows when the program exits
window1.close()




