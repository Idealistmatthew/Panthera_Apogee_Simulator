import pandas as pd
import numpy as np
from rocketpy import Environment, SolidMotor, Rocket, Flight

file_path = "Mass_Data\Mass estimation master sheet.xlsx"
# file_path_csv = "Mass_Data\Mass estimation master sheet - Simulator.csv"

mass_data = pd.read_excel(file_path,"Simulator")

# mass_data = pd.read_csv(file_path_csv)
mass_data = mass_data.rename(columns={"Unnamed: 2": "Value"})
# mass_data["Value"][1:] = mass_data["Value"][1:].astype(float)

print(mass_data)


# Generating White Giant Data
thrust = mass_data["Value"][2]
t_burn = mass_data["Value"][6]
tank_radius = mass_data["Value"][11]/1000
nitrous_density = mass_data["Value"][21]
nitrous_volume = mass_data["Value"][22]
IPA_density = mass_data["Value"][29]
IPA_volume = mass_data["Value"][30]
propellant_volume = nitrous_volume + IPA_volume
average_propellant_density = (IPA_density*IPA_volume + nitrous_density*nitrous_volume)/propellant_volume
nitrous_mass = mass_data["Value"][20] 
nitrous_reserve_mass = mass_data["Value"][26]
IPA_mass = mass_data["Value"][28]
IPA_reserve_mass = mass_data["Value"][34]
propellant_mass = nitrous_mass + IPA_mass
propellant_mass_wreserve = propellant_mass + nitrous_reserve_mass + IPA_reserve_mass
grain_initial_height = propellant_mass/(average_propellant_density*np.pi*(tank_radius)**2)

#Generating Panthera Data
dry_mass = float(mass_data["First-pass mass"][0])
COM_dist = mass_data["Component CoM position, m"][0]
Nozzle_dist = float(mass_data["Component CoM position, m"][25] - COM_dist)
propellant_dist = float(mass_data["Component CoM position, m"][16])    # used distance between nitrous tank COM and COM of Panthera+Aquila

#Generating Aquila Data
aquila_mass = float(mass_data["First-pass mass"][83])

#change drag_data
drag_data = np.genfromtxt(r"Drag_Data\CD_Test.csv", delimiter = ",")
dragOff = drag_data[1:1000, [0,3]]
dragOn = drag_data[1:1000,[0,4]]

print(average_propellant_density)
print(propellant_mass)

Env = Environment(
    railLength=18,
    latitude=35.4,
    longitude=-117.8,
    elevation=621 #elevation above sea level, m
)

WhiteGiant = SolidMotor(
    thrustSource = thrust,
    burnOut = t_burn,
    grainNumber = 1,
    grainOuterRadius = tank_radius,
    grainDensity = average_propellant_density,
    grainInitialInnerRadius = 0,
    grainInitialHeight = grain_initial_height,
    #nozzleRadius = 0.0736 # Estimate for 10 kN WG
    #throatRadius = 0.0498 # Estimate for 10 kN WG
)
WhiteGiant.info()

Panthera = Rocket(
    motor = WhiteGiant,
    radius = tank_radius, #Assume same as tank outer radius
    mass = dry_mass, 
    inertiaI = 6.60, # arbitrary number
    inertiaZ = 0.0351, # arbitrary number
    distanceRocketNozzle = Nozzle_dist, 
    distanceRocketPropellant = propellant_dist, 
    powerOffDrag = dragOff,
    powerOnDrag = dragOn,
)

Panthera.info()
NoseCone = Panthera.addNose(length=0.40, kind="vonKarman", distanceToCM=3.8)

FinSet = Panthera.addFins(4, span=0.325, rootChord=0.4, tipChord=0.2, distanceToCM=-1.400)

Tail = Panthera.addTail(topRadius=0.15 , bottomRadius =0.65 ,length=1, distanceToCM=-3.8)
Panthera.setRailButtons([0,18])

#Creating a flight object to simulate the flight of the first stage
TestFlight = Flight(rocket=Panthera,
environment=Env,
inclination=90,
heading=0,
maxTime = t_burn
)

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
    mass = aquila_mass - N5800_propmass,
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

pantheraSolution = TestFlight.solution[-1] #The initial solution for stage 2 is the final position and velocity data obtained from numerical integration in stage 1 simulation
pantheraSolution[0] = 0 #Flight has to start at t=0

TestFlight2 = Flight(rocket=Aquila,
  initialSolution = pantheraSolution, #using the initial solution from the panthera stage
  environment= Env,
  inclination =90,
  heading = 0,
terminateOnApogee= True
)

panthera_burnout_velocity = pantheraSolution[6]
panthera_burnout_altitude = pantheraSolution[3]
aquila_apogee = TestFlight2.apogee

print(f"Panthera Burnout Velocity: {panthera_burnout_velocity} m/s")
print(f"Panthera Burnout Altitude: {panthera_burnout_altitude} m")
print(f"Aquila Apogee: {aquila_apogee} m")

#Displaying aquila trajectory
TestFlight2.plot3dTrajectory()