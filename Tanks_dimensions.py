#Need to find thickness of cylindrical, end (spherical, assumed)
#Main variable is type of material, welding efficency, total fuel required, operating temperature and pressure.
import os
os.system('cls' if os.name == 'nt' else 'clear')

import numpy as np
import matplotlib.pyplot as plt
#Fuel Tank material is Al5051

dict = {
    "fuel":{
        "density":841.9,
        'compressive_elasticity':1e6,# Undetermined, need to do experiment measurement itself
        'flow_rate':0.001,
        'acoustic_c':2000,# Undetermined
    },
    "oxidiser":{
        "density":1001.2, # estimate from https://www.researchgate.net/figure/Thermodynamic-properties-of-liquid-nitrous-oxide-N2O_fig1_332489740
        'compressive_elasticity':1e6,# Undetermined, need to do experiment measurement itself
        'flow_rate':0.009,
        'acoustic_c':2000,# Undetermined
    },
    "material":{
        'youngs':68e9,
        'poissons':0.33,
        'material_density':2700,
        'yield_stress': 56e6,
        'ultimate_stress':170e6,
        #Pressure, max pressure=35 bar. Operating pressure=25 bar. In bar
        'max_delta_p':20e5,
    },
    "other":{
        'a':0.15,
        'k':1,
    },
}
material=dict['material']
fuel=dict['fuel']
oxidiser=dict['oxidiser']
# def total_propellent_mass(apogee):
#     from optimisation_panthera_tanks import apogee_to_mass_func
#     apogee_to_mass_func[2]=apogee_to_mass_func[2]-apogee
#     propellor_mass=np.roots(apogee_to_mass_func)
#     total_mass=propellor_mass[1]
#     expulsion_efficiency=0.97
#     total_mass=total_mass/expulsion_efficiency
#     return total_mass
def total_propellent_mass(apogee):
    # apogee_to_mass_func=[3.63785875e-01,1.97877764e+01,4.10204164e+03]
    apogee_to_mass_func=[3.92368513e-02, 6.00200261e+01, 1.47627269e+03]
    apogee_to_mass_func[2]=apogee_to_mass_func[2]-apogee
    propellor_mass=np.roots(apogee_to_mass_func)
    total_mass=propellor_mass[1]
    expulsion_efficiency=0.97
    total_mass=total_mass/expulsion_efficiency
    return total_mass

def fuel_oxidiser_mass_volume(total_mass,fuel_density,oxidiser_density,mixture_ratio,fuel_coef=1, oxidiser_coef=9,a=15e-2,g=9.81,ullage=1.05, mol_mass_fuel=60e-3, mol_mass_oxidiser=44e-3, realistic=0):
    # assume the propellent mass is entirely dependent on coefficient
    if(mixture_ratio<1):
        # if propellent mass already include maxture_ratio
        # fuel_mass=total_mass*(fuel_coef*mol_mass_fuel)/(oxidiser_coef/mixture_ratio*mol_mass_oxidiser+fuel_coef*mol_mass_fuel)
        # oxidiser_mass=total_mass*(oxidiser_coef/mixture_ratio*mol_mass_oxidiser)/(oxidiser_coef/mixture_ratio*mol_mass_oxidiser+fuel_coef*mol_mass_fuel)
        fuel_mass=total_mass*(fuel_coef*mol_mass_fuel)/(oxidiser_coef*mol_mass_oxidiser+fuel_coef*mol_mass_fuel)
        oxidiser_mass=(total_mass*(oxidiser_coef*mol_mass_oxidiser)/(oxidiser_coef*mol_mass_oxidiser+fuel_coef*mol_mass_fuel))/mixture_ratio
    else:
        fuel_mass=total_mass*(fuel_coef*mol_mass_fuel)/(oxidiser_coef*mol_mass_oxidiser+fuel_coef*mol_mass_fuel)*mixture_ratio
        oxidiser_mass=total_mass*(oxidiser_coef*mol_mass_oxidiser)/(oxidiser_coef*mol_mass_oxidiser+fuel_coef*mol_mass_fuel)

    fuel_volume=fuel_mass/fuel_density
    actual_fuel_volume=fuel_volume*ullage
    # This is the cruder estimate, if account for end caps then...
    fuel_length=actual_fuel_volume/area
    oxidiser_volume=oxidiser_mass/oxidiser_density
    actual_oxidiser_volume=oxidiser_volume*ullage
    oxidiser_length=actual_oxidiser_volume/area
    fuel['tank_length']=fuel_length
    fuel['liq_volume']=fuel_volume
    fuel['liq_mass']=fuel_mass
    oxidiser['tank_length']=oxidiser_length
    oxidiser['liq_mass']=oxidiser_mass
    oxidiser['liq_volume']=oxidiser_volume

def tank_dimensions(safe_stress, max_delta_p, type, k, a=15e-2, g=9.81):
    #K stress factor; accounting for local bending stress and discontinuity stress at the combination point.
    K=0.161905*k**2-0.0669*k+0.577708;#obtained via interpolation in excel. very crude estimate
    #Design factor, only used when considering ellipsoidal
    if(k==1):
        design_factor=4;
    else:
        design_factor=2*k+1/np.sqrt(k**2-1)*np.log((k+np.sqrt(k**2-1))/(k-np.sqrt(k**2-1)));

    #Current design, k=1
    cylindrical_tank_thickness=max_delta_p*a/(safe_stress*e)
    cylindrical_thickness_near_weld=cylindrical_tank_thickness*1.4 # accounts for bending moments, strength of weld, etc.
    end_thickness=max_delta_p*a*(K+1/2)/(2*safe_stress)

    #Optional, ellipsoidal
    if(k!=1):
        knuckle_wall_thickness=cylindrical_tank_thickness*K
        crown_end_thickness=cylindrical_tank_thickness*k*a # thickness of the tip of the end.
        type['knuckle_wall_thickness']=knuckle_wall_thickness
        type['crown_end_thickness']=crown_end_thickness
        end_thickness=(K+k/2)/2*cylindrical_tank_thickness
    end_cap_volume=np.pi*a**2*end_thickness*design_factor/(2*k)
    end_cap_mass=end_cap_volume*material['material_density']

    cylinder_volume=2*np.pi*a*type['tank_length']*cylindrical_tank_thickness
    cylinder_mass=cylinder_volume*material['material_density']

    material_mass=end_cap_mass+cylinder_mass;
    total_mass=material_mass+type["liq_mass"];
    #max pressure is the axial load due ot the mass of the rocket
    p_ext=total_mass*g/area;
    type['cylindrical_tank_thickness']=cylindrical_tank_thickness
    type['cylinder_mass']=cylinder_mass
    type['end_thickness']=end_thickness
    type['end_cap_mass']=end_cap_mass
    type['dry_mass']=material_mass
    type['total_mass']=total_mass
    type['end_cap_volume']=end_cap_volume
    type['total_material_volume']=cylinder_volume+end_cap_volume
    type['total_tank_volume']=type['liq_volume']+cylinder_volume+end_cap_volume
a=dict['other']['a']
area=np.pi*a**2
#estimate fuel mass required from the apogee
apogee=140000
# We have to test out fuel oxidiser ratio
mixture_ratio=0.9 # estimate, ratio in moles
# Reaction: C2H7OH + 9N2O -> 9N2 + 3CO2 + 4H2O

total_mass=total_propellent_mass(apogee)
fuel_oxidiser_mass_volume(total_mass,fuel['density'],oxidiser['density'],mixture_ratio)

#Welding efficiency, 0.65-1.00
e=1; # In this case if it is the knuckle to crown, no weld than 1, if any weld than change it.

# k is tank ellipse ratio b/a, where b is y axis radius a is x-axis radius. k=1 when spherical
k=dict['other']['k'];#(k>=1)

safe_stress=material['yield_stress']/1.33; # Condition under personnel

if (material['ultimate_stress']/1.65<safe_stress):
    safe_stress=material['ultimate_stress']/1.65
tank_dimensions(safe_stress, material['max_delta_p'], fuel, k)
tank_dimensions(safe_stress, material['max_delta_p'], oxidiser, k)
print('fuel')
for x in fuel:
    print(x,':',fuel[x])
print('\noxidiser')
for x in oxidiser:
    print(x,':',oxidiser[x])

dry_mass=fuel['dry_mass']+oxidiser['dry_mass']
print("Total dry mass=%s" % (dry_mass))
import json

with open('tanks_specifications.json', 'w')as fp:
    json.dump(dict, fp)
base_height=2
Total_height=fuel['tank_length']+oxidiser['tank_length']+2*a*k+base_height
print(Total_height)
print('Top fuel bottom oxidiser')
c_o_m_1=((fuel['liq_mass']+fuel['cylinder_mass'])*(fuel['tank_length']/2+oxidiser['tank_length']+a*k)+fuel['end_cap_mass']*(a*k/6+fuel['tank_length']+oxidiser['tank_length']+a*k)+(oxidiser['liq_mass']+oxidiser['cylinder_mass'])*(oxidiser['tank_length']/2+a*k)+oxidiser['end_cap_mass']*(oxidiser['tank_length']+oxidiser['tank_length']+a*k/6))/(fuel['total_mass']+oxidiser['total_mass'])+base_height
print("COM is %s" % (c_o_m_1))
print('Top oxidiser bottom fuel')
c_o_m_2=((oxidiser['liq_mass']+oxidiser['cylinder_mass'])*(oxidiser['tank_length']/2+fuel['tank_length']+a*k)+oxidiser['end_cap_mass']*(a*k/6+oxidiser['tank_length']+fuel['tank_length']+a*k)+(fuel['liq_mass']+fuel['cylinder_mass'])*(fuel['tank_length']/2+a*k)+fuel['end_cap_mass']*(fuel['tank_length']+fuel['tank_length']+a*k/6))/(oxidiser['total_mass']+fuel['total_mass'])+base_height
print("COM is %s" % (c_o_m_2))

# fuel_total_mass=[]
# fuel_total_volume=[]
# max_pressure=[]
# k_list = np.linspace(2, 1, 100, endpoint=False)[::-1]
# p_int=1e5 #atmospheric pressure

# youngs=material['youngs']
# k=1
# tank_dimensions(safe_stress, material['max_delta_p'], fuel, k)
# fuel_total_mass.append(fuel['total_mass'])
# buckling_constant=0.10;
# fuel_total_volume.append(fuel['total_tank_volume'])
# critical_pressure_cause_buckling=(buckling_constant*2*youngs*fuel['end_thickness']**2)/((a*k)**2)
# max_pressure.append(critical_pressure_cause_buckling)

# for k in k_list:
#     tank_dimensions(safe_stress, material['max_delta_p'], fuel, k)
#     fuel_total_mass.append(fuel['total_mass'])
#     fuel_total_volume.append(fuel['total_tank_volume'])
#     critical_pressure_cause_buckling=(buckling_constant*2*youngs*fuel['end_thickness']**2)/((a*k)**2)
#     max_pressure.append(critical_pressure_cause_buckling)

# k_list=np.insert(k_list,0,1)
# plot1 = plt.figure(1)
# plt.plot(k_list, fuel_total_mass)
# plt.xlabel("eccentricity")
# plt.ylabel("total_mass")

# plot2 = plt.figure(2)
# plt.plot(k_list, fuel_total_volume)
# plt.xlabel("eccentricity")
# plt.ylabel("total_volume")

# plot3 = plt.figure(3)
# plt.plot(k_list, max_pressure)
# plt.xlabel("eccentricity")
# plt.ylabel("max_pressure")
# plt.show()

