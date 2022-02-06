from numpy.core.function_base import linspace
from rocketpy import Environment, SolidMotor, Rocket, Flight
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from Tanks_dimensions import tank_dimensions, fuel_oxidiser_mass_volume
# Setting up the environment
Env = Environment(
    railLength=18,
    latitude=32.990254,
    longitude=-106.974998,
    elevation=1400
)

# import datetime
# tomorrow = datetime.date.today() + datetime.timedelta(days=1)
# Env.setDate((tomorrow.year, tomorrow.month, tomorrow.day, 12))
# Env.setAtmosphericModel(type='Forecast', file='GFS')
# Env.info()

tank_data = {
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

material=tank_data['material']
fuel = tank_data['fuel']
oxidiser = tank_data['oxidiser']

fuel_density = 841.9
oxidiser_density = 970
mixture_ratio = 0.9

def apogee_fromvariedtankMass(propellantmass):
    """
    Function that returns the maximum apogee values based on the mass input


    Parameters
    ----------
    propellantmass : int, float
    mass of propellant on Panthera

    Returns
    -------

    """

    #Calculating propellant tank size and mass (estimate of tank drymass) based on propellant mass
    (fuel_length, fuel_mass, oxidiser_length, oxidiser_mass) = fuel_oxidiser_mass_volume(propellantmass, fuel_density, oxidiser_density, mixture_ratio, fuel, oxidiser)

    ## some lines of code to calculate the grain height and other properties that change with propellant mass
    grainmass = propellantmass/2
    density = (3.5*975.2 + 788.75)/4.5
    grainvolume = grainmass/density
    grainradius = 0.15
    grainheight = float(grainvolume/(np.pi*(grainradius**2)))
    burnOuttime = float(propellantmass/150*30)

    #Welding efficiency, 0.65-1.00
    e=1; # In this case if it is the knuckle to crown, no weld than 1, if any weld than change it.

    # k is tank ellipse ratio b/a, where b is y axis radius a is x-axis radius. k=1 when spherical
    k=tank_data['other']['k'];#(k>=1)

    safe_stress=material['yield_stress']/1.33; # Condition under personnel

    if (material['ultimate_stress']/1.65<safe_stress):
        safe_stress=material['ultimate_stress']/1.65

    (fuel_cylindrical_tank_thickness, fuel_cylinder_mass, fuel_end_thickness, fuel_end_cap_mass, fuel_total_mass) = tank_dimensions(safe_stress, material['max_delta_p'], fuel, k, e)
    (oxidiser_cylindrical_tank_thickness, oxidiser_cylinder_mass, oxidiser_end_thickness, oxidiser_end_cap_mass, oxidiser_total_mass) = tank_dimensions(safe_stress, material['max_delta_p'], oxidiser, k, e)

    tank_drymass = oxidiser_cylinder_mass + oxidiser_end_cap_mass + fuel_cylinder_mass + fuel_end_cap_mass

    WhiteGiant = SolidMotor(
        thrustSource= 10000,
        burnOut = burnOuttime,
        grainNumber = 2,
        grainSeparation = 0.2,
        grainDensity = (3.5*975.2 + 788.75)/4.5, # mass ratio was used to calculate the grain density average)
        grainOuterRadius = 0.15, # Not sure what White Giant's Outer Radius is (only have CAD for white dwarf), calculated to ensure propellant mass is 150kg
        grainInitialInnerRadius = 0,
        grainInitialHeight = grainheight, # Not sure what White Giant's Initial Height is either (paired with radius to ensure propellant mass is 150kg using ullage volume)
        nozzleRadius = 200/1000, # Not sure about this either
        throatRadius = 100/1000, # not sure about this either
        interpolationMethod = "linear"
    )

    # WhiteGiant.info()

    Panthera = Rocket(
        motor = WhiteGiant,
        radius = grainradius, # increase a bit off the tank radius
        mass = float(tank_drymass) + 78.05, # I included the wet mass of Aquila in this (meant to be total dry mass of rocket)
        inertiaI = 6.60, # arbitrary number
        inertiaZ = 0.0351, # arbitrary number
        distanceRocketNozzle = -3.8, # arbitrary number
        distanceRocketPropellant = -0.085704, # arbitraty number
        powerOffDrag = 0.5,
        powerOnDrag = 0.5,
    )

    Panthera.setRailButtons([0,18])

    #arbitrary aeros surfaces
    NoseCone = Panthera.addNose(length=0.40, kind="vonKarman", distanceToCM=3.8)

    FinSet = Panthera.addFins(4, span=0.325, rootChord=0.4, tipChord=0.2, distanceToCM=-1.400)

    Tail = Panthera.addTail(topRadius=0.15 , bottomRadius =0.65 ,length=1, distanceToCM=-3.8)

    # def drogueTrigger(p, y):
    #     # p = pressure
    #     # y = [x, y, z, vx, vy, vz, e0, e1, e2, e3, w1, w2, w3]
    #     # activate drogue when vz < 0 m/s.
    #     return True if y[5] < 0 else False

    # def mainTrigger(p, y):
    #     # p = pressure
    #     # y = [x, y, z, vx, vy, vz, e0, e1, e2, e3, w1, w2, w3]
    #     # activate main when vz < 0 m/s and z < 800 m.
    #     return True if y[5] < 0 and y[2] < 800 else False

    # Main = Panthera.addParachute('Main',
    #                             CdS=10.0,
    #                             trigger=mainTrigger,
    #                             samplingRate=105,
    #                             lag=1.5,
    #                             noise=(0, 8.3, 0.5))

    # Drogue = Panthera.addParachute('Drogue',
    #                               CdS=1.0,
    #                               trigger=drogueTrigger,
    #                               samplingRate=105,
    #                               lag=1.5,
    #                               noise=(0, 8.3, 0.5))

    TestFlight = Flight(rocket=Panthera, environment=Env, inclination=90, heading=0)
    return TestFlight.apogee

mass = np.linspace(60,1000, num = 100)
apogee_list = []
for i in mass:
    apogee_list.append(apogee_fromvariedtankMass(i))

plt.plot(mass, apogee_list)
plt.xlabel("Propellant Mass (kg)")
plt.ylabel("Apogee (m)")
plt.show()

#For the convenience of the tanks dimensions calculation
apogee_to_mass_func=np.polyfit(mass, apogee_list, 2)
print(apogee_to_mass_func)


# res = optimize.minimize(apogee_fromvariedtankMass, 150)
# print(res.x)
# import time
# start = time.time()
# print(apogee_fromvariedtankMass(155))
# end = time.time()
# print(f"Runtime of the program is {end-start}")