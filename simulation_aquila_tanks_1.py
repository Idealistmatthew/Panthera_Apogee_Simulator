#Importing the relevant modules

from rocketpy import Environment, SolidMotor, Rocket, Flight
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

#Setting up the environment, including a default value of 9.8 for g

Env = Environment(
    railLength=18,
    latitude=35.4,
    longitude=-117.8,
    elevation=621 #elevation above sea level, m
)

#Setting up parameters for White Giant liquid engine
drag_data = np.genfromtxt("Drag_Data/CD Test.csv", delimiter = ",")


#Setting propellant mass and burn time parameters
propellant_mass = 150 # Total mass of fuel and oxidiser, kg
thrust = 10000 # Thrust of White Giant, N
V_ex = 180*9.81 # Exhaust velocity, m/s
mdot = thrust/V_ex # Propellant mass flow rate, kg/s
t_burn = propellant_mass/mdot # Duration of Panthera burn, s

#Modelling the fuel and oxidiser as a solid with average density rho
fuel_density = 841.9 #Density of IPA and H20 mixture at 15C, from ic.gc.ca and NIST
oxidiser_density = 1001.2 #Density of N20 at -20C, from NIST
ullage = 0.05 #Fraction of total volume replaced by ullage

rho = ((fuel_density + 3.5 * oxidiser_density)/4.5)*(1-ullage) #Average density of propellant mix when modelled as a solid grain, including ullage volume, kg/m^3

# Configure Panthera tanks (assume a single cylinder, flat ends)
d_out = 0.3 # Outer diameter, m
t_wall = 0.003 # Tank wall thickness, m
rho_wall = 2800 # Density of tank material, kg/m^3
d_in = d_out - (2*t_wall) # Inner diameter, m
r_in = d_in/2
r_out = d_out/2

tank_volume = propellant_mass/rho # Req'd internal volume, m^3
tank_height = tank_volume/(np.pi*np.power(r_in, 2)) # Req'd tank height, m
material_volume = np.pi*t_wall*((d_out*tank_height)+(2*np.power(r_out, 2))) # Req'd tank material volume, m^3
tank_drymass = material_volume*rho_wall # Tank dry mass
dragOff = drag_data[1:1000, [0,3]]
dragOn = drag_data[1:1000,[0,4]]

print(tank_height)
#Creating a solidmotor object to represent the White Giant engine

WhiteGiant = SolidMotor(
    thrustSource = thrust,
    burnOut = t_burn,
    grainNumber = 1,
    grainOuterRadius = r_in,
    grainDensity = rho,
    grainInitialInnerRadius = 0,
    grainInitialHeight = tank_height,
    #nozzleRadius = 0.0736 # Estimate for 10 kN WG
    #throatRadius = 0.0498 # Estimate for 10 kN WG
)

#Creating a rocket object to simulate the rocket at launch, including the wet mass of aquila

Panthera = Rocket(
    motor = WhiteGiant,
    radius = r_in, #Assume same as tank outer radius
    mass = 65, #Using a total wet mass of launch, including aquila wet mass, of 270kg
    inertiaI = 6.60, # arbitrary number
    inertiaZ = 0.0351, # arbitrary number
    distanceRocketNozzle = -3.8, # arbitrary number
    distanceRocketPropellant = -0.085704, # arbitrary number
    powerOffDrag = dragOff, 
    powerOnDrag = dragOn, 
)

#Adding rail buttons
Panthera.setRailButtons([0,18])

#arbitrary aeros surfaces
NoseCone = Panthera.addNose(length=0.40, kind="vonKarman", distanceToCM=3.8)

FinSet = Panthera.addFins(4, span=0.325, rootChord=0.4, tipChord=0.2, distanceToCM=-1.400)

Tail = Panthera.addTail(topRadius=0.15 , bottomRadius =0.65 ,length=1, distanceToCM=-3.8)

#Creating a flight object to simulate the flight of the first stage
TestFlight = Flight(rocket=Panthera, 
environment=Env, 
inclination=90, 
heading=0, 
maxTime = t_burn
)

#Creating a model for the off-the-shelf motor for Aquila, the Cesaroni Pro90 N5800

# Pro98 data taken from Cesaroni, thrustcurve.org
N5800_propmass = 9.021 # Total grain mass, kg
N5800_portdia = 0.0254 # Estimate of port diameter from Pro98 technical drawings, m
N5800_graindia = 0.090 # Estimate of grain outer diameter, m
N5800_grainlen = 1.12/6 # Estimate of individual grain length, m
N5800_density = N5800_propmass/((np.power(N5800_graindia, 2)-np.power(N5800_portdia, 2))*N5800_grainlen*6*np.pi/4)

N5800 = SolidMotor(
    thrustSource = r"Motors\Cesaroni_20146N5800-P.eng",
    burnOut = 3.49,
    grainNumber = 6,
    grainSeparation=0.001,
    grainOuterRadius = N5800_graindia/2,
    grainDensity = N5800_density,
    grainInitialInnerRadius = N5800_portdia/2,
    grainInitialHeight = N5800_grainlen,
    interpolationMethod="linear"
)

#Creating the aquila rocket model
Aquila = Rocket(
    motor = N5800,
    radius = 0.12/2,
    mass = 35 - N5800_propmass,
    inertiaI = 26.3, # Estimate from OR
    inertiaZ = 0.3, # Estimate from OR
    distanceRocketNozzle = -0.4, # Estimate from RASAero
    distanceRocketPropellant = 0.15, # Estimate from RASAero
    powerOffDrag = dragOff, 
    powerOnDrag = dragOn
)

Aquila.setRailButtons([-0.2, 0.6])
Nose = Aquila.addNose(length=0.6, kind="vonKarman", distanceToCM=1.0)
Fins = Aquila.addFins(4, span=0.12, rootChord=0.21, tipChord=0.13, distanceToCM=-0.3)

#Creating a flight object for the second stage (Aquila) after separation from Panthera

pantheraSolution = TestFlight.solution[-1] #The initial solution for stage 2 is the final position and velocity data obtained from numerical integration in stage 1 simulation
pantheraSolution[0] = 0 #Flight has to start at t=0

TestFlight2 = Flight(rocket=Aquila,
  initialSolution = pantheraSolution, #using the initial solution from the panthera stage
  environment= Env,
  inclination =90,
  heading = 0, 
terminateOnApogee= True
)

#Displaying useful results

panthera_burnout_velocity = pantheraSolution[6]
panthera_burnout_altitude = pantheraSolution[3]
aquila_apogee = TestFlight2.apogee

print(f"Panthera Burnout Velocity: {panthera_burnout_velocity} m/s")
print(f"Panthera Burnout Altitude: {panthera_burnout_altitude} m")
print(f"Aquila Apogee: {aquila_apogee} m")

#Displaying aquila trajectory
TestFlight2.plot3dTrajectory()