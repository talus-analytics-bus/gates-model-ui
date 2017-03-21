"""
Gates Foundation Malaria and Schistosomiasis Intervention Timing Model
@author: Mike Van Maele, Justin Kerr

Created on Wed Jan 27, 2016
Updated on Mon May 11, 2016
"""

"Python Standard Libraries (versions listed)"
import time #15.3
import random #9.6
import csv #13.1
import datetime #8.1
import json #18.2
import sys #28.1
import math #9.2

"External Libraries (author and source link listed)"
#python-dateutil (2.0) 
#Author: Gustavo Niemeyer <gustavo@niemeyer.net>
#Accessed 4/17/2016
#URL: https://labix.org/python-dateutil#head-8ec264be46f5eb8d8c6f2c4e371977c3ac861ca0
#Source code: https://launchpad.net/dateutil
import dateutil.relativedelta as date

"Initialize variables and constants"
#Timer
start = time.time()

#Load from JS GUI
USE_GUI = False
X_TICKS = 60 #number of days along x-axis ticks
DEBUG_MODE = True
if USE_GUI:
    for line in sys.stdin:
        UI_INPUTS = json.loads(line)
else:
    RUN_NAME = "032117-gates-call"
    JSON_FILE = open("output/" + RUN_NAME + "/debug_inputs.json")    
    UI_INPUTS = json.load(JSON_FILE)
    UI_INPUTS['use_integration'] = False
             
F_TREATED = 0.80     #Likelihood of being treated with ACT (Uganda Ministry of Health (2015))
    
#F_SCHISTO_COINFECTION_MOD = 1.85 #Source: (Ndeffo Mbah et al. (2014)) 1.16 TO 2.74
F_SCHISTO_COINFECTION_MOD = 1.85 #Source: (Ndeffo Mbah et al. (2014))
IS_COUPLED = ""
if F_SCHISTO_COINFECTION_MOD is 1.0:
    IS_COUPLED = "-uncoupled-" + str(sys.argv[1])
else:
    IS_COUPLED = "-coupled-" + str(sys.argv[1])
#Show plots or not
SHOW_PLOTS = True
if (SHOW_PLOTS):
    import matplotlib.pyplot as plt

#With or without integration
USE_INTEGRATION = bool(int(UI_INPUTS["use_integration"]))
#With or without integration?
if USE_INTEGRATION:
    integration = ", with Integration"
    fn_int = "_with_integration"
else:
    integration = ", without Integration"
    fn_int = "_without_integration"

#Initialize user-specified inputs (pulled from GUI)
N_PEOPLE = int(UI_INPUTS["n_people"])    #Number of people to simulate
F_AGE_UNDER_5 = float(UI_INPUTS["pop1"]) #% distribution of population under 5 years old
F_AGE_5_TO_15 = float(UI_INPUTS["pop2"]) #% distribution of population between 5 and 15 years old
F_AGE_16_PLUS = float(UI_INPUTS["pop3"]) #% distribution of population 16 years old or older

P_SCHISTO = float(UI_INPUTS["schisto_prevalence"]) # % schistosomiasis prevalence
F_PZQ_TARGET_COV = float(UI_INPUTS["schisto_coverage"]) #Target % coverage of praziquantel (PZQ) mass drug 
                        #administration
PZQ_AGE_RANGE = tuple(UI_INPUTS["schisto_age_range"] )#Age groups that get PZQ (by default, only 5-15 y/o 
                    #children will get it because they are school-age and PZQ
                    #interventions may be targeting school-age children)

PZQ_MONTH_NUM = int(UI_INPUTS["schisto_month_num"]) #Month PZQ is distributed in the "constant" case (without integration). Indexed
                                #from 1 (i.e., January = 1)

MALARIA_TRANS_PATTERN = UI_INPUTS["malaria_timing"]  #Malaria transmission pattern. Either
                                    #"Seasonal" (automatically implements integration) or "Constant" (uses user-input intervention timing)
if UI_INPUTS.has_key("malaria_peak_month_num"):
    PEAK_TRANS_MONTHS_TMP = tuple(UI_INPUTS["malaria_peak_month_num"])
    PEAK_TRANS_MONTHS = [ int(x) for x in PEAK_TRANS_MONTHS_TMP ]     #Peak malaria transmission month(s). Indexed
                                #from 1 (i.e., January = 1)
else:
    PEAK_TRANS_MONTHS = []
N_BASELINE_INF_BITES = float(UI_INPUTS["malaria_rate"])  #Baseline infectious mosquito bites per year for
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
N_DAYS_BURN_INIT = 365*2 #Baseline number of days to burn in the model to steady-state values. Note that the burn period can be longer if the model starts in the middle of malaria season
N_DAYS_BURN = N_DAYS_BURN_INIT #Duration of the burn in period (may vary)
N_DAYS_SIM = 365 #Duration of the simulation

P_INFECT = 0.25 #Proability of successful human inoculation upon an infectious bite (Ndeffo Mbah et al. (2014))
D_PROTECT = 20      #Number of days malaria treatment protects against re-
                    #infection (default is 20) (Ndeffo Mbah et al. (2014) and Griffin et al. (2010))
F_ASYMP = 0.28      #The fraction of people infected with malaria who are
                    #asymptomatic (do not get treatment) (Ndeffo Mbah et al. (2014) and Griffin et al. (2010))

F_SYMP_TREATED = (1 - F_ASYMP)*F_TREATED #The fraction of people who get 
                                        #malaria, are symptomatic, and get treatment
F_SYMP_UNTREATED = (1 - F_ASYMP)*(1 - F_TREATED) #The fraction of people who get malaria,
                                                #are symptomatic, and don't get treatment
BREAKPOINT_1 = F_SYMP_TREATED #Used when randomly binning malaria infectives
BREAKPOINT_2 = F_SYMP_TREATED + F_SYMP_UNTREATED

FRAC_BITES_IN_SEASON = 0.8 #Fraction of AEIR that occur in malaria season
if MALARIA_TRANS_PATTERN is "constant":
    FRAC_BITES_IN_SEASON = 0.0
D_MALARIA = 5 #Malaria infection lasts about 5 days (Ndeffo Mbah et al. (2014) and Griffin et al. (2010))
D_PAT_ASYMP_MALARIA = 180 #Patent malaria infection lasts 180 days (Ndeffo Mbah et al. (2014) and Griffin et al. (2010)) 
D_SUBPAT_ASYMP_MALARIA = 180 #Subpatent malaria infection lasts 180 days (Ndeffo Mbah et al. (2014) and Griffin et al. (2010))
INIT_P_MALARIA_BASELINE =  1.0 - math.exp(-1.0 * float(N_BASELINE_INF_BITES) * (1 / 365.0)) #Baseline daily prob. of getting malaria.
P_MALARIA_SEASONAL_MOD = 5.0  #Factor by which the daily prob. of getting malaria
                            #increases during malaria season (Kelly-Hope and McKenzie 2009; based on difference between places with 7 or more months of rain vs. 6 or fewer)
NET_EFFICACY =  0.53 #(average of results from Eisele et al. (2010) and Guyatt et al. (2002))
SPRAY_EFFICACY = 0.65 #(Guyatt et al. (2002))

##Vector-related constants (for future version)
##Number of susceptible vectors (assume 4% are infected at the start
##of the simulation)
#F_INF = 0.04 #Assumed
#F_SUS = 1 - F_INF
#TIME_DELTA = 1.0 #days, 1 by default (model time step is 1 day)
#a = 0.67 #bites per day on humans by a female vector (Ndeffo Mbah et al. (2014))
#b = 0.25 #probability of successful human inoculation upon an infectious bite (Ndeffo Mbah et al. (2014))
#MU_M = 0.125 #mosquito natural mortality rate (Ndeffo Mbah et al. (2014))
#T_INCUB = 10.0 #mosquito incubation period, days (Ndeffo Mbah et al. (2014))
#PSI = math.exp(-1.0 * MU_M * T_INCUB) #fraction of mosquitos that survive the incubation period and become infectious (Ndeffo Mbah et al. (2014))
#I_M_0 = 0.04 #percent of vector population infected with malaria at time zero
##Total number of vectors (assumed constant)
#NUM_VEC = N_PEOPLE * float(N_BASELINE_INF_BITES) / (I_M_0 * a * b)
#C_D = 0.3 #probability of vector infection upon biting a human in a state of untreated symptomatic malaria (Ndeffo Mbah et al. (2014))
#C_A = 0.1 #probability of vector infection upon biting a human in a state of asymp patent malaria (Ndeffo Mbah et al. (2014))
#C_U = 0.05 ##probability of vector infection upon biting a human in a state of asymp subpatent malaria (Ndeffo Mbah et al. (2014))
        
#Miscellaneous global constants
ONE_YEAR =  date.relativedelta(years=1)
ONE_MONTH = date.relativedelta(months=1)
ONE_DAY =  date.relativedelta(days=1)   

class Person( object ):
    """ Class that holds all the people.  Representation of the compartmental 
    model are stored as attibutes"""
    
    #Total number of people in memory
    count = 0
    
    #Total number of people with deterministic schisto so far
    schisto_count = 0
    
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
        
        #Deterministic schisto
        if Person.schisto_count < float(N_PEOPLE * P_SCHISTO):
            self.has_schisto = True
            Person.schisto_count = Person.schisto_count + 1.0
        else:
            self.has_schisto = False
#        #Stochastic schisto
#        get_schisto_runif = runif()
#        if get_schisto_runif < P_SCHISTO:
#            self.has_schisto = True #do they have schistosomiasis?
#        else:
#            self.has_schisto = False
            
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
        self.debug_aeir = 0.0 #validate that simulated aeir is approx input aeir
        
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
               # cur_AEIR = N_BASELINE_INF_BITES #for not using mosquitoes
                TEMP = N_BASELINE_INF_BITES
                if app.is_malaria_season[t]:
                    cur_AEIR = (FRAC_BITES_IN_SEASON * TEMP)/app.debug_days_in_season
                else:
                    #do non-seasonal AEIR
                    cur_AEIR = (TEMP - (FRAC_BITES_IN_SEASON * TEMP))/(365.0 - app.debug_days_in_season)
                if cur_person.has_net:
                    cur_AEIR *= (1 - NET_EFFICACY)
                if cur_person.has_spray:
                    cur_AEIR *= (1 - SPRAY_EFFICACY)
                if cur_person.has_schisto:
                    cur_AEIR *= F_SCHISTO_COINFECTION_MOD
                    
                cur_p_malaria = 1.0 - math.exp(-1.0 * cur_AEIR)
                
                if cur_p_malaria > 1.0:
                    cur_p_malaria = 1.0
                
                got_malaria = False
                got_bitten_runif = runif()
                #got_infected_runif = runif()
                got_bitten = got_bitten_runif < cur_p_malaria
                #got_infected = got_infected_runif < P_INFECT
                #got_malaria = got_bitten and got_infected
                got_malaria = got_bitten
                
                #Randomly test whether the person gets malaria this day     
                if got_malaria:
                    #Increment person's total malaria episode counter (symp or asymp)
                    if t > N_DAYS_BURN:
                        app.n_malaria_cases = app.n_malaria_cases + 1
                    
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
                            #Increment person's total symp malaria cases
                            if t > N_DAYS_BURN:
                                app.n_symp_malaria_cases = app.n_symp_malaria_cases + 1
                            
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
                            #Increment person's total symp malaria cases
                            if t > N_DAYS_BURN:
                                app.n_symp_malaria_cases = app.n_symp_malaria_cases + 1
                            
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
                        #Increment person's total symp malaria cases. Assumes we count
                        #"reinfection" episodes as unique episodes
                        if t > N_DAYS_BURN:
                            app.n_symp_malaria_cases = app.n_symp_malaria_cases + 1
                            
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
#        #constant, will be replaced with equation from (Ndeffo Mbah et al. (2014))
#        D = people.D #symp untreat
#        A = people.A #patent
#        U = people.U #subpatent
#        total_inf_people = D + A + U
#        D_frac = D / total_inf_people
#        A_frac = A / total_inf_people
#        U_frac = U / total_inf_people
#        Lambda_M_vec = a * (C_D * D_frac + C_A * A_frac + C_U * U_frac)
#                
#        #Update differential equations (Ndeffo Mbah et al. (2014))
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
    def __init__( self ):
        #Initialize baseline AEIR (for time zero)
        self.AEIR = float(N_BASELINE_INF_BITES)
        self.debug_days_in_season = 0.0
        self.debug_tot_season_days = 0.0
        self.debug_tot_nonseason_days = 0.0
        self.n_symp_malaria_cases = 0 #num of times person got a symptomatic malaria case
        self.n_malaria_cases = 0 #num of times person got symp or asymp malaria case
        
    def write_prevalence( self ):
        #Writes prevalence values and graphs them
    
        
                
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
        
        with open('output/' + RUN_NAME + '/' + RUN_NAME + fn_int + IS_COUPLED + '.csv', 'wb') as csvfile:
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
                if F_PZQ_TARGET_COV > 0.0:
                    #PZQ
                    plt.plot((self.t_pzq-N_DAYS_BURN)/30.0,0.5,'.');
                    plt.text((self.t_pzq-N_DAYS_BURN)/30.0,0.5 + y_shift,"t_pzq: " + pzq_date.isoformat(),rotation=45)
                
                if ITN_CHECKED:
                    #Nets
                    plt.plot((self.t_net-N_DAYS_BURN)/30.0,0.6,'.');
                    plt.text((self.t_net-N_DAYS_BURN)/30.0,0.6 + y_shift,"t_net: " + net_date.isoformat(),rotation=45);
                
                if IRS_CHECKED:
                    #Sprays
                    plt.plot((self.t_spray-N_DAYS_BURN)/30.0,0.7,'.');
                    plt.text((self.t_spray-N_DAYS_BURN)/30.0,0.7 + y_shift,"t_spray: " + spray_date.isoformat(),rotation=45);       
                
                if not self.t_season_start == -1:
                    for cur_season in range(0,len(self.t_season_start)):
                        cur_t_start = self.t_season_start[cur_season]
                        cur_t_end = self.t_season_end[cur_season]
                        
                        if not cur_t_start > N_DAYS_TOT and not cur_t_end > N_DAYS_TOT: 
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
            
            plt.savefig('output/' + RUN_NAME + '/' + RUN_NAME + fn_int + IS_COUPLED + '.png', format='png', dpi=dpi)
            plt.savefig('output/' + RUN_NAME + '/' + RUN_NAME + fn_int + IS_COUPLED + '.svg', format='svg')
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
        output2 = {\
        "schisto":schisto_avg_prev,\
        "malaria":malaria_avg_prev,\
        "n_malaria_cases":self.n_malaria_cases,\
        "n_symp_malaria_cases":self.n_symp_malaria_cases,\
        "pzq_month":self.pzq_date.strftime("%m"),\
        "net_month":itn_output,\
        "spray_month":irs_output,\
        "use_integration":USE_INTEGRATION,\
        }   
        print json.dumps(output)
        with open('output/' + RUN_NAME + '/' + RUN_NAME + fn_int + IS_COUPLED + '.txt', 'wb') as csvfile:
            
            csvfile.write(json.dumps(output2))
        csvfile.close()
        
        with open('output/' + RUN_NAME + '/' + RUN_NAME + fn_int + IS_COUPLED + '-validation'+'.txt', 'wb') as csvfile2:
            
#            csvfile2.write("asymp and symp\t" + str(app.n_malaria_cases) + "\t" + str(100.0 * (app.n_malaria_cases / (N_PEOPLE * (N_DAYS_SIM/365.0)))))
#            csvfile2.write("\tsymp only\t" + str(app.n_symp_malaria_cases) + "\t" + str(100.0 * (app.n_symp_malaria_cases / (N_PEOPLE * (N_DAYS_SIM/365.0)))))
            csvfile2.write(str(100.0 * (app.n_symp_malaria_cases / (N_PEOPLE * (N_DAYS_SIM/365.0)))))
        csvfile2.close()
            
        return output
        
if __name__ == '__main__':
    # Initialization #--------------------------------------------------------#
    #Define common functions/values (to reduce runtime)    
    #Currently assumes that no one is infected at time zero
    app = App()
    people = People()
    update_interventions_and_infections = people.update_interventions_and_infections
    append = people.append    
    
    if MALARIA_TRANS_PATTERN == "seasonal":
        #Integration:        
        if USE_INTEGRATION:
            #Int dist times are one month before the first season "block"
            #start in calendar year
            for cur_month in PEAK_TRANS_MONTHS:
                prev_month = ((cur_month-2) % 12) + 1
                if prev_month not in PEAK_TRANS_MONTHS:
                    int_dist_month = cur_month - 1                    
                    break
            else:
                int_dist_month = 1
                print "Error: no dist month found for seasonal, integrated"
            pzq_date = datetime.date(CUR_YEAR, int_dist_month, 1)
            net_date = datetime.date(CUR_YEAR, int_dist_month, 1)
            spray_date = datetime.date(CUR_YEAR, int_dist_month, 1)
            days_to_shift_burn_start = 0
            
        #Non-integration:
        else:
            #Any ints. distributed out of season? If so, start the sim. with the
            #earliest distributed.
            #0 - PZQ, 1 - nets, 2 - sprays
            #Determine which ints are given out of season, if any
            int_mos = (PZQ_MONTH_NUM,ITN_MONTH_NUM,IRS_MONTH_NUM);
            ints_not_in_seas_idx = [i for i, j in enumerate(int_mos) if j not in PEAK_TRANS_MONTHS]
            some_ints_out_of_seas = len(ints_not_in_seas_idx) > 0
            
            #Make tuple of int dist dates
            pzq_date = datetime.date(CUR_YEAR, PZQ_MONTH_NUM, 1)
            net_date = datetime.date(CUR_YEAR, ITN_MONTH_NUM, 1)
            spray_date = datetime.date(CUR_YEAR, IRS_MONTH_NUM, 1)
            #0 - PZQ, 1 - nets, 2 - sprays
            ints_dates = [pzq_date,net_date,spray_date]
            
            #If some int are given out of season, start sim with earliest of these
            #and if some int distribution dates are prior to this date, push them
            #forward a year
            ints_checked = list()        
            if some_ints_out_of_seas:
                earliest_int_idx = ints_not_in_seas_idx[0]
                earliest_int_date = ints_dates[earliest_int_idx]
                ints_checked.append(earliest_int_idx)
                for i in range(0,3):
                    if i not in ints_checked:
                        cur_int_date = ints_dates[i]
                        cur_int_needs_to_be_pushed = earliest_int_date > cur_int_date
                        if cur_int_needs_to_be_pushed:
                            pushed_cur_int_date = cur_int_date + ONE_YEAR
                            ints_dates[i] = pushed_cur_int_date
                        ints_checked.append(i)
                pzq_date = ints_dates[0]
                net_date = ints_dates[1]
                spray_date = ints_dates[2]
            #If no ints are distributed out of season, distribute them in
            #the user-given order because it doesn't matter (they'll all be
            #in the middle of a season)
            else:
                pass
            
        #Set sim start date to date of first int dist, and sim end date to
        #one year later
        sim_start_date = min(pzq_date,net_date,spray_date)
        sim_end_date = sim_start_date + N_DAYS_SIM * ONE_DAY
        
        #Setup burn-in period seasonality
        #If simulation starts in season, add the correct number of
        #malaria season months to the end of the burn-in
        sim_start_month = sim_start_date.month
        sim_starts_in_seas = sim_start_month in PEAK_TRANS_MONTHS
        burn_end_date = sim_start_date
        burn_seas_end_date = burn_end_date
        if sim_starts_in_seas:
            #Figure out how many months longer burn-in should be
            cur_month = ((sim_start_month-2) % 12) + 1
            months_to_add = 0
            while cur_month in PEAK_TRANS_MONTHS:
                months_to_add += 1
                cur_month = ((cur_month-2) % 12) + 1
            burn_seas_start_date = burn_seas_end_date - months_to_add * ONE_MONTH
        else:
            burn_seas_start_date = burn_seas_end_date
        days_to_shift_burn_start = (burn_seas_end_date - burn_seas_start_date).days
        burn_start_date = sim_start_date - (N_DAYS_BURN + days_to_shift_burn_start) * ONE_DAY

        #Update N_DAYS_BURN and N_DAYS_TOT
        N_DAYS_BURN = (burn_end_date - burn_start_date).days            
        N_DAYS_TOT = N_DAYS_BURN + N_DAYS_SIM            
        
        #Setup variable to track whether it's malaria season
        #Setup burn-in period properly, capturing the need to start in
        #season if necessary
        is_malaria_season_tmp = [False]*(10000)
        burn_start_tstep = 0
        burn_end_tstep = N_DAYS_BURN
        burn_seas_start_tstep = burn_end_tstep - days_to_shift_burn_start
        burn_seas_end_tstep = burn_end_tstep
        is_malaria_season_tmp[burn_seas_start_tstep:burn_seas_end_tstep] =\
            [True]*days_to_shift_burn_start
            
        #Setup other seasonal periods
        sim_start_month = sim_start_date.month
        cur_date = sim_start_date
        t_season_start = list()
        t_season_end = list()
        
        for i in range(0,12):
            cur_month = ((sim_start_month - 1 + i) % 12) + 1
            cur_date_plus_one_month = cur_date + ONE_MONTH
            if cur_month in PEAK_TRANS_MONTHS:
                start_tstep = (cur_date - burn_start_date).days
                end_tstep = start_tstep + (cur_date_plus_one_month - cur_date).days
                is_malaria_season_tmp[start_tstep:end_tstep] = \
                    [True]*(end_tstep - start_tstep)
                print (end_tstep - start_tstep)
                app.debug_days_in_season = app.debug_days_in_season + (end_tstep - start_tstep)
            cur_date = cur_date_plus_one_month
        #Handle last day of simulation (first of the month)
        cur_month = ((sim_start_month - 1 + 12) % 12) + 1
        if cur_month in PEAK_TRANS_MONTHS:
            print (end_tstep - start_tstep)
            cur_date_plus_one_day = cur_date + ONE_DAY
            start_tstep = (cur_date - burn_start_date).days
            end_tstep = start_tstep + (cur_date_plus_one_day - cur_date).days
            is_malaria_season_tmp[start_tstep:end_tstep] = \
                [True]*(end_tstep - start_tstep)
            app.debug_days_in_season = app.debug_days_in_season + (end_tstep - start_tstep)
        is_malaria_season = is_malaria_season_tmp[0:N_DAYS_TOT]
        app.is_malaria_season = is_malaria_season
        
        for i in range(0,len(is_malaria_season)-1):
            cur_step = is_malaria_season[i]
            nxt_step = is_malaria_season[i+1]
            if cur_step and not nxt_step:
                t_season_end.append(i + 1)
            elif nxt_step and not cur_step:
                t_season_start.append(i + 1)
        
        if is_malaria_season[N_DAYS_TOT-1]:
            t_season_end.append(N_DAYS_TOT)
                
        #Set intervention times
        #PZQ
        app.t_pzq = (pzq_date - burn_start_date).days
        #Nets
        app.t_net = (net_date - burn_start_date).days
        #Spray
        app.t_spray = (spray_date - burn_start_date).days
        
        #Set burn in stop time
        app.t_burn_stop = (burn_end_date - burn_start_date).days
        
        #For plotting: Set season start/end times
        app.t_season_start = t_season_start
        app.t_season_end = t_season_end
        
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
    
    #Write key dates to app
    app.sim_start_date = sim_start_date
    app.sim_end_date = sim_end_date
    app.burn_start_date = burn_start_date
    app.burn_end_date = burn_end_date
    app.pzq_date = pzq_date
    app.net_date = net_date
    app.spray_date = spray_date

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

       # Interventions / Infections / Prevalence #----------------------------#
       #Apply interventions at the proper times and update everyone's malaria
       #and schisto infection status. Also update the prevalence vs. time
       #series for this time step.
       update_interventions_and_infections(app)
#       update_interventions_and_infections(app, vectors)
        
    #End model timer and print the time elapsed.
    end = time.time()
    
    #Write prevalence values to three CSV files and plot it for 5-15 y/o
    app.write_prevalence()
    app.export_prevalence()
