from rocketpy import Environment, SolidMotor, Rocket, Flight
# Setting up the environment
Env = Environment(
    railLength=5.2,
    latitude=32.990254,
    longitude=-106.974998,
    elevation=1400
)

import datetime
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
Env.setDate((tomorrow.year, tomorrow.month, tomorrow.day, 12))
Env.setAtmosphericModel(type='Forecast', file='GFS')
Env.info()

WhiteGiant = SolidMotor(
    thrustSource= 10000,
    burnOut = 30,
    grainNumber = 2,
    grainSeparation = 0,
    grainDensity = (3.5*975.2 + 788.75)/4.5, # mass ratio was used to calculate the grain density average)
    grainOuterRadius = 0.03, # Not sure what White Giant's Outer Radius is (only have CAD for white dwarf), calculated to ensure propellant mass is 150kg
    grainInitialInnerRadius = 0,
    grainInitialHeight = 0.626, # Not sure what White Giant's Initial Height is either (paired with radius to ensure propellant mass is 150kg using ullage volume)
    nozzleRadius = 33/1000, # Not sure about this either
    throatRadius = 11/1000, # not sure about this either
    interpolationMethod = "linear"
)

WhiteGiant.info()

Panthera = Rocket(
    motor = WhiteGiant,
    radius = 0.05, # increase a bit off the tank radius
    mass = 60, # I included the wet mass of Aquila in this
    inertiaI = 6.60, # arbitrary number
    inertiaZ = 0.0351, # arbitrary number
    distanceRocketNozzle = -1.255, # arbitrary number
    distanceRocketPropellant = -0.085704, # arbitraty number
    powerOffDrag = 0.5, 
    powerOnDrag = 0.5, 
)

Panthera.setRailButtons([0.2,-0.5])

#arbitrary aeros surfaces
NoseCone = Panthera.addNose(length=0.55829, kind="vonKarman", distanceToCM=0.71971)

FinSet = Panthera.addFins(4, span=0.100, rootChord=0.120, tipChord=0.040, distanceToCM=-1.04956)

Tail = Panthera.addTail(topRadius=0.0635, bottomRadius=0.0435, length=0.060, distanceToCM=-1.194656)

def drogueTrigger(p, y):
    # p = pressure
    # y = [x, y, z, vx, vy, vz, e0, e1, e2, e3, w1, w2, w3]
    # activate drogue when vz < 0 m/s.
    return True if y[5] < 0 else False

def mainTrigger(p, y):
    # p = pressure
    # y = [x, y, z, vx, vy, vz, e0, e1, e2, e3, w1, w2, w3]
    # activate main when vz < 0 m/s and z < 800 m.
    return True if y[5] < 0 and y[2] < 800 else False

Main = Panthera.addParachute('Main',
                            CdS=10.0,
                            trigger=mainTrigger,
                            samplingRate=105,
                            lag=1.5,
                            noise=(0, 8.3, 0.5))

Drogue = Panthera.addParachute('Drogue',
                              CdS=1.0,
                              trigger=drogueTrigger,
                              samplingRate=105,
                              lag=1.5,
                              noise=(0, 8.3, 0.5))

TestFlight = Flight(rocket=Panthera, environment=Env, inclination=85, heading=0)
TestFlight.allInfo()