# -*- coding: utf-8 -*-
"""
Created on Wed Jan 27 08:53:24 2016

@author: Mike Van Maele, Justin Kerr

Model now object oriented to allow for interaction between disease states. Only
a single high-worm burden state of schistosomiasis has been implemented. Malaria
reinfections simply supercede existing infections (no super-infection)
"""

"Libraries"
import time
import random
import csv
import datetime
import dateutil.relativedelta as date
import json
import sys
start = time.time()

"Initialize variables and constants"
#Load from JS GUI
for line in sys.stdin:
    UI_INPUTS = json.loads(line)
    
#Show plots or not
SHOW_PLOTS = True
if (SHOW_PLOTS):
    import matplotlib.pyplot as plt

#With or without integration (defined as "smartly" setting the timing of
#interventions as per recommendations in the literature)
USE_INTEGRATION = bool(int(UI_INPUTS["use_integration"]))

#Initialize user-specified inputs (pulled from GUI)
F_AGE_UNDER_5 = float(UI_INPUTS["pop1"])     #% distribution of population under 5 years old
F_AGE_5_TO_15 = float(UI_INPUTS["pop2"])       #% distribution of population between 5 and 15 years old
F_AGE_16_PLUS = float(UI_INPUTS["pop3"])    #% distribution of population 16 years old or older

F_PZQ_TARGET_COV = float(UI_INPUTS["schisto_coverage"])    #Target % coverage of praziquantel (PZQ) mass drug 
                        #administration
PZQ_AGE_RANGE = tuple(UI_INPUTS["schisto_age_range"] )#Age groups that get PZQ (by default, only 5-15 y/o 
                    #children will get it because they are school-age and PZQ
                    #interventions may be targeting school-age children)

T_PZQ = 30          #Number of days at which PZQ is distributed. Required
                    #user input if "constant" malaria transmission pattern selected
PZQ_MONTH_NUM = int(UI_INPUTS["schisto_month_num"]) #Month PZQ is distributed in the "constant" case (without integration). Indexed
                                #from 1 (i.e., January = 1)

MALARIA_TRANS_PATTERN = UI_INPUTS["malaria_timing"]  #Malaria transmission pattern. Either
                                    #"Seasonal" (automatically implements integration) or "Constant" (uses user-input intervention timing)
PEAK_TRANS_MONTHS_TMP = tuple(UI_INPUTS["malaria_peak_month_num"])
PEAK_TRANS_MONTHS = [ int(x) for x in PEAK_TRANS_MONTHS_TMP ]     #Peak malaria transmission month(s). Indexed
                                #from 1 (i.e., January = 1)
N_BASELINE_INF_BITES = UI_INPUTS["malaria_rate"]  #Baseline infectious mosquito bites per year for
                            #the transmission of malaria. Can be low (20),
                            #medium (100), or high (250).
IRS_CHECKED = bool(int(UI_INPUTS["irs"]))  #Can indoor residual insecticide spraying be used?
                    #True or false.
F_IRS_TARGET_COV = float(UI_INPUTS["irs_coverage"]) #Target % coverage of indoor spraying.
T_SPRAY = 150       #Number of days at which sprays are distributed. Required
                    #user input if "constant" malaria transmission pattern selected
IRS_MONTH_NUM = int(UI_INPUTS["irs_month_num"]) #Month IRS are distributed in the "constant" case (without integration). Indexed
                                #from 1 (i.e., January = 1)
    
ITN_CHECKED = bool(int(UI_INPUTS["itn"]))  #Can insecticide-treated bed nets be used? True or false.
F_ITN_TARGET_COV = float(UI_INPUTS["itn_coverage"]) #Target % coverage of indoor spraying.
T_NET = 150         #Number of days at which nets are distributed. Required
                    #user input if "constant" malaria transmission pattern selected
ITN_MONTH_NUM = int(UI_INPUTS["itn_month_num"]) #Month nets are distributed in the "constant" case (without integration). Indexed
                                #from 1 (i.e., January = 1)

IRS_ITN_DIST_STRAT = UI_INPUTS["irs_itn_distribution"]  #Not currently used. The IRS/ITN countermeasure
                                #distribution strategy.

#Initialize non-user-specified, constant inputs
CUR_YEAR = 2016
N_PEOPLE = 1000    #Number of people to simulate
N_DAYS_BURN = 60    #Number of days to burn in the model to steady-state values
                    #To do: let it burn until values don't fluctuate
#N_PEOPLE = 10000    #Number of people to simulate
N_DAYS = N_DAYS_BURN + 365 + 10      #Simulation runtime in days
#N_DAYS = 425      #Simulation runtime in days
                    #To do: force this value to be fixed
if not ITN_CHECKED:
    T_NET = N_DAYS
else:
    T_NET = N_DAYS    #Number of days after simulation start to distribute nets
                    #Determine based on season start (30 days prior)
    
if not IRS_CHECKED:    
    T_SPRAY = N_DAYS
else:
    T_SPRAY = N_DAYS  #Number of days after simulation start to distribute spray
                    #Determine based on season start (30 days prior)
    
if len(PZQ_AGE_RANGE) == 0:
    T_PZQ = N_DAYS
else:
    T_PZQ = N_DAYS     #Number of days after simulation start to distribute PZQ
                    #Determine based on season start (4 months prior)   
    
D_PROTECT = 20      #Number of days malaria treatment protects against re-
                    #infection (default is 20)
START_MONTH = None  #Month of year to start simulation, indexed from 1 (i.e.,
                    #January = 1). By default, 4 months before season start
START_DAY = 0       #Day of month to start simulation, 0 by default
F_ASYMP = 0.28      #The fraction of people infected with malaria who are
                    #asymptomatic (do not get treatment) (Mbah et al, 2014)
F_TREATED = 0.8     #TO DO: Ask Justin how to set this value
                    #The fraction of people with symptomatic malaria who get
                    #treatment
F_SYMP_TREATED = (1 - F_ASYMP)*F_TREATED #The fraction of people who get 
                                        #malaria, are symptomatic, and get treatment
F_SYMP_UNTREATED = (1 - F_ASYMP)*(1 - F_TREATED) #The fraction of people who get malaria,
                                                #are symptomatic, and don't get treatment
BREAKPOINT_1 = F_SYMP_TREATED #Used when randomly binning malaria infectives
BREAKPOINT_2 = F_SYMP_TREATED + F_SYMP_UNTREATED

D_MALARIA = 5 #Malaria infection lasts about 5 days (Mbah et al, 2014)
D_ASYMP_MALARIA = 360
INIT_P_MALARIA_BASELINE = float(N_BASELINE_INF_BITES) / 365.0 #Baseline daily prob. of getting malaria.
F_SCHISTO_COINFECTION_MOD = 1.85 #Source: (Mbah et al, 2014)
P_MALARIA_SEASONAL_MOD = 5  #Factor by which the daily prob. of getting malaria
                            #increases during malaria season (Kelly-Hope and McKenzie 2009; based on difference between places with 7 or more months of rain vs. 6 or fewer)

#TO DO: Justin figuring out these values
P_SCHISTO = 0.1 #Daily prob. of getting schistosomiasis, Justin working on it
NET_EFFICACY = 0.9 #(p. 9 of Shukat et al 2010)
SPRAY_EFFICACY = 0.9 #(p. 9 of Shukat et al 2010)

#Miscellaneous global constants
ONE_YEAR =  date.relativedelta(years=1)
ONE_MONTH = date.relativedelta(months=1)
ONE_DAY =  date.relativedelta(days=1)   

class Person( object ):
    """ Class that holds all the people.  Representation of the compartmental 
    model are stored as attibutes"""
    
    #Total number of people in memory
    count = 0
    
    #Totals by age bin (0-4, 5-15, and 16+)
    age_bin_counts = {'0-4':0, '5-15':0, '16+':0}
    
    def __init__( self ):
        Person.count += 1        
        self.id = Person.count - 1
        
        # Malaria parameters #------------------------------------------------#
        self.has_malaria = False #do they have malaria?
        self.is_symptomatic = False #if they have malaria, is it symptomatic?
        self.days_to_asymp_malaria = -1 #days until asymptomatic malaria start
        self.asymp_malaria_days_left = -1 #days left of asymptomatic malaria
        self.symp_malaria_days_left = -1 #days left of symptomatic malaria
        self.protection_days_left = -1 #days left of malaria protection
        
        # Schisto parameters #------------------------------------------------#
        self.has_schisto = False #do they have schistosomiasis?
        self.has_PZQ = False #were they given PZQ at T_PZQ?

        # Intervention parameters #-------------------------------------------#
        self.has_net = False #do they have protection from bed nets?
        self.has_spray = False #do they have protection from sprays?

        # Age parameters #----------------------------------------------------#
        #Determine age bin for this person:
        age_bin_runif = random.random()
        breakpoint_under_5 = F_AGE_UNDER_5
        breakpoint_5_to_15 = F_AGE_UNDER_5 + F_AGE_5_TO_15
        if age_bin_runif < breakpoint_under_5:
            self.age_bin = "0-4"
            Person.age_bin_counts["0-4"] += 1
        elif age_bin_runif >= breakpoint_under_5 and age_bin_runif < breakpoint_5_to_15:
            self.age_bin = "5-15"
            Person.age_bin_counts["5-15"] += 1
        else:
            self.age_bin = "16+"
            Person.age_bin_counts["16+"] += 1
            
class People( list ):
    """Class defining the list that holds people in the simulation."""
        
    def update_interventions_and_infections( self, app):
        """Once per time step, check whether each person gets malaria and/or
        schisto. Also, check whether a person's malaria timer has ended; if so,
        flag them as no longer having malaria."""
        t = app.cur_time_step
        cur_p_malaria_baseline = app.cur_p_malaria_baseline
        runif = random.random
        for n in range(0, Person.count):
            cur_person = self[n];
            
            # Timers #--------------------------------------------------------#
            #Reduce the number of days of protection left from ACT by 1. Do the 
            #same thing for the number of days of malaria sickness
            cur_person.protection_days_left -= 1;
            cur_person.symp_malaria_days_left -= 1;            
            cur_person.asymp_malaria_days_left -= 1;            
            cur_person.days_to_asymp_malaria -= 1;            
            
            # Interventions #-------------------------------------------------#
            if t == app.t_net and ITN_CHECKED:
                #Randomly choose people to get nets and adjust malaria probability
                get_net_runif = runif()
                if get_net_runif < F_ITN_TARGET_COV:
                    cur_person.has_net = True
            if t == app.t_spray and IRS_CHECKED:
                #Randomly choose people to get spray and adjust malaria probability
                get_spray_runif = runif()
                if get_spray_runif < F_IRS_TARGET_COV:
                    cur_person.has_spray = True
            if t == app.t_pzq:
                #Randomly choose people to get PZQ and adjust schisto probability
                #Note: It is assumed anyone who gets PZQ continues to take it
                #every six months (not explicitly modeled)
                cur_person_in_pzq_age_range = cur_person.age_bin in PZQ_AGE_RANGE
                if cur_person_in_pzq_age_range:
                    get_PZQ_runif = runif()
                    if get_PZQ_runif < F_PZQ_TARGET_COV:
                        cur_person.has_PZQ = True
                        cur_person.has_schisto = False
            
            # Malaria infection #---------------------------------------------#
            #Symptomatic malaria timer: days left of symptomatic malaria. When
                #this time ends, turn off symptomatic flag. If the person does
                #not have an asymptomatic malaria timer set, then turn off the
                #"has_malaria" flag also.
            #Note: Symptomatic malaria always lasts 5 days, and asymptomatic
                #malaria always lasts 360 days
            asymp_malaria_starts_today = cur_person.days_to_asymp_malaria == 0
            asymp_malaria_ends_today = cur_person.asymp_malaria_days_left == 0
            symp_malaria_ends_today = cur_person.symp_malaria_days_left == 0    
            
            #UNTREATED SYMPTOMATIC: Transitioning from symp to asymp malaria
            #If person is switching from symptomatic to asymptomatic malaria
            #today, update flags accordingly
            if asymp_malaria_starts_today:
                #Set their symptomatic flag to false
                cur_person.is_symptomatic = False
                #Ensure their has malaria flag is still true
                cur_person.has_malaria = True
                #Set days of asymptomatic malaria remaining
                cur_person.asymp_malaria_days_left = D_ASYMP_MALARIA                
            
            #TREATED SYMPTOMATIC: Transition from symp malaria to no malaria
            #Else, if person's symptomatic malaria ends today and they had protection
            #which means they won't transition to asymptomatic malaria
            elif symp_malaria_ends_today and cur_person.days_to_asymp_malaria < 0:
                #Set has malaria flag to false
                cur_person.has_malaria = False
                #Set their symptomatic flag to false
                cur_person.is_symptomatic = False
            
            #UNTREATED SYMPTOMATIC and UNTREATED ASYMPTOMATIC: Transition from
            #asymp malaria to no malaria
            #Else, if person's asymptomatic malaria ends today, update flags
            #accordingly
            elif asymp_malaria_ends_today:
                #Set has malaria flag to false
                cur_person.has_malaria = False
                #Set their symptomatic flag to false
                cur_person.is_symptomatic = False
            
            #If the person is currently protected from malaria by having
            #received ACT, skip them. Otherwise, continue.            
            is_protected = cur_person.protection_days_left > 0
            if not is_protected:
                #Check the person's intervention and schisto flags and modify
                #their P_MALARIA value accordingly
                cur_p_malaria = cur_p_malaria_baseline
                if cur_person.has_schisto:
                    cur_p_malaria *= F_SCHISTO_COINFECTION_MOD
                if cur_person.has_net:
                    cur_p_malaria *= (1 - NET_EFFICACY)
                if cur_person.has_spray:
                    cur_p_malaria *= (1 - SPRAY_EFFICACY)
                if cur_p_malaria > 1:
                    cur_p_malaria = 1
                    
                #Randomly test whether the person gets malaria this day     
                get_malaria_runif = runif()
                if get_malaria_runif < cur_p_malaria:
                    #If the current person already has asymptomatic malaria,
                    #or if they don't have malaria yet:
                    has_asymp_malaria = cur_person.has_malaria and not cur_person.is_symptomatic
                    if has_asymp_malaria or not cur_person.has_malaria:                    
                        #Set the person's malaria flag to true
                        cur_person.has_malaria = True
                        
                        #If the person got malaria, determine which category
                        #they will be: symptomatic or asymptomatic, and treated or
                        #untreated
                        symp_treat_runif = runif()
                        
                        #Bin into one of three categories below:
                        #SYMPTOMATIC, TREATED
                        if symp_treat_runif < BREAKPOINT_1:
                            #Set symp malaria values:                            
                            cur_person.is_symptomatic = True
                            cur_person.symp_malaria_days_left = D_MALARIA
                            cur_person.protection_days_left = D_PROTECT
                            
                            #Don't get asymp malaria:
                            cur_person.days_to_asymp_malaria = -1
                            cur_person.asymp_malaria_days_left = -1
                            
                        #SYMPTOMATIC, UNTREATED
                        elif symp_treat_runif >= BREAKPOINT_1 and symp_treat_runif < BREAKPOINT_2:
                            #Set symp malaria values:                            
                            cur_person.is_symptomatic = True
                            cur_person.symp_malaria_days_left = D_MALARIA
                            cur_person.protection_days_left = -1
                            
                            #Later, get asymp malaria:
                            cur_person.days_to_asymp_malaria = D_MALARIA
                            cur_person.asymp_malaria_days_left = -1
                        #ASYMPTOMATIC, UNTREATED
                        else: 
                            #Don't get symp malaria:                            
                            cur_person.is_symptomatic = False
                            cur_person.symp_malaria_days_left = -1
                            cur_person.protection_days_left = -1
                            
                            #Instantly get asymp malaria:
                            cur_person.days_to_asymp_malaria = -1
                            cur_person.asymp_malaria_days_left = D_ASYMP_MALARIA
                    #If the person already has untreated symptomatic malaria:
                    else:
                        #Keep them in the symptomatic, untreated bin and
                        #restart their malaria illness timer
                        #Set symp malaria values:                            
                        cur_person.is_symptomatic = True
                        cur_person.symp_malaria_days_left = D_MALARIA
                        cur_person.protection_days_left = -1
                        
                        #Later, get asymp malaria:
                        cur_person.days_to_asymp_malaria = D_MALARIA
                        cur_person.asymp_malaria_days_left = -1
                        
                        
            # Schisto infection #---------------------------------------------#
            if not cur_person.has_schisto and not cur_person.has_PZQ:
                get_schisto_runif = runif()
                if get_schisto_runif < P_SCHISTO:
                    cur_person.has_schisto = True
            
            # Prevalence values #---------------------------------------------#
            #Update the prevalence vs. time series
            if cur_person.has_schisto:
                cur_age_bin = cur_person.age_bin
                cur_n_people = Person.age_bin_counts[cur_age_bin]
                app.prevalence_schisto[cur_age_bin][t] += 1.0/cur_n_people
            if cur_person.has_malaria:
                cur_age_bin = cur_person.age_bin
                cur_n_people = Person.age_bin_counts[cur_age_bin]
                app.prevalence_malaria[cur_age_bin][t] += 1.0/cur_n_people
            if cur_person.has_schisto and cur_person.has_malaria:
                cur_age_bin = cur_person.age_bin
                cur_n_people = Person.age_bin_counts[cur_age_bin]
                app.prevalence_coinfection[cur_age_bin][t] += 1.0/cur_n_people
                    
class App( object ):
    """Class defining application parameters."""
    #Values
    cur_time_step = 0
    cur_p_malaria_baseline = INIT_P_MALARIA_BASELINE
    is_malaria_season = [False]*N_DAYS
    prevalence_schisto = \
    {'0-4': [0.0]*N_DAYS, '5-15': [0.0]*N_DAYS, '16+': [0.0]*N_DAYS}
    prevalence_malaria = \
    {'0-4': [0.0]*N_DAYS, '5-15': [0.0]*N_DAYS, '16+': [0.0]*N_DAYS}   
    prevalence_coinfection = \
    {'0-4': [0.0]*N_DAYS, '5-15': [0.0]*N_DAYS, '16+': [0.0]*N_DAYS}    
    
    #Functions
    def update_p_malaria_baseline(self):
        """Modifies the baseline daily probability of being infected with
        malaria based on (1) seasonality and (2) vector pressure (to-do)."""
        #If the current time step is malaria season and the previous one
        #was not, multiply the daily probability of getting malaria by the
        #seasonal modifier.
        cur_time_step = self.cur_time_step
        prev_time_step = cur_time_step - 1
        is_malaria_season = self.is_malaria_season
        #Note: the model assumes the time step before the FIRST time step
        #(i.e., time step -1) is NOT malaria season
        if prev_time_step == -1:
            self.cur_p_malaria_baseline = INIT_P_MALARIA_BASELINE
        elif is_malaria_season[cur_time_step] and not is_malaria_season[prev_time_step]:
            self.cur_p_malaria_baseline *= P_MALARIA_SEASONAL_MOD
        elif not is_malaria_season[cur_time_step] and is_malaria_season[prev_time_step]:
            self.cur_p_malaria_baseline /= P_MALARIA_SEASONAL_MOD
            
        #TO DO: Update p_malaria based on vector pressure. Justin and/or the
        #GWU team will figure out the best way to approach this.
            
    def write_prevalence( self ):
        #Writes prevalence values and graphs them for school-age children (5-15)
    
        #With or without integration?
        if USE_INTEGRATION:
            integration = ", with Integration"
            fn_int = "_with_integration"
        else:
            integration = ", without Integration"
            fn_int = "_without_integration"
                
        #Load number of people in each age bin
        n_people_0_4 = Person.age_bin_counts["0-4"]        
        n_people_5_15 = Person.age_bin_counts["5-15"]        
        n_people_16_plus = Person.age_bin_counts["16+"]        
        
        #Store the prevalence for each disease (y) vs. time (x)
        x = range(0, N_DAYS)
        y = {}
        y["schisto"] = {"0-4":[0]*N_DAYS,"5-15":[0]*N_DAYS,"16+":[0]*N_DAYS,"All":[0]*N_DAYS}
        y["malaria"] = {"0-4":[0]*N_DAYS,"5-15":[0]*N_DAYS,"16+":[0]*N_DAYS,"All":[0]*N_DAYS}
        y["coinfection"] = {"0-4":[0]*N_DAYS,"5-15":[0]*N_DAYS,"16+":[0]*N_DAYS,"All":[0]*N_DAYS}

        title_spaces = [""]*6
        spaces = [""]*2
        header_str = ["Time (d)","0-4 y/o","5-15 y/o","16+ y/o","All"]
        headers = header_str + spaces + header_str + spaces + header_str
        
        with open('output/output' + fn_int + '.csv', 'wb') as csvfile:
            writer = csv.writer(csvfile, quoting = csv.QUOTE_NONNUMERIC)
            title = ["Prevalence of schistosomiasis by age group vs. time (d)"] + title_spaces + ["Prevalence of malaria by age group vs. time (d)"] + title_spaces + ["Prevalence of coinfection by age group vs. time (d)"]
            writer.writerow(title)
            writer.writerow(headers)
            for t in range(0, N_DAYS):
                # Schisto output #----------------------------------------------------#
                y["schisto"]["0-4"][t] = self.prevalence_schisto["0-4"][t]
                y["schisto"]["5-15"][t] = self.prevalence_schisto["5-15"][t]
                y["schisto"]["16+"][t] = self.prevalence_schisto["16+"][t]
                schisto_prev_all = \
                    (y["schisto"]["0-4"][t] * n_people_0_4 + \
                    y["schisto"]["5-15"][t] * n_people_5_15 + \
                    y["schisto"]["16+"][t] * n_people_16_plus) / \
                    N_PEOPLE
                y["schisto"]["All"][t] = schisto_prev_all
                cur_output_schisto = [t,y["schisto"]["0-4"][t],y["schisto"]["5-15"][t],y["schisto"]["16+"][t],y["schisto"]["All"][t]]
 
                # Malaria output #----------------------------------------------------#
                y["malaria"]["0-4"][t] = self.prevalence_malaria["0-4"][t]
                y["malaria"]["5-15"][t] = self.prevalence_malaria["5-15"][t]
                y["malaria"]["16+"][t] = self.prevalence_malaria["16+"][t]
                malaria_prev_all = \
                    (y["malaria"]["0-4"][t] * n_people_0_4 + \
                    y["malaria"]["5-15"][t] * n_people_5_15 + \
                    y["malaria"]["16+"][t] * n_people_16_plus) / \
                    N_PEOPLE
                y["malaria"]["All"][t] = malaria_prev_all
                cur_output_malaria = [t,y["malaria"]["0-4"][t],y["malaria"]["5-15"][t],y["malaria"]["16+"][t],y["malaria"]["All"][t]]

                # Coinfection output #------------------------------------------------#
                y["coinfection"]["0-4"][t] = self.prevalence_coinfection["0-4"][t]
                y["coinfection"]["5-15"][t] = self.prevalence_coinfection["5-15"][t]
                y["coinfection"]["16+"][t] = self.prevalence_coinfection["16+"][t]
                coinfection_prev_all = \
                    (y["coinfection"]["0-4"][t] * n_people_0_4 + \
                    y["coinfection"]["5-15"][t] * n_people_5_15 + \
                    y["coinfection"]["16+"][t] * n_people_16_plus) / \
                    N_PEOPLE
                y["coinfection"]["All"][t] = coinfection_prev_all
                cur_output_coinfection = [t,y["coinfection"]["0-4"][t],y["coinfection"]["5-15"][t],y["coinfection"]["16+"][t],y["coinfection"]["All"][t]]

                writer.writerow(cur_output_schisto + spaces + cur_output_malaria + spaces + cur_output_coinfection)
            self.prevalence_schisto["All"] = y["schisto"]["All"]
            self.prevalence_malaria["All"] = y["malaria"]["All"]
            self.prevalence_coinfection["All"] = y["coinfection"]["All"]
        csvfile.close()
            
        # Plotting #----------------------------------------------------------#
        if (SHOW_PLOTS):
            #Plot options
            dpi = 100
            
            #Plot prevalence for all
            age_group_to_plot = "All"
            plt.plot(x,y["schisto"][age_group_to_plot],label="Schistosomiasis"); 
            plt.plot(x,y["malaria"][age_group_to_plot],label="Malaria"); 
            plt.plot(x,y["coinfection"][age_group_to_plot],label="Coinfection");
            plt.legend();
            plt.grid(True);
            plt.xlabel("Time (d)");
            plt.ylabel("Prevalence (fraction of population)")
            plt.ylim([0,1.1]);
            plt.title("Disease Prevalence vs. Time (d) for " + age_group_to_plot + integration);
            plt.savefig('output/output_graph_all_ages' + fn_int + '.png', format='png', dpi=dpi)
            plt.close()
    #        plt.show()
           
#            #Plot prevalence for 0-4
#            age_group_to_plot = "0-4"
#            plt.plot(x,y["schisto"][age_group_to_plot],label="Schistosomiasis"); 
#            plt.plot(x,y["malaria"][age_group_to_plot],label="Malaria"); 
#            plt.plot(x,y["coinfection"][age_group_to_plot],label="Coinfection");
#            plt.legend();
#            plt.grid(True);
#            plt.xlabel("Time (d)");
#            plt.ylabel("Prevalence (fraction of population)")
#            plt.ylim([0,1.1]);
#            plt.title("Disease Prevalence vs. Time (d) for " + age_group_to_plot);
#            plt.savefig('output/output_graph_0_4.png', format='png', dpi=dpi)
#    #        plt.show()
#            
#            #Plot prevalence for 5-15
#            age_group_to_plot = "5-15"
#            plt.plot(x,y["schisto"][age_group_to_plot],label="Schistosomiasis"); 
#            plt.plot(x,y["malaria"][age_group_to_plot],label="Malaria"); 
#            plt.plot(x,y["coinfection"][age_group_to_plot],label="Coinfection");
#            plt.legend();
#            plt.grid(True);
#            plt.xlabel("Time (d)");
#            plt.ylabel("Prevalence (fraction of population)")
#            plt.ylim([0,1.1]);
#            plt.title("Disease Prevalence vs. Time (d) for " + age_group_to_plot);
#            plt.savefig('output/output_graph_5_15.png', format='png', dpi=dpi)
#    #        plt.show()
#            
#            #Plot prevalence for 16+
#            age_group_to_plot = "16+"
#            plt.plot(x,y["schisto"][age_group_to_plot],label="Schistosomiasis"); 
#            plt.plot(x,y["malaria"][age_group_to_plot],label="Malaria"); 
#            plt.plot(x,y["coinfection"][age_group_to_plot],label="Coinfection");
#            plt.legend();
#            plt.grid(True);
#            plt.xlabel("Time (d)");
#            plt.ylabel("Prevalence (fraction of population)")
#            plt.ylim([0,1.1]);
#            plt.title("Disease Prevalence vs. Time (d) for " + age_group_to_plot);
#            plt.savefig('output/output_graph_16_plus.png', format='png', dpi=dpi)
#            plt.show()
        
    def export_prevalence ( self ):
        """Export average of last 10 prevalence values for malaria and schisto.
        Current exports the inputs that were passed times two."""
        malaria_avg_prev = sum(self.prevalence_malaria["All"][(N_DAYS_BURN):(N_DAYS)])/(N_DAYS - N_DAYS_BURN)
        schisto_avg_prev = sum(self.prevalence_schisto["All"][(N_DAYS_BURN):(N_DAYS)])/(N_DAYS - N_DAYS_BURN)
#        output = {"schisto":schisto_avg_prev, "malaria":malaria_avg_prev}       
        output = {"schisto":schisto_avg_prev, "malaria":malaria_avg_prev, "t_pzq":self.t_pzq, "t_net":self.t_net, "t_spray":self.t_spray, "use_integration":USE_INTEGRATION, "F_PZQ_TARGET_COV":F_PZQ_TARGET_COV}       
        print json.dumps(output)
        return output
        
if __name__ == '__main__':
    # Initialization #--------------------------------------------------------#
    #Define common functions/values (to reduce runtime)    
    #Currently assumes that no one is infected at time zero
    app = App()
    people = People()
    update_p_malaria_baseline = app.update_p_malaria_baseline
    update_interventions_and_infections = people.update_interventions_and_infections
    append = people.append    

    #Intervention timing calculations
    if MALARIA_TRANS_PATTERN == "seasonal":
        #Error checking
        more_than_8_months = len(PEAK_TRANS_MONTHS) > 8
        discontinuous_months = False
        n_months = len(PEAK_TRANS_MONTHS)
        for n in range(0, n_months - 1):
            cur_month = PEAK_TRANS_MONTHS[n]
            nxt_month = PEAK_TRANS_MONTHS[n+1]
            if (nxt_month-cur_month != -11) and (nxt_month-cur_month != 1):
                discontinuous_months = True
        if discontinuous_months or more_than_8_months:
            print "Error: Peak transmission months must be a continuous block of 8 or fewer months."
        
        #Get length of malaria season based on months input (for one year)
        season_start_date = datetime.date(CUR_YEAR, PEAK_TRANS_MONTHS[0], 1)
        season_end_date = season_start_date + (n_months)*ONE_MONTH - ONE_DAY
        
        malaria_season_len_days = (season_end_date - season_start_date).days
        is_malaria_season_tmp = [False]*(10000)
        
        #Set intervention times
        if USE_INTEGRATION:
            burn_start_date = season_start_date - ONE_MONTH*6
            burn_end_date = season_start_date - ONE_MONTH*4
            #Set burn-in stop time
            app.t_burn_stop = (burn_end_date - burn_start_date).days
            
            pzq_date = season_start_date - ONE_MONTH*4
            net_date = season_start_date - ONE_MONTH*1
            spray_date = season_start_date - ONE_MONTH*1
        else: #Without integration: start burn-in two months before first intervention
            pzq_date = datetime.date(CUR_YEAR, PZQ_MONTH_NUM, 1)
            net_date = datetime.date(CUR_YEAR, ITN_MONTH_NUM, 1)
            spray_date = datetime.date(CUR_YEAR, IRS_MONTH_NUM, 1)
            sim_start_date = min(pzq_date, net_date, spray_date)

            burn_start_date = sim_start_date - ONE_MONTH*2
            burn_end_date = sim_start_date        
            #Set burn-in stop time
            app.t_burn_stop = (burn_end_date - burn_start_date).days
            
            #If they started the first intervention in the middle of the
            #malaria season, burn the model in during malaria season
            if (sim_start_date >= season_start_date) and (sim_start_date < season_end_date):
                is_malaria_season_tmp[0:app.t_burn_stop] = [True]*app.t_burn_stop
                          
        #Set intervention times
        #PZQ
        app.t_pzq = (pzq_date - burn_start_date).days
        #Nets
        app.t_net = (net_date - burn_start_date).days
        #Spray
        app.t_spray = (spray_date - burn_start_date).days

            
        #Set season start and end times
        t_season_start = (season_start_date - burn_start_date).days
        t_season_end = (season_end_date - burn_start_date).days
        
        #Setup variable that states whether each time step is in malaria season
        #or not in malaria season for the number of days the simulation should
        #be run
        season_start_date_tmp = season_start_date
        season_end_date_tmp = season_end_date
        is_malaria_season_tmp[t_season_start:t_season_end] = [True]*malaria_season_len_days
        while(True):        
            if t_season_end >= N_DAYS:
                break #STOP
            season_start_date_tmp += ONE_YEAR
            t_season_start = (season_start_date_tmp - burn_start_date).days
            if t_season_start >= N_DAYS:
                break #STOP
            season_end_date_tmp += ONE_YEAR
            t_season_end = (season_end_date_tmp - burn_start_date).days
            is_malaria_season_tmp[t_season_start:t_season_end] = [True]*malaria_season_len_days
        app.is_malaria_season = is_malaria_season_tmp[0:N_DAYS]    
    else: #not seasonal: start burn-in two months before first intervention
        if USE_INTEGRATION:
            #Set burn-in stop time
            app.t_burn_stop = N_DAYS_BURN
            
            pzq_date = datetime.date(CUR_YEAR, PZQ_MONTH_NUM, 1)
            sim_start_date = pzq_date
            
            burn_start_date = pzq_date - ONE_MONTH*2
            burn_end_date = sim_start_date

            net_date = pzq_date + ONE_MONTH*3
            spray_date = net_date
        else: #Without integration: start burn-in two months before first intervention
            #Set burn-in stop time
            app.t_burn_stop = N_DAYS_BURN
            
            #First intervention will be the first in the calendar year, starting
            #from January; given on the first of the month input by the user
            pzq_date = datetime.date(CUR_YEAR, PZQ_MONTH_NUM, 1)
            net_date = datetime.date(CUR_YEAR, ITN_MONTH_NUM, 1)
            spray_date = datetime.date(CUR_YEAR, IRS_MONTH_NUM, 1)
            sim_start_date = min(pzq_date, net_date, spray_date)
                          
        #Set intervention times
        #PZQ
        app.t_pzq = (pzq_date - sim_start_date).days + N_DAYS_BURN
        #Nets
        app.t_net = (net_date - sim_start_date).days + N_DAYS_BURN
        #Spray
        app.t_spray = (spray_date - sim_start_date).days + N_DAYS_BURN

    #Create list of people
    for n in range(0, N_PEOPLE):
        append(Person())
    
    #For each time step:
    for t in range(0, N_DAYS):
#       print "Running time step %i of %i" % (t + 1, N_DAYS)
       
       # Initialization #-----------------------------------------------------#
       app.cur_time_step = t

       #Update the daily probability of being infected with malaria based on
       #(1) seasonality (if enabled) and (2) vector pressure. Note: The effect
       #of vector pressure has not yet been implemented.
       update_p_malaria_baseline()

       # Interventions / Infections / Prevalence #----------------------------#
       #Apply interventions at the proper times and update everyone's malaria
       #and schisto infection status. Also update the prevalence vs. time
       #series for this time step.
       update_interventions_and_infections(app)
        
    #End model timer and print the time elapsed.
    end = time.time()
#    print "Time elapsed (sec): %f" % (end-start)
#    print "Getting outputs..."
    
    #Write prevalence values to three CSV files and plot it for 5-15 y/o
    app.write_prevalence()
    
    #Write JSON output (print)
    app.export_prevalence()