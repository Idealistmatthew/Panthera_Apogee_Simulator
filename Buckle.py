import os
os.system('cls' if os.name == 'nt' else 'clear')
import json
with open('tanks_specifications.json') as f:
   data = json.load(f)

import numpy as np

fuel=data['fuel']
oxidiser=data['oxidiser']
material=data['material']
other=data['other']
def buckle(type, p_int, g=9.81, a=other['a'], k=other['k']):
    area=np.pi*a**2
    youngs=material['youngs']
    end_thickness=type['end_thickness']
    material_mass=type['end_cap_mass']+type['cylinder_mass'];
    total_weight=type['total_mass']*g;
    #max pressure is the axial load due ot the mass of the rocket
    p_ext=total_weight/area;

    # buckling constat is within the range 0.05 to 0.10
    buckling_constant=0.10;
    critical_pressure_cause_buckling=0.342*youngs*end_thickness**2/a**2;
    critical_pressure_cause_buckling=(buckling_constant*2*youngs*end_thickness**2)/(a*k)**2;

    #Critical shear stress at atmospheric pressure
    stress_crit_atm=(9*(type['cylindrical_tank_thickness']/a)**1.6+0.16*(type['cylindrical_tank_thickness']/type['tank_length'])**1.3)*youngs
    var1=p_ext-stress_crit_atm
    var2=p_ext-p_int-critical_pressure_cause_buckling
    print("%s%s%s" % ('stress_crit_atm = ', stress_crit_atm*10**(-5), ' bar'));
    print("%s%s%s" % ('critical_pressure_cause_buckling = ', critical_pressure_cause_buckling*10**(-5), ' bar'));
    print("%s%s%s" % ('p_ext = ', p_ext*10**(-5), ' bar'));
    if( var1 > 0 or var2 > 0):
       print('Buckle alert')
       if(var1<var2):
            p_int_req=var2
       else:
            p_int_req=var1
       print("%s%s%s" % ('Internal pressure required=',p_int_req, ' Pa'))
    else:
       print('No buckle')

buckle(fuel, 1e5)
buckle(oxidiser, -1000000000e5)


