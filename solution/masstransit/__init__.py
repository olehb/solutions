"""Mass Transit solution model.
   Excel filename: Drawdown-Mass Transit_RRS_v1.1_29Nov2018_PUBLIC.xlsm
"""

import pathlib

import numpy as np
import pandas as pd

from model import adoptiondata
from model import advanced_controls as ac
from model import ch4calcs
from model import co2calcs
from model import customadoption
from model import dd
from model import emissionsfactors
from model import firstcost
from model import helpertables
from model import operatingcost
from model import s_curve
from model import unitadoption
from model import vma
from model import tam
from solution import rrs

DATADIR = pathlib.Path(__file__).parents[2].joinpath('data')
THISDIR = pathlib.Path(__file__).parents[0]
VMAs = {
  'Current Adoption': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Current_Adoption.csv"),
      use_weight=False),
  'CONVENTIONAL First Cost per Implementation Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "CONVENTIONAL_First_Cost_per_Implementation_Unit.csv"),
      use_weight=False),
  'SOLUTION First Cost per Implementation Unit': vma.VMA(
      filename=None, use_weight=False),
  'CONVENTIONAL Lifetime Capacity': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "CONVENTIONAL_Lifetime_Capacity.csv"),
      use_weight=False),
  'SOLUTION Lifetime Capacity': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Lifetime_Capacity.csv"),
      use_weight=False),
  'CONVENTIONAL Average Annual Use': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "CONVENTIONAL_Average_Annual_Use.csv"),
      use_weight=False),
  'SOLUTION Average Annual Use': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Average_Annual_Use.csv"),
      use_weight=False),
  'CONVENTIONAL Variable Operating Cost (VOM) per Functional Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "CONVENTIONAL_Variable_Operating_Cost_VOM_per_Functional_Unit.csv"),
      use_weight=False),
  'SOLUTION Variable Operating Cost (VOM) per Functional Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Variable_Operating_Cost_VOM_per_Functional_Unit.csv"),
      use_weight=True),
  'CONVENTIONAL Fixed Operating Cost (FOM)': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "CONVENTIONAL_Fixed_Operating_Cost_FOM.csv"),
      use_weight=False),
  'SOLUTION Fixed Operating Cost (FOM)': vma.VMA(
      filename=None, use_weight=False),
  'CONVENTIONAL Total Energy Used per Functional Unit': vma.VMA(
      filename=None, use_weight=False),
  'SOLUTION Energy Efficiency Factor': vma.VMA(
      filename=None, use_weight=False),
  'SOLUTION Total Energy Used per Functional Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Total_Energy_Used_per_Functional_Unit.csv"),
      use_weight=False),
  'CONVENTIONAL Fuel Consumed per Functional Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "CONVENTIONAL_Fuel_Consumed_per_Functional_Unit.csv"),
      use_weight=False),
  'SOLUTION Fuel Efficiency Factor': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Fuel_Efficiency_Factor.csv"),
      use_weight=False),
  'CONVENTIONAL Direct Emissions per Functional Unit': vma.VMA(
      filename=None, use_weight=False),
  'SOLUTION Direct Emissions per Functional Unit': vma.VMA(
      filename=None, use_weight=False),
  'CONVENTIONAL Indirect CO2 Emissions per Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "CONVENTIONAL_Indirect_CO2_Emissions_per_Unit.csv"),
      use_weight=False),
  'SOLUTION Indirect CO2 Emissions per Unit': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "SOLUTION_Indirect_CO2_Emissions_per_Unit.csv"),
      use_weight=False),
  'CH4-CO2eq Tons Reduced': vma.VMA(
      filename=None, use_weight=False),
  'N2O-CO2eq Tons Reduced': vma.VMA(
      filename=None, use_weight=False),
  'CONVENTIONAL Revenue per Functional Unit': vma.VMA(
      filename=None, use_weight=False),
  'SOLUTION Revenue per Functional Unit': vma.VMA(
      filename=None, use_weight=False),
  'Car Insurance Costs': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Car_Insurance_Costs.csv"),
      use_weight=False),
  'Car Purchase (First) Costs': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Car_Purchase_First_Costs.csv"),
      use_weight=True),
  'Car Occupancy Rates': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Car_Occupancy_Rates.csv"),
      use_weight=False),
  'Car Lifetime in Vehicle-km': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Car_Lifetime_in_Vehicle_km.csv"),
      use_weight=False),
  'Discount Rates - Household': vma.VMA(
      filename=THISDIR.joinpath("vma_data", "Discount_Rates_Household.csv"),
      use_weight=False),
}
vma.populate_fixed_summaries(vma_dict=VMAs, filename=THISDIR.joinpath('vma_data', 'VMA_info.csv'))

units = {
  "implementation unit": "Urban trip",
  "functional unit": "Pkm (urban)",
  "first cost": "US$B",
  "operating cost": "US$B",
}

name = 'Mass Transit'
solution_category = ac.SOLUTION_CATEGORY.REDUCTION

scenarios = ac.load_scenarios_from_json(directory=THISDIR.joinpath('ac'), vmas=VMAs)


class Scenario:
  name = name
  units = units
  vmas = VMAs
  solution_category = solution_category

  def __init__(self, scenario=None):
    if scenario is None:
      scenario = list(scenarios.keys())[0]
    self.scenario = scenario
    self.ac = scenarios[scenario]

    # TAM
    tamconfig_list = [
      ['param', 'World', 'PDS World', 'OECD90', 'Eastern Europe', 'Asia (Sans Japan)',
       'Middle East and Africa', 'Latin America', 'China', 'India', 'EU', 'USA'],
      ['source_until_2014', self.ac.source_until_2014, self.ac.source_until_2014,
       'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES',
       'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES'],
      ['source_after_2014', self.ac.ref_source_post_2014, self.ac.pds_source_post_2014,
       'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES',
       'ALL SOURCES', 'ALL SOURCES', 'ALL SOURCES'],
      ['trend', '3rd Poly', '3rd Poly',
       '3rd Poly', '3rd Poly', '3rd Poly', '3rd Poly', '3rd Poly', '3rd Poly',
       '3rd Poly', '3rd Poly', '3rd Poly'],
      ['growth', 'Medium', 'Medium', 'Medium', 'Medium',
       'Medium', 'Medium', 'Medium', 'Medium', 'Medium', 'Medium', 'Medium'],
      ['low_sd_mult', 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
      ['high_sd_mult', 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]
    tamconfig = pd.DataFrame(tamconfig_list[1:], columns=tamconfig_list[0], dtype=np.object).set_index('param')
    tam_ref_data_sources = {
      'Baseline Cases': {
          'ETP 2016, URBAN 6 DS + Non-motorized Travel Adjustment': THISDIR.joinpath('tam', 'tam_ETP_2016_URBAN_6_DS_Nonmotorized_Travel_Adjustment.csv'),
          'ICCT, 2012, "Global Transportation Roadmap Model" + Non-motorized Travel Adjustment': THISDIR.joinpath('tam', 'tam_ICCT_2012_Global_Transportation_Roadmap_Model_Nonmotorized_Travel_Adjustment.csv'),
      },
      'Conservative Cases': {
          'ETP 2016, URBAN 4 DS + Non-motorized Travel Adjustment': THISDIR.joinpath('tam', 'tam_ETP_2016_URBAN_4_DS_Nonmotorized_Travel_Adjustment.csv'),
          'ITDP - UC Davis (2015)  A Global High Shift Cycling Scenario Updated Report Data - Baseline Scenario': THISDIR.joinpath('tam', 'tam_ITDP_UC_Davis_2015_A_Global_High_Shift_Cycling_Scenario_Updated_Report_Data_Baseline_Scenario.csv'),
      },
      'Ambitious Cases': {
          'ETP 2016, URBAN 2 DS + Non-motorized Travel Adjustment': THISDIR.joinpath('tam', 'tam_ETP_2016_URBAN_2_DS_Nonmotorized_Travel_Adjustment.csv'),
          'ITDP - UC Davis (2015)  A Global High Shift Cycling Scenario Updated Report Data - HighShift Scenario': THISDIR.joinpath('tam', 'tam_ITDP_UC_Davis_2015_A_Global_High_Shift_Cycling_Scenario_Updated_Report_Data_HighShift_Scenario.csv'),
      },
      'Region: OECD90': {
        'Ambitious Cases': {
          'ITDP - UC Davis (2015)  A Global High Shift Cycling Scenario Updated Report Data - High shift': THISDIR.joinpath('tam', 'tam_ITDP_UC_Davis_2015_A_Global_High_Shift_Cycling_Scenario_Updated_Report_Data_High_shift.csv'),
        },
      },
      'Region: Eastern Europe': {
        'Ambitious Cases': {
          'ITDP - UC Davis (2015)  A Global High Shift Cycling Scenario Updated Report Data - High shift': THISDIR.joinpath('tam', 'tam_ITDP_UC_Davis_2015_A_Global_High_Shift_Cycling_Scenario_Updated_Report_Data_High_shift.csv'),
        },
      },
      'Region: Asia (Sans Japan)': {
        'Ambitious Cases': {
          'ITDP - UC Davis (2015)  A Global High Shift Cycling Scenario Updated Report Data - High shift': THISDIR.joinpath('tam', 'tam_ITDP_UC_Davis_2015_A_Global_High_Shift_Cycling_Scenario_Updated_Report_Data_High_shift.csv'),
        },
      },
      'Region: Middle East and Africa': {
        'Ambitious Cases': {
          'ITDP - UC Davis (2015)  A Global High Shift Cycling Scenario Updated Report Data - High shift': THISDIR.joinpath('tam', 'tam_ITDP_UC_Davis_2015_A_Global_High_Shift_Cycling_Scenario_Updated_Report_Data_High_shift.csv'),
        },
      },
      'Region: Latin America': {
        'Ambitious Cases': {
          'ITDP - UC Davis (2015)  A Global High Shift Cycling Scenario Updated Report Data - High shift': THISDIR.joinpath('tam', 'tam_ITDP_UC_Davis_2015_A_Global_High_Shift_Cycling_Scenario_Updated_Report_Data_High_shift.csv'),
        },
      },
    }
    self.tm = tam.TAM(tamconfig=tamconfig, tam_ref_data_sources=tam_ref_data_sources,
      tam_pds_data_sources=tam_ref_data_sources)
    ref_tam_per_region=self.tm.ref_tam_per_region()
    pds_tam_per_region=self.tm.pds_tam_per_region()

    # Custom PDS Data
    ca_pds_data_sources = [
      {'name': 'Drawdown Book Edition 1 Scenario 1', 'include': True,
          'filename': THISDIR.joinpath('ca_pds_data', 'custom_pds_ad_Drawdown_Book_Edition_1_Scenario_1.csv')},
      {'name': 'Drawdown Book Edition 1 Scenario 2', 'include': True,
          'filename': THISDIR.joinpath('ca_pds_data', 'custom_pds_ad_Drawdown_Book_Edition_1_Scenario_2.csv')},
    ]
    self.pds_ca = customadoption.CustomAdoption(data_sources=ca_pds_data_sources,
        soln_adoption_custom_name=self.ac.soln_pds_adoption_custom_name,
        high_sd_mult=1.0, low_sd_mult=1.0,
        total_adoption_limit=pds_tam_per_region)

    # Custom REF Data
    ca_ref_data_sources = [
      {'name': 'Custom REF Adoption - Fixed Mass Transit Pass-km Annually', 'include': False,
          'filename': THISDIR.joinpath('ca_ref_data', 'custom_ref_ad_Custom_REF_Adoption_Fixed_Mass_Transit_Passkm_Annually.csv')},
      {'name': 'Adoption Based on IEA 6DS', 'include': False,
          'filename': THISDIR.joinpath('ca_ref_data', 'custom_ref_ad_Adoption_based_on_IEA_6DS.csv')},
    ]
    self.ref_ca = customadoption.CustomAdoption(data_sources=ca_ref_data_sources,
        soln_adoption_custom_name=self.ac.soln_ref_adoption_custom_name,
        high_sd_mult=1.0, low_sd_mult=1.0,
        total_adoption_limit=ref_tam_per_region)

    ref_adoption_data_per_region = self.ref_ca.adoption_data_per_region()

    if False:
      # One may wonder why this is here. This file was code generated.
      # This 'if False' allows subsequent conditions to all be elif.
      pass
    elif self.ac.soln_pds_adoption_basis == 'Fully Customized PDS':
      pds_adoption_data_per_region = self.pds_ca.adoption_data_per_region()
      pds_adoption_trend_per_region = self.pds_ca.adoption_trend_per_region()
      pds_adoption_is_single_source = None
    elif self.ac.soln_pds_adoption_basis == 'Linear':
      pds_adoption_data_per_region = None
      pds_adoption_trend_per_region = None
      pds_adoption_is_single_source = None

    ht_ref_adoption_initial = pd.Series(
      [9607070620938.643, 2177533057697.923, 575975431282.0925, 4506889445113.769, 1416146219920.7346,
       1334877448730.5225, 0.0, 0.0, 0.0, 0.0],
       index=dd.REGIONS)
    ht_ref_adoption_final = ref_tam_per_region.loc[2050] * (ht_ref_adoption_initial / ref_tam_per_region.loc[2014])
    ht_ref_datapoints = pd.DataFrame(columns=dd.REGIONS)
    ht_ref_datapoints.loc[2014] = ht_ref_adoption_initial
    ht_ref_datapoints.loc[2050] = ht_ref_adoption_final.fillna(0.0)
    ht_pds_adoption_initial = ht_ref_adoption_initial
    ht_regions, ht_percentages = zip(*self.ac.pds_adoption_final_percentage)
    ht_pds_adoption_final_percentage = pd.Series(list(ht_percentages), index=list(ht_regions))
    ht_pds_adoption_final = ht_pds_adoption_final_percentage * pds_tam_per_region.loc[2050]
    ht_pds_datapoints = pd.DataFrame(columns=dd.REGIONS)
    ht_pds_datapoints.loc[2014] = ht_pds_adoption_initial
    ht_pds_datapoints.loc[2050] = ht_pds_adoption_final.fillna(0.0)
    self.ht = helpertables.HelperTables(ac=self.ac,
        ref_datapoints=ht_ref_datapoints, pds_datapoints=ht_pds_datapoints,
        pds_adoption_data_per_region=pds_adoption_data_per_region,
        ref_adoption_limits=ref_tam_per_region, pds_adoption_limits=pds_tam_per_region,
        ref_adoption_data_per_region=ref_adoption_data_per_region,
        pds_adoption_trend_per_region=pds_adoption_trend_per_region,
        pds_adoption_is_single_source=pds_adoption_is_single_source)

    self.ef = emissionsfactors.ElectricityGenOnGrid(ac=self.ac)

    self.ua = unitadoption.UnitAdoption(ac=self.ac,
        ref_total_adoption_units=ref_tam_per_region, pds_total_adoption_units=pds_tam_per_region,
        soln_ref_funits_adopted=self.ht.soln_ref_funits_adopted(),
        soln_pds_funits_adopted=self.ht.soln_pds_funits_adopted(),
        bug_cfunits_double_count=True)
    soln_pds_tot_iunits_reqd = self.ua.soln_pds_tot_iunits_reqd()
    soln_ref_tot_iunits_reqd = self.ua.soln_ref_tot_iunits_reqd()
    conv_ref_tot_iunits = self.ua.conv_ref_tot_iunits()
    soln_net_annual_funits_adopted=self.ua.soln_net_annual_funits_adopted()

    self.fc = firstcost.FirstCost(ac=self.ac, pds_learning_increase_mult=2,
        ref_learning_increase_mult=2, conv_learning_increase_mult=2,
        soln_pds_tot_iunits_reqd=soln_pds_tot_iunits_reqd,
        soln_ref_tot_iunits_reqd=soln_ref_tot_iunits_reqd,
        conv_ref_tot_iunits=conv_ref_tot_iunits,
        soln_pds_new_iunits_reqd=self.ua.soln_pds_new_iunits_reqd(),
        soln_ref_new_iunits_reqd=self.ua.soln_ref_new_iunits_reqd(),
        conv_ref_new_iunits=self.ua.conv_ref_new_iunits(),
        fc_convert_iunit_factor=1.0)

    self.oc = operatingcost.OperatingCost(ac=self.ac,
        soln_net_annual_funits_adopted=soln_net_annual_funits_adopted,
        soln_pds_tot_iunits_reqd=soln_pds_tot_iunits_reqd,
        soln_ref_tot_iunits_reqd=soln_ref_tot_iunits_reqd,
        conv_ref_annual_tot_iunits=self.ua.conv_ref_annual_tot_iunits(),
        soln_pds_annual_world_first_cost=self.fc.soln_pds_annual_world_first_cost(),
        soln_ref_annual_world_first_cost=self.fc.soln_ref_annual_world_first_cost(),
        conv_ref_annual_world_first_cost=self.fc.conv_ref_annual_world_first_cost(),
        single_iunit_purchase_year=2017,
        soln_pds_install_cost_per_iunit=self.fc.soln_pds_install_cost_per_iunit(),
        conv_ref_install_cost_per_iunit=self.fc.conv_ref_install_cost_per_iunit(),
        conversion_factor=1.0)

    self.c4 = ch4calcs.CH4Calcs(ac=self.ac,
        soln_net_annual_funits_adopted=soln_net_annual_funits_adopted)

    self.c2 = co2calcs.CO2Calcs(ac=self.ac,
        ch4_ppb_calculator=self.c4.ch4_ppb_calculator(),
        soln_pds_net_grid_electricity_units_saved=self.ua.soln_pds_net_grid_electricity_units_saved(),
        soln_pds_net_grid_electricity_units_used=self.ua.soln_pds_net_grid_electricity_units_used(),
        soln_pds_direct_co2_emissions_saved=self.ua.soln_pds_direct_co2_emissions_saved(),
        soln_pds_direct_ch4_co2_emissions_saved=self.ua.soln_pds_direct_ch4_co2_emissions_saved(),
        soln_pds_direct_n2o_co2_emissions_saved=self.ua.soln_pds_direct_n2o_co2_emissions_saved(),
        soln_pds_new_iunits_reqd=self.ua.soln_pds_new_iunits_reqd(),
        soln_ref_new_iunits_reqd=self.ua.soln_ref_new_iunits_reqd(),
        conv_ref_new_iunits=self.ua.conv_ref_new_iunits(),
        conv_ref_grid_CO2_per_KWh=self.ef.conv_ref_grid_CO2_per_KWh(),
        conv_ref_grid_CO2eq_per_KWh=self.ef.conv_ref_grid_CO2eq_per_KWh(),
        soln_net_annual_funits_adopted=soln_net_annual_funits_adopted,
        fuel_in_liters=False)

    self.r2s = rrs.RRS(total_energy_demand=ref_tam_per_region.loc[2014, 'World'],
        soln_avg_annual_use=self.ac.soln_avg_annual_use,
        conv_avg_annual_use=self.ac.conv_avg_annual_use)

