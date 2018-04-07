# -*- coding: utf-8 -*-
from opem.Params import Padulles_Amphlett_InputParams as InputParams
from opem.Params import Padulles_Amphlett_Outparams as OutputParams
from opem.Params import Padulles_Amphlett_Params_Default as Defaults
from opem.Static.Amphlett import Power_Calc,Eta_Act_Calc,Eta_Conc_Calc,Eta_Ohmic_Calc,Loss_Calc,Power_Thermal_Calc,Power_Total_Calc,Linear_Aprox_Params_Calc,Max_Params_Calc
from opem.Dynamic.Padulles1 import PH2_Calc,PO2_Calc,Kr_Calc,qO2_Calc,Efficiency_Calc
from opem.Dynamic.Padulles2 import Enernst_Calc,PH2O_Calc
from opem.Dynamic.Padulles_Hauer import qH2_Calc
from opem.Functions import *
from opem.Params import Padulles_Amphlett_Description,Overall_Params_Max_Description,Overall_Params_Linear_Description
import os

def Vcell_Calc(Enernst, Loss, N):
    """
    This function calculate cell voltage
    :param Enernst:  Enernst [V}
    :type Enernst : float
    :param Loss:  Loss [V]
    :type Loss : float
    :return:  Cell voltage [V] as float
    """
    try:
        result = Enernst - N*Loss
        return result
    except Exception:
        print("[Error] Vcell Calculation Error (Enernst:%s, Loss:%s, N:%s)"%(str(Enernst),str(Loss),str(N)))

def Dynamic_Analysis(InputMethod=Get_Input, TestMode=False, PrintMode=True, ReportMode=True):
    """
    This function run Padulles-Amphlett analysis  with calling other functions
    :param InputMethod : Input Function Or Input Test Vector
    :param TestMode : Test Mode Flag
    :type InputMethod : dict or Get_Input function object
    :type TestMode:bool
    :param PrintMode : Print Mode Control Flag (True : Print Outputs)
    :type PrintMode:bool
    :param ReportMode : Report Mode Control Flag (True : Generate Report)
    :type ReportMode: bool
    :return: Result as dict
    """
    OutputFile = None
    CSVFile = None
    Warning1 = False
    Warning2 = False
    I_Warning = 0
    Overall_Params_Max = {}
    Overall_Params_Linear = {}
    Simulation_Title = "Padulles-Amphlett"
    try:

        if PrintMode==True:
            print("###########")
            print(Simulation_Title+"-Model Simulation")
            print("###########")
        OutputParamsKeys = list(OutputParams.keys())
        OutputParamsKeys.sort()
        Output_Dict = dict(zip(OutputParamsKeys, [None] * len(OutputParamsKeys)))
        if not TestMode:
            Input_Dict = InputMethod(InputParams,params_default=Defaults)
        else:
            Input_Dict = InputMethod
            Input_Dict = filter_default(input_dict=Input_Dict, params_default=Defaults)
        Input_Dict = filter_lambda(Input_Dict)
        if PrintMode==True:
            print("Analyzing . . .")
        Name = Input_Dict["Name"]
        if ReportMode==True:
            OutputFile = Output_Init(Input_Dict,Simulation_Title,Name)
            CSVFile = CSV_Init(OutputParamsKeys,OutputParams,Simulation_Title,Name)
            HTMLFile = HTML_Init(Simulation_Title, Name)
        IEndMax = Input_Dict["JMax"] * Input_Dict["A"]
        IEnd = min(IEndMax, Input_Dict["i-stop"])
        IEnd = Input_Dict["i-stop"]
        IStep = Input_Dict["i-step"]
        Precision = get_precision(IStep)
        i = Input_Dict["i-start"]
        I_List = []
        Power_List = []
        Vstack_List = []
        Efficiency_List = []
        PH2_List = []
        PO2_List = []
        PH2O_List = []
        Eta_Ohmic_List = []
        Eta_Conc_List = []
        Eta_Active_List = []
        Power_Thermal_List = []
        Kr=Kr_Calc(Input_Dict["N0"])
        qH2=qH2_Calc(Input_Dict["qMethanol"],Input_Dict["CV"],Input_Dict["t1"],Input_Dict["t2"])
        qO2=qO2_Calc(qH2,Input_Dict["rho"])
        while i < IEnd:
            try:
                I_List.append(i)
                Output_Dict["PO2"] = PO2_Calc(Input_Dict["KO2"], Input_Dict["tO2"], Kr, i, qO2)
                Output_Dict["PH2"] = PH2_Calc(Input_Dict["KH2"], Input_Dict["tH2"], Kr, i, qH2)
                PH2_List.append(Output_Dict["PH2"])
                PO2_List.append(Output_Dict["PO2"])
                Output_Dict["Eta Activation"] = Eta_Act_Calc(Input_Dict["T"], Output_Dict["PO2"], Output_Dict["PH2"], i,
                                                             Input_Dict["A"])
                Eta_Active_List.append(Output_Dict["Eta Activation"])
                Output_Dict["Eta Ohmic"] = Eta_Ohmic_Calc(i, Input_Dict["l"], Input_Dict["A"], Input_Dict["T"],
                                                          Input_Dict["lambda"], R_elec=Input_Dict["R"])
                Eta_Ohmic_List.append(Output_Dict["Eta Ohmic"])
                Output_Dict["Eta Concentration"] = Eta_Conc_Calc(i, Input_Dict["A"], Input_Dict["B"],
                                                                 Input_Dict["JMax"])
                Eta_Conc_List.append(Output_Dict["Eta Concentration"])
                Output_Dict["Loss"] = Loss_Calc(Output_Dict["Eta Activation"], Output_Dict["Eta Ohmic"],
                                                Output_Dict["Eta Concentration"])
                Output_Dict["PH2O"]=PH2O_Calc(Input_Dict["KH2O"],Input_Dict["tH2O"],Kr,i,qH2)
                PH2O_List.append(Output_Dict["PH2O"])
                Output_Dict["E"]=Enernst_Calc(Input_Dict["E0"],Input_Dict["N0"],Input_Dict["T"],Output_Dict["PH2"],Output_Dict["PO2"],Output_Dict["PH2O"])
                Output_Dict["FC Voltage"]=Vcell_Calc(Output_Dict["E"], Output_Dict["Loss"],Input_Dict["N0"])
                [Warning1, I_Warning] = warning_check_1(Output_Dict["FC Voltage"], I_Warning, i, Warning1)
                Warning2 = warning_check_2(Vcell=Output_Dict["FC Voltage"], warning_flag=Warning2)
                Vstack_List.append(Output_Dict["FC Voltage"])
                Output_Dict["FC Efficiency"] = Efficiency_Calc(Output_Dict["FC Voltage"],Input_Dict["N0"])
                Efficiency_List.append(Output_Dict["FC Efficiency"])
                Output_Dict["FC Power"] = Power_Calc(Output_Dict["FC Voltage"], i)
                Output_Dict["Power-Thermal"] = Power_Thermal_Calc(VStack=Output_Dict["FC Voltage"], N=Input_Dict["N0"], i=i)
                Power_List.append(Output_Dict["FC Power"])
                Power_Thermal_List.append(Output_Dict["Power-Thermal"])
                if ReportMode==True:
                    Output_Save(OutputParamsKeys, Output_Dict,OutputParams, i, OutputFile,PrintMode)
                    CSV_Save(OutputParamsKeys, Output_Dict, i, CSVFile)
                i = rounder(i + IStep, Precision)
            except Exception as e:
                print(str(e))
                i = rounder(i + IStep, Precision)
                if ReportMode==True:
                    Output_Save(OutputParamsKeys, Output_Dict, OutputParams, i, OutputFile,PrintMode)
                    CSV_Save(OutputParamsKeys, Output_Dict, i, CSVFile)
        [Estimated_V, B0, B1] = linear_plot(x=I_List, y=Vstack_List)
        Linear_Approx_Params = Linear_Aprox_Params_Calc(B0, B1)
        Max_Params = Max_Params_Calc(Power_List, Efficiency_List, Vstack_List)
        Power_Total = Power_Total_Calc(Vstack_List, IStep, Input_Dict["N0"])
        Overall_Params_Linear["Pmax(L-Approx)"] = Linear_Approx_Params[0]
        Overall_Params_Linear["V0"] = B0
        Overall_Params_Linear["K"] = B1
        Overall_Params_Linear["VFC|Pmax(L-Approx)"] = Linear_Approx_Params[1]

        Overall_Params_Max["Pmax"] = Max_Params["Max_Power"]
        Overall_Params_Max["VFC|Pmax"] = Max_Params["Max_VStack"]
        Overall_Params_Max["Efficiency|Pmax"] = Max_Params["Max_EFF"]
        Overall_Params_Max["Ptotal(Elec)"] = Power_Total[0]
        Overall_Params_Max["Ptotal(Thermal)"] = Power_Total[1]
        if ReportMode==True:
            HTML_Desc(Simulation_Title, Padulles_Amphlett_Description, HTMLFile)
            HTML_Input_Table(Input_Dict=Input_Dict, Input_Params=InputParams, file=HTMLFile)
            HTML_Overall_Params_Table(Overall_Params_Max, Overall_Params_Max_Description, file=HTMLFile, header=True)
            HTML_Chart(x=str(I_List), y=str(Power_List), color='rgba(255,99,132,1)', x_label="I(A)", y_label="P(W)",
                    chart_name="FC-Power", size="600px", file=HTMLFile)
            HTML_Chart(x=str(I_List), y=[str(Vstack_List), str(Estimated_V)],
                       color=['rgba(99,100,255,1)', 'rgb(238, 210, 141)'], x_label="I(A)", y_label="V(V)",
                       chart_name=["FC-Voltage", "Linear-Apx"], size="600px", file=HTMLFile)
            HTML_Overall_Params_Table(Overall_Params_Linear, Overall_Params_Linear_Description, file=HTMLFile,
                                      header=False)
            HTML_Chart(x=str(I_List), y=[str(Eta_Active_List), str(Eta_Conc_List), str(Eta_Ohmic_List)],
                       color=['rgba(255,99,132,1)', 'rgba(99,100,255,1)', 'rgb(238, 210, 141)'],
                       x_label="I(A)", y_label="V(V)", chart_name=["Eta Active", "Eta Conc",
                                                                   "Eta Ohmic"], size="600px", file=HTMLFile)
            HTML_Chart(x=str(I_List), y=str(Efficiency_List), color='rgb(255, 0, 255)', x_label="I(A)", y_label="EFF",
                       chart_name="Efficiency", size="600px", file=HTMLFile)
            HTML_Chart(x=str(I_List), y=str(PO2_List), color='	rgb(0, 255, 128)', x_label="I(A)", y_label="PO2(atm)",
                       chart_name="PO2", size="600px", file=HTMLFile)
            HTML_Chart(x=str(I_List), y=str(PH2_List), color='	rgb(128, 0, 255)', x_label="I(A)", y_label="PH2(atm)",
                       chart_name="PH2", size="600px", file=HTMLFile)
            HTML_Chart(x=str(I_List), y=str(PH2O_List), color='	rgb(165, 185, 112)', x_label="I(A)",
                       y_label="PH2O(atm)",
                       chart_name="PH2O", size="600px", file=HTMLFile)
            HTML_Chart(x=str(list(map(rounder, Power_List))), y=str(Efficiency_List), color='rgb(238, 210, 141)',
                       x_label="P(W)", y_label="EFF",
                       chart_name="Efficiency vs Power", size="600px", file=HTMLFile)
            HTML_Chart(x=str(I_List), y=str(Power_Thermal_List), color='rgb(255, 0, 255)', x_label="I(A)",
                       y_label="P(W)",
                       chart_name="Power(Thermal)", size="600px", file=HTMLFile)
            warning_print(warning_flag_1=Warning1, warning_flag_2=Warning2, I_Warning=I_Warning, file=HTMLFile,
                          PrintMode=PrintMode)
            HTML_End(HTMLFile)
            OutputFile.close()
            CSVFile.close()
            HTMLFile.close()
        if PrintMode==True:
            print("Done!")
        if not TestMode:
            if PrintMode==True:
                print("Result In -->" + os.path.join(os.getcwd(),Simulation_Title))
        else:
            return {"Status":True,"P": Power_List, "I": I_List, "V": Vstack_List,"EFF":Efficiency_List,"PO2":PO2_List,"PH2":PH2_List,
                    "PH2O":PH2O_List,"Ph":Power_Thermal_List,"V0":B0,"K":B1}
    except Exception:
        if TestMode==True:
            return {"Status":False,"Message":"[Error] "+Simulation_Title+" Simulation Failed!(Check Your Inputs)"}
        else:
            print("[Error] "+Simulation_Title+" Simulation Failed!(Check Your Inputs)")