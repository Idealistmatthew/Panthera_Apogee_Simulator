import pandas as pd
import numpy as np
from rocketpy import Environment, SolidMotor, Rocket, Flight, Function
import matplotlib.pyplot as plt

file_path = "Mass_Data\Mass estimation master sheet.xlsx"
# file_path_csv = "Mass_Data\Mass estimation master sheet - Simulator.csv"

mass_data = pd.read_excel(file_path,"Simulator")

# mass_data = pd.read_csv(file_path_csv)
mass_data = mass_data.rename(columns={"Unnamed: 2": "Value"})
# mass_data["Value"][1:] = mass_data["Value"][1:].astype(float)

print(mass_data)

#import airfoil coefficient of lift vs angle of attack data
airfoil_file_path = r"Airfoil\xf-n2414-il-50000.csv"
airfoil_data = pd.read_csv(airfoil_file_path)



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

FinSet = Panthera.addFins(4, span=0.75, rootChord=1.2, tipChord=0.6, distanceToCM=-0.60, airfoil=(airfoil_file_path,"degrees"))

Tail = Panthera.addTail(topRadius=0.15 , bottomRadius =0.65 ,length=1, distanceToCM=-3.8)
Panthera.setRailButtons([0,18])

#Creating a flight object to simulate the flight of the first stage
TestFlight = Flight(rocket=Panthera,
environment=Env,
inclination=90,
heading=0,
maxTime = t_burn
)

# TestFlight.plot3dTrajectory()

def calculateFinFlutterAnalysis(Flight, finThickness, shearModulus):
        """Calculate, create and plot the Fin Flutter velocity, based on the
        pressure profile provided by Atmospheric model selected. It considers the
        Flutter Boundary Equation that is based on a calculation published in
        NACA Technical Paper 4197.
        Be careful, these results are only estimates of a real problem and may
        not be useful for fins made from non-isotropic materials. These results
        should not be used as a way to fully prove the safety of any rocket’s fins.
        IMPORTANT: This function works if only a single set of fins is added
        Parameters
        ----------
        finThickness : float
            The fin thickness, in meters
        shearModulus : float
            Shear Modulus of fins' material, must be given in Pascal
        Return
        ------
        None
        """
        # Post-process results
        if Flight.postProcessed is False:
            Flight.postProcess()

        s = (Flight.rocket.tipChord + Flight.rocket.rootChord) * Flight.rocket.span / 2
        ar = Flight.rocket.span * Flight.rocket.span / s
        la = Flight.rocket.tipChord / Flight.rocket.rootChord

        # Calculate the Fin Flutter Mach Number
        Flight.flutterMachNumber = (
            (shearModulus * 2 * (ar + 2) * (finThickness / Flight.rocket.rootChord) ** 3)
            / (1.337 * (ar**3) * (la + 1) * Flight.pressure)
        ) ** 0.5
        # FlutterMach = Flight.flutterMachNumber[:,:]
        # plt.plot(FlutterMach[:,:])
        # Calculate difference between Fin Flutter Mach Number and the Rocket Speed
        Flight.difference = Flight.flutterMachNumber - Flight.MachNumber

        # Calculate a safety factor for flutter
        # Flight.safetyFactor = Flight.flutterMachNumber / Flight.MachNumber
        # print(Flight.safetyFactor[:,:])
        # Calculate the minimun Fin Flutter Mach Number and Velocity
        # Calculate the time and height of minimun Fin Flutter Mach Number
        minflutterMachNumberTimeIndex = np.argmin(Flight.flutterMachNumber[:, 1])
        minflutterMachNumber = Flight.flutterMachNumber[minflutterMachNumberTimeIndex, 1]
        minMFTime = Flight.flutterMachNumber[minflutterMachNumberTimeIndex, 0]
        minMFHeight = Flight.z(minMFTime) - Flight.env.elevation
        minMFVelocity = minflutterMachNumber * Flight.env.speedOfSound(minMFHeight)

        # Calculate minimum difference between Fin Flutter Mach Number and the Rocket Speed
        # Calculate the time and height of the difference ...
        minDifferenceTimeIndex = np.argmin(Flight.difference[:, 1])
        minDif = Flight.difference[minDifferenceTimeIndex, 1]
        minDifTime = Flight.difference[minDifferenceTimeIndex, 0]
        minDifHeight = Flight.z(minDifTime) - Flight.env.elevation
        minDifVelocity = minDif * Flight.env.speedOfSound(minDifHeight)

        # Calculate the minimun Fin Flutter Safety factor
        # Calculate the time and height of minimun Fin Flutter Safety factor
        # minSFTimeIndex = np.argmin(Flight.safetyFactor[:, 1])
        # minSF = Flight.safetyFactor[minSFTimeIndex, 1]
        # minSFTime = Flight.safetyFactor[minSFTimeIndex, 0]
        # minSFHeight = Flight.z(minSFTime) - Flight.env.elevation

        # Print fin's geometric parameters
        print("Fin's geometric parameters")
        print("Surface area (S): {:.4f} m2".format(s))
        print("Aspect ratio (AR): {:.3f}".format(ar))
        print("TipChord/RootChord = \u03BB = {:.3f}".format(la))
        print("Fin Thickness: {:.5f} m".format(finThickness))

        # Print fin's material properties
        print("\n\nFin's material properties")
        print("Shear Modulus (G): {:.3e} Pa".format(shearModulus))

        # Print a summary of the Fin Flutter Analysis
        print("\n\nFin Flutter Analysis")
        print(
            "Minimum Fin Flutter Velocity: {:.3f} m/s at {:.2f} s".format(
                minMFVelocity, minMFTime
            )
        )
        print("Minimum Fin Flutter Mach Number: {:.3f} ".format(minflutterMachNumber))
        # print(
        #    "Altitude of minimum Fin Flutter Velocity: {:.3f} m (AGL)".format(
        #        minMFHeight
        #    )
        # )
        print(
            "Minimum of (Fin Flutter Mach Number - Rocket Speed): {:.3f} m/s at {:.2f} s".format(
                minDifVelocity, minDifTime
            )
        )
        print(
            "Minimum of (Fin Flutter Mach Number - Rocket Speed): {:.3f} Mach at {:.2f} s".format(
                minDif, minDifTime
            )
        )
        # print(
        #    "Altitude of minimum (Fin Flutter Mach Number - Rocket Speed): {:.3f} m (AGL)".format(
        #        minDifHeight
        #    )
        # )
        # print(
        #     "Minimum Fin Flutter Safety Factor: {:.3f} at {:.2f} s".format(
        #         minSF, minSFTime
        #     )
        # )
        # print(
        #     "Altitude of minimum Fin Flutter Safety Factor: {:.3f} m (AGL)\n\n".format(
        #         minSFHeight
        #     )
        # )

        # Create plots
        fig12 = plt.figure(figsize=(6, 9))
        ax1 = plt.subplot(211)
        ax1.plot()
        ax1.plot(
            Flight.flutterMachNumber[:, 0],
            Flight.flutterMachNumber[:, 1],
            label="Fin flutter Mach Number",
        )
        ax1.plot(
            Flight.MachNumber[:, 0],
            Flight.MachNumber[:, 1],
            label="Rocket Freestream Speed",
        )
        ax1.set_xlim(0, Flight.apogeeTime if Flight.apogeeTime != 0.0 else Flight.tFinal)
        ax1.set_title("Fin Flutter Mach Number x Time(s)")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Mach")
        ax1.legend()
        ax1.grid(True)

        ax2 = plt.subplot(212)
        ax2.plot(Flight.difference[:, 0], Flight.difference[:, 1])
        ax2.set_xlim(0, Flight.apogeeTime if Flight.apogeeTime != 0.0 else Flight.tFinal)
        ax2.set_title("Mach flutter - Freestream velocity")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Mach")
        ax2.grid()

        # ax3 = plt.subplot(313)
        # ax3.plot(Flight.safetyFactor[:, 0], Flight.safetyFactor[:, 1])
        # ax3.set_xlim(Flight.outOfRailTime, Flight.apogeeTime)
        # ax3.set_ylim(0, 6)
        # ax3.set_title("Fin Flutter Safety Factor")
        # ax3.set_xlabel("Time (s)")
        # ax3.set_ylabel("Safety Factor")
        # ax3.grid()

        plt.subplots_adjust(hspace=0.5)
        plt.show()

        return None

calculateFinFlutterAnalysis(TestFlight, 0.0105, 2.4e10)   
