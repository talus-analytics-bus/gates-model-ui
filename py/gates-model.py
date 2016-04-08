# -*- coding: utf-8 -*-
"""
Created on Wed Jan 27 08:53:24 2016
Updated on Tue Apr 05

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
import math
start = time.time()

"Initialize variables and constants"
#Load from JS GUI
USE_GUI = True
X_TICKS = 60 #number of days along x-axis ticks
DEBUG_MODE = True
if USE_GUI:
    for line in sys.stdin:
        UI_INPUTS = json.loads(line)
else:
    JSON_FILE = open("debug/debug_inputs.json")    
    UI_INPUTS = json.load(JSON_FILE)
    UI_INPUTS['use_integration'] = False

#Show plots or not
SHOW_PLOTS = False
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
IRS_MONTH_NUM = int(UI_INPUTS["irs_month_num"]) #Month IRS are distributed in the "constant" case (without integration). Indexed
                                #from 1 (i.e., January = 1)
ITN_CHECKED = bool(int(UI_INPUTS["itn"]))  #Can insecticide-treated bed nets be used? True or false.
F_ITN_TARGET_COV = float(UI_INPUTS["itn_coverage"]) #Target % coverage of indoor spraying.
ITN_MONTH_NUM = int(UI_INPUTS["itn_month_num"]) #Month nets are distributed in the "constant" case (without integration). Indexed
                                #from 1 (i.e., January = 1)
#If not using ITN or not using IRS, set their distro date to the same
#date as PZQ so that they don't interfere with time
if not IRS_CHECKED:
    IRS_MONTH_NUM = PZQ_MONTH_NUM
if not ITN_CHECKED:
    ITN_MONTH_NUM = PZQ_MONTH_NUM

#Initialize non-user-specified, constant inputs
CUR_YEAR = 2016
N_PEOPLE = 1000    #Number of people to simulate
N_DAYS_BURN_INIT = 365    #Baselineumber of days to burn in the model to steady-state values. Note that the burn period can be longer if the model starts in the middle of malaria season
N_DAYS_BURN = N_DAYS_BURN_INIT #Duration of the burn in period (may vary)
#N_PEOPLE = 10000    #Number of people to simulate
N_DAYS_SIM = 365*1 #Duration of the simulation
    
D_PROTECT = 20      #Number of days malaria treatment protects against re-
                    #infection (default is 20)
F_ASYMP = 0.28      #The fraction of people infected with malaria who are
                    #asymptomatic (do not get treatment) (Mbah et al, 2014)
F_TREATED = 0.8     #TO DO: Figure out a good way to initialize this value
                    #The fraction of people with symptomatic malaria who get
                    #treatment
F_SYMP_TREATED = (1 - F_ASYMP)*F_TREATED #The fraction of people who get 
                                        #malaria, are symptomatic, and get treatment
F_SYMP_UNTREATED = (1 - F_ASYMP)*(1 - F_TREATED) #The fraction of people who get malaria,
                                                #are symptomatic, and don't get treatment
BREAKPOINT_1 = F_SYMP_TREATED #Used when randomly binning malaria infectives
BREAKPOINT_2 = F_SYMP_TREATED + F_SYMP_UNTREATED

D_MALARIA = 5 #Malaria infection lasts about 5 days (Mbah et al, 2014)
D_PAT_ASYMP_MALARIA = 180 #Patent malaria infection lasts 180 days (Mbah et al 2014)
D_SUBPAT_ASYMP_MALARIA = 180 #Subpatent malaria infection lasts 180 days (Mbah et al 2014)
INIT_P_MALARIA_BASELINE =  1.0 - math.exp(-1.0 * float(N_BASELINE_INF_BITES) * (1 / 365.0)) #Baseline daily prob. of getting malaria.
F_SCHISTO_COINFECTION_MOD = 1.85 #Source: (Mbah et al, 2014)
P_MALARIA_SEASONAL_MOD = 5.0  #Factor by which the daily prob. of getting malaria
                            #increases during malaria season (Kelly-Hope and McKenzie 2009; based on difference between places with 7 or more months of rain vs. 6 or fewer)
NET_EFFICACY =  0.53 #(average of results from Eisele et al., 2010 and Guyatt et al., 2002)
SPRAY_EFFICACY = 0.65 #(Guyatt 2002)

#TO DO: Justin figuring out these values
P_SCHISTO = 0.45 #Fraction of people that get schisto infections (applied at model run initialization)

##Vector-related constants (for future version)
##Number of susceptible vectors (assume 4% are infected at the start
##of the simulation)
#F_INF = 0.04 #Assumed
#F_SUS = 1 - F_INF
#TIME_DELTA = 1.0 #days, 1 by default (model time step is 1 day)
#a = 0.67 #bites per day on humans by a female vector (Mbah et al 2014)
#b = 0.25 #probability of successful human inoculation upon an infectious bite (Mbah et al 2014)
#MU_M = 0.125 #mosquito natural mortality rate (Mbah et al, 2014)
#T_INCUB = 10.0 #mosquito incubation period, days (Mbah et al, 2014)
#PSI = math.exp(-1.0 * MU_M * T_INCUB) #fraction of mosquitos that survive the incubation period and become infectious (Mbah et al, 2014)
#I_M_0 = 0.04 #percent of vector population infected with malaria at time zero
##Total number of vectors (assumed constant)
#NUM_VEC = N_PEOPLE * float(N_BASELINE_INF_BITES) / (I_M_0 * a * b)
#C_D = 0.3 #probability of vector infection upon biting a human in a state of untreated symptomatic malaria (Mbah et al 2014)
#C_A = 0.1 #probability of vector infection upon biting a human in a state of asymp patent malaria (Mbah et al 2014)
#C_U = 0.05 ##probability of vector infection upon biting a human in a state of asymp subpatent malaria (Mbah et al 2014)
        
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
        runif = random.random
        
        # Malaria parameters #------------------------------------------------#
        self.has_malaria = False #do they have malaria?
        self.is_symptomatic = False #if they have malaria, is it symptomatic?
        self.days_to_asymp_malaria = -1 #days until patent asymptomatic malaria start
        self.pat_malaria_days_left = -1 #days left of patent asymptomatic malaria
        self.subpat_malaria_days_left = -1 #days left of subpatent asymptomatic malaria
        self.symp_malaria_days_left = -1 #days left of symptomatic malaria
        self.protection_days_left = -1 #days left of malaria protection
        
        # Schisto parameters #------------------------------------------------#
        get_schisto_runif = runif()
        if get_schisto_runif < P_SCHISTO:
            self.has_schisto = True #do they have schistosomiasis?
        else:
            self.has_schisto = False
        self.has_PZQ = False #were they given PZQ at T_PZQ?

        # Intervention parameters #-------------------------------------------#
        self.has_net = False #do they have protection from bed nets?
        self.has_spray = False #do they have protection from sprays?

        # Age parameters #----------------------------------------------------#
        #Determine age bin for this person:
        age_bin_runif = runif()
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
    def __init__( self ):
        self.D = 0.0
        self.A = 0.0
        self.U = 0.0
        
    def update_interventions_and_infections( self, app):
#    def update_interventions_and_infections( self, app, vectors):
        """Once per time step, check whether each person gets malaria and/or
        schisto. Also, check whether a person's malaria timer has ended; if so,
        flag them as no longer having malaria."""
        t = app.cur_time_step
        runif = random.random
        #Update counts
        self.D = 0.0
        self.A = 0.0
        self.U = 0.0
        for n in range(0, Person.count):
            cur_person = self[n]
            # Timers #--------------------------------------------------------#
            #Reduce the number of days of protection left from ACT by 1. Do the 
            #same thing for the number of days of malaria sickness
            cur_person.days_to_asymp_malaria -= 1;            
            cur_person.pat_malaria_days_left -= 1;            
            cur_person.subpat_malaria_days_left -= 1;            
            cur_person.symp_malaria_days_left -= 1;            
            cur_person.protection_days_left -= 1;
            
            # Interventions #-------------------------------------------------#
            #Apply interventions at appropriate times
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
            symp_malaria_ends_today = cur_person.symp_malaria_days_left == 0    
            pat_malaria_starts_today = cur_person.days_to_asymp_malaria == 0
            pat_malaria_ends_today = cur_person.pat_malaria_days_left == 0
            subpat_malaria_ends_today = cur_person.subpat_malaria_days_left == 0
            
            #UNTREATED SYMPTOMATIC: Transitioning from symp to asymp patent malaria
            #If person is switching from symptomatic to asymptomatic malaria
            #today, update flags accordingly
            if pat_malaria_starts_today:
                #Set their symptomatic flag to false
                cur_person.is_symptomatic = False
                #Ensure their has malaria flag is still true
                cur_person.has_malaria = True
                #Set days of patent malaria remaining
                cur_person.pat_malaria_days_left = D_PAT_ASYMP_MALARIA  
                
                #Update counts
                self.D -= 1 #goes from untreat symp to patent
                self.A += 1
            
            #TREATED SYMPTOMATIC: Transition from symp malaria to no malaria
            #Else, if person's symptomatic malaria ends today and they had protection
            #which means they won't transition to asymptomatic malaria
            elif symp_malaria_ends_today and cur_person.days_to_asymp_malaria < 0:
                #Set has malaria flag to false
                cur_person.has_malaria = False
                #Set their symptomatic flag to false
                cur_person.is_symptomatic = False
            
            #UNTREATED SYMPTOMATIC and UNTREATED ASYMPTOMATIC: Transition from
            #patent to subpatent
            elif pat_malaria_ends_today:
                #Set has malaria flag to false
                cur_person.has_malaria = True
                #Set their symptomatic flag to false
                cur_person.is_symptomatic = False
                #Start their subpatent malaria infection timer
                cur_person.subpat_malaria_days_left = D_SUBPAT_ASYMP_MALARIA
                #Update counts
                self.A -= 1 #goes from patent to subpatent
                self.U += 1
                
            #Transition from subpatent to no infection:
            elif subpat_malaria_ends_today:
                #Set has malaria flag to false
                cur_person.has_malaria = False
                #Set their symptomatic flag to false
                cur_person.is_symptomatic = False
                
                #Decrease count
                self.U -= 1 #Goes from subpatent to clear
            
            #If the person is currently protected from malaria by having
            #received ACT, skip them. Otherwise, continue.            
            is_protected = cur_person.protection_days_left > 0
            if not is_protected:
                #Check the person's intervention and schisto flags and modify
                #their P_MALARIA value accordingly
#                cur_p_malaria = cur_p_malaria_baseline
#                cur_AEIR = app.AEIR
                cur_AEIR = float(N_BASELINE_INF_BITES) #for not using mosquitoes
                if app.is_malaria_season[t]:
                    cur_AEIR *= P_MALARIA_SEASONAL_MOD
                if cur_person.has_schisto:
                    # cur_p_malaria *= F_SCHISTO_COINFECTION_MOD
                    cur_AEIR *= F_SCHISTO_COINFECTION_MOD
                if cur_person.has_net:
                    # cur_p_malaria *= (1 - NET_EFFICACY)
                    cur_AEIR *= (1 - NET_EFFICACY)
                if cur_person.has_spray:
                    # cur_p_malaria *= (1 - SPRAY_EFFICACY)
                    cur_AEIR *= (1 - SPRAY_EFFICACY)
                cur_p_malaria = 1.0 - math.exp(-1.0 * cur_AEIR * (1.0 / 365.0))
                if cur_p_malaria > 1:
                    cur_p_malaria = 1
                    
                #Randomly test whether the person gets malaria this day     
                get_malaria_runif = runif()
                if get_malaria_runif < cur_p_malaria:
                    #If the current person already has asymptomatic malaria,
                    #or if they don't have malaria yet:
                    has_pat_malaria = cur_person.pat_malaria_days_left > 0
                    has_subpat_malaria = cur_person.subpat_malaria_days_left > 0
                    
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
                            cur_person.pat_malaria_days_left = -1
                            cur_person.subpat_malaria_days_left = -1
                            
                            #Update counters
                            if has_pat_malaria: #went from pat to treated
                                self.A -= 1
                            elif has_subpat_malaria: #went from subpat to treated
                                self.U -= 1
                            
                        #SYMPTOMATIC, UNTREATED
                        elif symp_treat_runif >= BREAKPOINT_1 and symp_treat_runif < BREAKPOINT_2:
                            #Set symp malaria values:                            
                            cur_person.is_symptomatic = True
                            cur_person.symp_malaria_days_left = D_MALARIA
                            cur_person.protection_days_left = -1
                            
                            #Later, get asymp malaria:
                            cur_person.days_to_asymp_malaria = D_MALARIA
                            cur_person.pat_malaria_days_left = -1
                            cur_person.subpat_malaria_days_left = -1
                            
                            #Update counters
                            self.D += 1 #went from ??? to untreat symp
                            #Update counters
                            if has_pat_malaria: #left patent
                                self.A -= 1
                            elif has_subpat_malaria: #left subpatent
                                self.U -= 1
                            
                        #ASYMPTOMATIC, UNTREATED
                        else: 
                            #Don't get symp malaria:                            
                            cur_person.is_symptomatic = False
                            cur_person.symp_malaria_days_left = -1
                            cur_person.protection_days_left = -1
                            
                            #Instantly get asymp malaria:
                            cur_person.days_to_asymp_malaria = -1
                            cur_person.pat_malaria_days_left = D_PAT_ASYMP_MALARIA
                            cur_person.subpat_malaria_days_left = -1
                            
                            #Increment count
                            if has_pat_malaria: #from pat to pat
                                pass
                            elif has_subpat_malaria: #from subpat to pat
                                self.A += 1
                                self.U -= 1
                            
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
                        cur_person.pat_malaria_days_left = -1
                        cur_person.subpat_malaria_days_left = -1
            
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
            
            #D: Untreat symp
            if cur_person.is_symptomatic and cur_person.protection_days_left < 0:
                self.D += 1
            #A: Patent
            elif cur_person.pat_malaria_days_left > 0:
                self.A += 1
            #U: Subpatent
            elif cur_person.subpat_malaria_days_left > 0:
                self.U += 1
#        #Update vectors (for  future version)
#        vectors.update_vectors(people)
#        updated_I_m = vectors.inf / (vectors.inf + vectors.sus)
#        app.AEIR = updated_I_m * a * b * NUM_VEC / N_PEOPLE

#The code commented out below is a planned feature for a future version of the
#model which will handle the interacti
#class Vectors( object ):
#    """Class that defines the vector pool. In this model, the malaria vector
#    is modeled as a pool of mosquitoes that can be either susceptible (S) to
#    malaria or infected (I) with malaria."""
#    
#    def __init__( self , NUM_VEC ):
#        
#        #Number of susceptible vectors        
#        self.sus = NUM_VEC * F_SUS    
#    
#        #Number of infected vectors
#        self.inf = NUM_VEC * F_INF
#        
#    def update_vectors( self, people ):
#        """Run at each time step to update the total number of susceptible (S)
#        and infectious (I) mosquitoes in the simulation. This is affected by
#        number of people with each type of malaria. A constant vector
#        population is assumed."""
#        
#        #Initialize variables
#        sus = self.sus
#        inf = self.inf
#                
#        #constant, will be replaced with equation from (Mbah et al, 2014)
#        D = people.D #symp untreat
#        A = people.A #patent
#        U = people.U #subpatent
#        total_inf_people = D + A + U
#        D_frac = D / total_inf_people
#        A_frac = A / total_inf_people
#        U_frac = U / total_inf_people
#        Lambda_M_vec = a * (C_D * D_frac + C_A * A_frac + C_U * U_frac)
#                
#        #Update differential equations (Mbah et al, 2014)
#        dS_M = TIME_DELTA * ((MU_M * (sus + inf)) - (Lambda_M_vec * sus * PSI) - (MU_M * sus))
#        dI_M = TIME_DELTA * ((Lambda_M_vec * sus * PSI) - (MU_M * inf))
#        
#        #Update variables
#        self.sus += dS_M
#        self.inf += dI_M
#        
#    def debug_vectors( self, people ):
#        for n in range(0,60):
#            self.update_vectors(people)
        
#        print (self.inf/(self.inf + self.sus))

class App( object ):
    """Class defining application parameters and output writing functions."""
    #Values
    cur_time_step = 0
    N_DAYS_TOT = N_DAYS_SIM + N_DAYS_BURN
    is_malaria_season = [False]*N_DAYS_TOT
    
#    cur_p_malaria_baseline = INIT_P_MALARIA_BASELINE
    def initialize_prevalence_counts( self ):
        N_DAYS_TOT = N_DAYS_SIM + N_DAYS_BURN
        self.prevalence_schisto = \
        {'0-4': [0.0]*N_DAYS_TOT, '5-15': [0.0]*N_DAYS_TOT, '16+': [0.0]*N_DAYS_TOT}
        self.prevalence_malaria = \
        {'0-4': [0.0]*N_DAYS_TOT, '5-15': [0.0]*N_DAYS_TOT, '16+': [0.0]*N_DAYS_TOT}   
        self.prevalence_coinfection = \
        {'0-4': [0.0]*N_DAYS_TOT, '5-15': [0.0]*N_DAYS_TOT, '16+': [0.0]*N_DAYS_TOT}    
    
    #Functions
#    def update_p_malaria_baseline(self):
#        """Modifies the baseline daily probability of being infected with
#        malaria based on (1) seasonality and (2) vector pressure (to-do)."""
#        #If the current time step is malaria season and the previous one
#        #was not, multiply the daily probability of getting malaria by the
#        #seasonal modifier.
#        cur_time_step = self.cur_time_step
#        prev_time_step = cur_time_step - 1
#        is_malaria_season = self.is_malaria_season
#        
#        #Note: the model assumes the time step before the FIRST time step
#        #(i.e., time step -1) is NOT malaria season
#        if prev_time_step == -1:
#            self.cur_p_malaria_baseline = INIT_P_MALARIA_BASELINE
#        elif is_malaria_season[cur_time_step] and not is_malaria_season[prev_time_step]:
#            self.cur_p_malaria_baseline *= P_MALARIA_SEASONAL_MOD
#        elif not is_malaria_season[cur_time_step] and is_malaria_season[prev_time_step]:
#            self.cur_p_malaria_baseline /= P_MALARIA_SEASONAL_MOD
#            
#        #TO DO: Update p_malaria based on vector pressure. Justin and/or the
#        #GWU team will figure out the best way to approach this.
    def __init__( self ):
        #Initialize baseline AEIR (for time zero)
        self.AEIR = float(N_BASELINE_INF_BITES)
        
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
        
        N_DAYS_TOT = N_DAYS_SIM + N_DAYS_BURN
        
        #Store the prevalence for each disease (y) vs. time (x)
        x = range(0, N_DAYS_TOT)
        y = {}
        y["schisto"] = {"0-4":[0]*N_DAYS_TOT,"5-15":[0]*N_DAYS_TOT,"16+":[0]*N_DAYS_TOT,"All":[0]*N_DAYS_TOT}
        y["malaria"] = {"0-4":[0]*N_DAYS_TOT,"5-15":[0]*N_DAYS_TOT,"16+":[0]*N_DAYS_TOT,"All":[0]*N_DAYS_TOT}
        y["coinfection"] = {"0-4":[0]*N_DAYS_TOT,"5-15":[0]*N_DAYS_TOT,"16+":[0]*N_DAYS_TOT,"All":[0]*N_DAYS_TOT}

        title_spaces = [""]*6
        spaces = [""]*2
        header_str = ["Time (d)","0-4 y/o","5-15 y/o","16+ y/o","All"]
        headers = header_str + spaces + header_str + spaces + header_str
        
        with open('output/output' + fn_int + '.csv', 'wb') as csvfile:
            writer = csv.writer(csvfile, quoting = csv.QUOTE_NONNUMERIC)
            title = ["Prevalence of schistosomiasis by age group vs. time (d)"] + title_spaces + ["Prevalence of malaria by age group vs. time (d)"] + title_spaces + ["Prevalence of coinfection by age group vs. time (d)"]
            writer.writerow(title)
            writer.writerow(headers)
            for t in range(0, N_DAYS_TOT):
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
            shifted_x = [(x[val]- N_DAYS_BURN)/30.0 for val in range(len(x))]
            plt.plot(shifted_x,y["schisto"][age_group_to_plot],label="Schistosomiasis"); 
            plt.plot(shifted_x,y["malaria"][age_group_to_plot],label="Malaria"); 
#            plt.plot(shifted_x,y["coinfection"][age_group_to_plot],label="Coinfection");
            
            plt.legend();
            if DEBUG_MODE:
                y_shift = 0.0
                #PZQ
                plt.plot((self.t_pzq-N_DAYS_BURN)/30.0,0.5,'.');
                plt.text((self.t_pzq-N_DAYS_BURN)/30.0,0.5 + y_shift,"t_pzq: " + pzq_date.isoformat(),rotation=45)
                
                #Nets
                plt.plot((self.t_net-N_DAYS_BURN)/30.0,0.6,'.');
                plt.text((self.t_net-N_DAYS_BURN)/30.0,0.6 + y_shift,"t_net: " + net_date.isoformat(),rotation=45);
                
                #Sprays
                plt.plot((self.t_spray-N_DAYS_BURN)/30.0,0.7,'.');
                plt.text((self.t_spray-N_DAYS_BURN)/30.0,0.7 + y_shift,"t_spray: " + spray_date.isoformat(),rotation=45);       
                
                if not self.t_season_start == -1:
                    for cur_season in range(0,len(self.t_season_start)):
                        cur_t_start = self.t_season_start[cur_season]
                        cur_t_end = self.t_season_end[cur_season]
                        
                        cur_season_start_date = self.burn_start_date + ONE_DAY*cur_t_start
                        cur_season_end_date = self.burn_start_date + ONE_DAY*cur_t_end
                        
                        #Season start
                        plt.plot((cur_t_start - N_DAYS_BURN)/30.0,0.8,'.');
                        plt.text((cur_t_start - N_DAYS_BURN)/30.0,0.8 + y_shift,"t_seas_start: " + cur_season_start_date.isoformat(),rotation=45);       
                        
                        #Season end
                        plt.plot((cur_t_end - N_DAYS_BURN)/30.0,0.8,'.');
                        plt.text((cur_t_end - N_DAYS_BURN)/30.0 - .5,0.8 + y_shift,"t_seas_end: " + cur_season_end_date.isoformat(),rotation=45);
            plt.grid(True);
            plt.xlabel("Time (months)");
            plt.xticks(range(-4,int(math.ceil(N_DAYS_SIM/30.0)),2));
            plt.xlim(-4,N_DAYS_SIM/30.0)
            plt.ylabel("Prevalence (fraction of population)")
            plt.ylim([0,1]);
            plt.title("Disease Prevalence vs. Time (months) for " + age_group_to_plot + integration);
#            
    ##            fig, ax = plt.subplots()
    ##            plt.scatter(x, y)
    #            plt.scatter(x[0],y[0])
    #            plt.annotate(n[0], (x[0],y[0]))
    ##            for i, txt in enumerate(n):
    ##                plt.annotate(txt, (x[i],y[i]))
            
            plt.savefig('output/output_graph_all_ages' + fn_int + '.png', format='png', dpi=dpi)
            plt.savefig('output/output_graph_all_ages' + fn_int + '.svg', format='svg')
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
        N_DAYS_TOT = N_DAYS_SIM + N_DAYS_BURN
        malaria_avg_prev = sum(self.prevalence_malaria["All"][(N_DAYS_BURN):(N_DAYS_TOT)])/(N_DAYS_TOT - N_DAYS_BURN)
        schisto_avg_prev = sum(self.prevalence_schisto["All"][(N_DAYS_BURN):(N_DAYS_TOT)])/(N_DAYS_TOT - N_DAYS_BURN)
#        output = {"schisto":schisto_avg_prev, "malaria":malaria_avg_prev}   
        if not IRS_CHECKED:
            irs_output = "N/A"
        else:
            irs_output = self.spray_date.strftime("%m")
            
        if not ITN_CHECKED:
            itn_output = "N/A"
        else:
            itn_output = self.net_date.strftime("%m")
            
        output = {\
        "schisto":schisto_avg_prev,\
        "malaria":malaria_avg_prev,\
        "pzq_month":self.pzq_date.strftime("%m"),\
        "net_month":itn_output,\
        "spray_month":irs_output,\
        "use_integration":USE_INTEGRATION,\
        }       
        print json.dumps(output)
        return output
        
if __name__ == '__main__':
    # Initialization #--------------------------------------------------------#
    #Define common functions/values (to reduce runtime)    
    #Currently assumes that no one is infected at time zero
    app = App()
    people = People()
#    update_p_malaria_baseline = app.update_p_malaria_baseline
    update_interventions_and_infections = people.update_interventions_and_infections
    append = people.append    

    #Initialize lists of season start and end dates
    season_start_dates = list()
    season_end_dates = list()
    
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
        season_end_date = season_start_date + (n_months)*ONE_MONTH
        malaria_season_len_days = (season_end_date - season_start_date).days
        is_malaria_season_tmp = [False]*(10000)
        
        #Set total days of run
        N_DAYS_TOT = N_DAYS_SIM + N_DAYS_BURN #note that N_DAYS_BURN may be changed below
        year_mod = 0
    
        #Set intervention times
        if USE_INTEGRATION:
            burn_end_date = season_start_date - ONE_MONTH*1
            burn_start_date = burn_end_date - ONE_DAY*N_DAYS_BURN
            
            pzq_date = season_start_date - ONE_MONTH*1
            net_date = season_start_date - ONE_MONTH*1
            spray_date = season_start_date - ONE_MONTH*1

            sim_start_date = burn_end_date
            sim_end_date = sim_start_date + (N_DAYS_SIM)*ONE_DAY            
                            
        else: #Without integration: start burn-in two months before first intervention
            pzq_date = datetime.date(CUR_YEAR, PZQ_MONTH_NUM, 1)
            net_date = datetime.date(CUR_YEAR, ITN_MONTH_NUM, 1)
            spray_date = datetime.date(CUR_YEAR, IRS_MONTH_NUM, 1)
            
            if season_end_date.year > CUR_YEAR:
                season_start_date -= ONE_YEAR
                season_end_date -= ONE_YEAR
                if year_mod == 0:
                    year_mod = -1            
            
            #If necessary, reorder intervention timing so that no interventions
            #are given after the season has already ended
            intervention_dates = (pzq_date, net_date, spray_date)
            last_intervention_date_val = max(intervention_dates)
            new_intervention_dates = [pzq_date, net_date, spray_date]
            
            last_int_given_after_seas_end =   last_intervention_date_val >= season_end_date          
            some_ints_given_earlier = len([i for i, j in enumerate(intervention_dates) if j < season_end_date]) > 0         
            
            if last_int_given_after_seas_end and some_ints_given_earlier:
                which_ints_least = [i for i, j in enumerate(intervention_dates) if j < season_end_date]
                for i in which_ints_least:
                    new_intervention_dates[i] += ONE_YEAR
                season_start_date += ONE_YEAR
                season_end_date += ONE_YEAR
                year_mod = 1                
                pzq_date = new_intervention_dates[0]
                net_date = new_intervention_dates[1]
                spray_date = new_intervention_dates[2]
            
            sim_start_date = min(pzq_date, net_date, spray_date)
            sim_end_date = sim_start_date + (N_DAYS_SIM)*ONE_DAY  
            
#            if season_start_date > season_end_date:
#                season_start_date -= ONE_YEAR
            
           
            
            if season_start_date < sim_start_date:
                season_start_date += ONE_YEAR
                season_end_date += ONE_YEAR
                if year_mod == 0:
                    year_mod = 1

            burn_end_date = sim_start_date        
            burn_start_date = burn_end_date - ONE_DAY*N_DAYS_BURN
            
            #If they started the first intervention in the middle of the
            #malaria season, burn the model in during malaria season
#            if (sim_start_date >= season_start_date) and (sim_start_date < season_end_date):
#                is_malaria_season_tmp[0:app.t_burn_stop] = [True]*app.t_burn_stop
                          
        #Season dates#--------------------------------------------------------#
        #If sim start date is in the season, set the first season start date
        #to the beginning of the burn-in period, and finish the rest of the
        #season when the simulation starts
        sim_starts_in_season = sim_start_date.month in PEAK_TRANS_MONTHS
        if sim_starts_in_season:
            months_to_add =  PEAK_TRANS_MONTHS.index(sim_start_date.month)
            season_start_dates.append(sim_start_date - ONE_MONTH*months_to_add)
            burn_start_date = season_start_dates[0] - ONE_DAY*N_DAYS_BURN
            season_end_dates.append(season_end_date)
        else:
            season_start_dates.append(season_start_date)
            season_end_dates.append(season_end_date)
        
        #Build least of season start/end dates
        cur_season_start_date = datetime.date(CUR_YEAR + year_mod, PEAK_TRANS_MONTHS[0], 1)
        cur_season_end_date = season_end_dates[0]
        while(True):
            next_season_start_date = cur_season_start_date + ONE_YEAR
            next_start_lesst_sim_end = next_season_start_date < sim_end_date
            if next_start_lesst_sim_end:
                season_start_dates.append(next_season_start_date)
                cur_season_start_date += ONE_YEAR
            else:
                break
            next_season_end_date = cur_season_end_date + ONE_YEAR
            next_end_lesst_sim_end = next_season_end_date < sim_end_date
            if next_end_lesst_sim_end:
                season_end_dates.append(next_season_end_date)
                cur_season_end_date += ONE_YEAR
            else:
                season_end_dates.append(sim_end_date)
                break
        
        #Update N_DAYS_BURN AND N_DAYS
        N_DAYS_BURN = (burn_end_date - burn_start_date).days 
        N_DAYS_TOT = N_DAYS_SIM + N_DAYS_BURN
        
        #Set burn-in stop time
        app.t_burn_stop = N_DAYS_BURN
        app.burn_start_date = burn_start_date
        
        #Update sim end date
        sim_end_date = sim_start_date + (N_DAYS_SIM)*ONE_DAY        
        
        #Error check: start and end date lists must be same length
        if len(season_start_dates) is not len (season_end_dates):
            print "Error: season start and end date lists must be same length"
        
        #Build is_malaria_season: bool vec that says whether a day of the sim is malaria season or not
        t_season_start = list()
        t_season_end = list()
        for cur_season in range(0,len(season_start_dates)):
            cur_start = season_start_dates[cur_season]
            cur_end = season_end_dates[cur_season]
            idx_start = (cur_start - burn_start_date).days
            idx_end = (cur_end - burn_start_date).days
            is_malaria_season_tmp[idx_start:idx_end] = [True]*(idx_end-idx_start)
            t_season_start.append(idx_start)
            t_season_end.append(idx_end)
    
        #Set intervention times
        #PZQ
        app.t_pzq = (pzq_date - burn_start_date).days
        #Nets
        app.t_net = (net_date - burn_start_date).days
        #Spray
        app.t_spray = (spray_date - burn_start_date).days
            
        app.is_malaria_season = is_malaria_season_tmp[0:N_DAYS_TOT]
        app.t_season_start = t_season_start;
        app.t_season_end = t_season_end;
    else: #constant (not seasonal): start burn-in two months before first intervention
        if USE_INTEGRATION:
            INT_MONTH_NUM = min(PZQ_MONTH_NUM, ITN_MONTH_NUM, IRS_MONTH_NUM)
            pzq_date = datetime.date(CUR_YEAR, INT_MONTH_NUM, 1)
            
            sim_start_date = pzq_date
            sim_end_date = sim_start_date + (N_DAYS_SIM)*ONE_DAY 
            
            #Set burn-in stop time
            burn_end_date = sim_start_date
            burn_start_date = burn_end_date - ONE_DAY*N_DAYS_BURN
            app.t_burn_stop = (burn_end_date - burn_start_date).days;

            net_date = pzq_date
            spray_date = net_date
            
        else: #Without integration: start burn-in two months before first intervention
            #First intervention will be the first in the calendar year, starting
            #from January; given on the first of the month input by the user
            pzq_date = datetime.date(CUR_YEAR, PZQ_MONTH_NUM, 1)
            net_date = datetime.date(CUR_YEAR, ITN_MONTH_NUM, 1)
            spray_date = datetime.date(CUR_YEAR, IRS_MONTH_NUM, 1)
            sim_start_date = min(pzq_date, net_date, spray_date)
            sim_end_date = sim_start_date + (N_DAYS_SIM)*ONE_DAY 
            
            #Set burn-in stop time
            burn_end_date = sim_start_date
            burn_start_date = burn_end_date - ONE_DAY*N_DAYS_BURN
            app.t_burn_stop = (burn_end_date - burn_start_date).days;
            
        #Set intervention times
        #PZQ
        app.t_pzq = (pzq_date - sim_start_date).days + N_DAYS_BURN
        #Nets
        app.t_net = (net_date - sim_start_date).days + N_DAYS_BURN
        #Spray
        app.t_spray = (spray_date - sim_start_date).days + N_DAYS_BURN

        app.t_season_start = -1
        app.t_season_end = -1

    #Initialize prevalence counters
    app.initialize_prevalence_counts()   
    
    #Create list of people
    for n in range(0, N_PEOPLE):
        append(Person())
    
#    #Initialize vectors and AEIR(0)
#    vectors = Vectors(NUM_VEC)
#    
    #For each time step:
    N_DAYS_TOT = N_DAYS_SIM + N_DAYS_BURN    
    for t in range(0, N_DAYS_TOT):
       if not USE_GUI:
           print "Running time step %i of %i" % (t + 1, N_DAYS_TOT)
       
       # Initialization #-----------------------------------------------------#
       app.cur_time_step = t

#       #Update the daily probability of being infected with malaria based on
#       #(1) seasonality (if enabled) and (2) vector pressure. Note: The effect
#       #of vector pressure has not yet been implemented.
#       update_p_malaria_baseline()

       # Interventions / Infections / Prevalence #----------------------------#
       #Apply interventions at the proper times and update everyone's malaria
       #and schisto infection status. Also update the prevalence vs. time
       #series for this time step.
       update_interventions_and_infections(app)
#       update_interventions_and_infections(app, vectors)
        
    #End model timer and print the time elapsed.
    end = time.time()
#    print "Time elapsed (sec): %f" % (end-start)
#    print "Getting outputs..."
    
    #Write prevalence values to three CSV files and plot it for 5-15 y/o
    app.write_prevalence()
    
    #DEBUG: Write key dates to app
    app.sim_start_date = sim_start_date
    app.sim_end_date = sim_end_date
    if not app.t_season_start == -1:
        app.season_start_date = season_start_date
        app.season_end_date = season_end_date
    app.burn_start_date = burn_start_date
    app.burn_end_date = burn_end_date
    app.pzq_date = pzq_date
    app.net_date = net_date
    app.spray_date = spray_date
    
    #Write JSON output (print)
#    tmp_vec = Vectors(NUM_VEC)
#    tmp_vec.debug_vectors(people)
#    tmp_inf = tmp_vec.inf / (tmp_vec.sus + tmp_vec.inf)
#    app.vec_inf = tmp_inf
    app.export_prevalence()
    
    #DEBUG OUTPUTS#-----------------------------------------------------------#
    #Sim start and end dates (excludes burn-in period)
#    print "Sim start:"    
#    print(sim_start_date)
#    print ""
#
#    print "Sim end:"    
#    print(sim_end_date)
#    print "%i days after sim start" % ((sim_end_date - sim_start_date).days)
#    print ""
#    
#    #PZQ timing    
#    print "PZQ:"    
#    print(pzq_date)
#    print "%i days after sim start" % ((pzq_date - sim_start_date).days)
#    print ""
#    
#    #Net timing    
#    print "Nets:"    
#    print(net_date)
#    print "%i days after sim start" % ((net_date - sim_start_date).days)
#    print ""
#    
#    #Spray timing    
#    print "Sprays:"    
#    print(spray_date)
#    print "%i days after sim start" % ((spray_date - sim_start_date).days)
#    print ""
#    
#    #Seasons (each one)
#    N_SEASONS = 1 #to-do
#    for i in range(0,N_SEASONS):
#        print "Season %i start:" % (i+1)    
#        print(season_start_date)
#        print "%i days after sim start" % ((season_start_date - sim_start_date).days)
#        print ""
#        print "Season %i end:" % (i+1)    
#        print(season_end_date)
#        print "%i days after sim start" % ((season_end_date - sim_start_date).days)
#        print ""
#    
#    
#    