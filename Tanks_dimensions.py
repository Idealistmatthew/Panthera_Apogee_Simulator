#Need to find thickness of cylindrical, end (spherical, assumed)
#Main variable is type of material, welding efficency, total fuel required, operating temperature and pressure.
import os
os.system('cls' if os.name == 'nt' else 'clear')

import numpy as np
#Fuel Tank material is Al5051

dict = {
    "fuel":{},
    "oxidiser":{},
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
def total_propellent_mass(apogee):
    from optimisation_panthera_tanks import apogee_to_mass_func
    apogee_to_mass_func[2]=apogee_to_mass_func[2]-apogee
    propellor_mass=np.roots(apogee_to_mass_func)
    total_mass=propellor_mass[1]
    return total_mass

def fuel_oxidiser_mass_volume(total_mass,fuel_density,oxidiser_density,mixture_ratio,fuel_coef=1, oxidiser_coef=9,a=15e-2,g=9.81,ullage=1.1, mol_mass_fuel=60e-3, mol_mass_oxidiser=44e-3):
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
    fuel_length=actual_fuel_volume/area
    oxidiser_volume=oxidiser_mass/oxidiser_density
    actual_oxidiser_volume=oxidiser_volume*ullage
    oxidiser_length=actual_oxidiser_volume/area
    fuel['tank_length']=fuel_length
    fuel['liq_mass']=fuel_mass
    oxidiser['tank_length']=oxidiser_length
    oxidiser['liq_mass']=oxidiser_mass


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
    type['total_mass']=total_mass

a=dict['other']['a']
area=np.pi*a**2
#Fuel
fuel_density=841.9; #kg/m3
#oxidiser
oxidiser_density=970; # estimate from https://www.researchgate.net/figure/Thermodynamic-properties-of-liquid-nitrous-oxide-N2O_fig1_332489740
#estimate fuel mass required from the apogee
apogee=10000
# We have to test out fuel oxidiser ratio
mixture_ratio=0.9 # estimate, raio in moles
# Reaction: C2H7OH + 9N2O -> 9N2 + 3CO2 + 4H2O

total_mass=total_propellent_mass(apogee)
fuel_oxidiser_mass_volume(total_mass,fuel_density,oxidiser_density,mixture_ratio)

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

import json

with open('tanks_specifications.json', 'w')as fp:
    json.dump(dict, fp)



# Cost
# coefficient of expansion, how big the gap.
# DUration of time and the total strain.
# Shifting of Center of Gravity
# Bending momenend_thickness due to transverse acceleration