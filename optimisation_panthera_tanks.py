from numpy.core.function_base import linspace
from rocketpy import Environment, SolidMotor, Rocket, Flight
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
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
    ## some lines of code to calculate the grain height and other properties that change with propellant mass
    grainmass = propellantmass/2
    density = (3.5*975.2 + 788.75)/4.5
    grainvolume = grainmass/density
    grainradius = 0.3
    grainheight = float(grainvolume/(np.pi*(grainradius**2)))
    burnOuttime = float(propellantmass/150*30)
    drymass = float(50 + 50*(propellantmass/150))

    WhiteGiant = SolidMotor(
        thrustSource= 10000,
        burnOut = burnOuttime,
        grainNumber = 2,
        grainSeparation = 0.2,
        grainDensity = (3.5*975.2 + 788.75)/4.5, # mass ratio was used to calculate the grain density average)
        grainOuterRadius = 0.3, # Not sure what White Giant's Outer Radius is (only have CAD for white dwarf), calculated to ensure propellant mass is 150kg
        grainInitialInnerRadius = 0,
        grainInitialHeight = grainheight, # Not sure what White Giant's Initial Height is either (paired with radius to ensure propellant mass is 150kg using ullage volume)
        nozzleRadius = 200/1000, # Not sure about this either
        throatRadius = 100/1000, # not sure about this either
        interpolationMethod = "linear"
    )

    # WhiteGiant.info()

    Panthera = Rocket(
        motor = WhiteGiant,
        radius = 0.3, # increase a bit off the tank radius
        mass = drymass, # I included the wet mass of Aquila in this (meant to be total dry mass of rocket)
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
    return -TestFlight.apogee

mass = np.linspace(60,200,num = 100)
apogee_list = []
for i in mass:
    apogee_list.append(-apogee_fromvariedtankMass(i))

plt.plot(mass, apogee_list)
plt.xlabel("Propellant Mass (kg)")
plt.ylabel("Apogee (m)")
plt.show()





# res = optimize.minimize(apogee_fromvariedtankMass, 150)
# print(res.x)
# import time
# start = time.time()
# print(apogee_fromvariedtankMass(155))
# end = time.time()
# print(f"Runtime of the program is {end-start}")