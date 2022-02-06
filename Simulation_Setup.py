import pandas as pd
import numpy as np
from rocketpy import SolidMotor, Rocket

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


#change drag_data
drag_data = np.genfromtxt(r"Drag_Data\CD_Test.csv", delimiter = ",")
dragOff = drag_data[1:1000, [0,3]]
dragOn = drag_data[1:1000,[0,4]]

print(average_propellant_density)
print(propellant_mass)

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
