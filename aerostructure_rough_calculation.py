import numpy as np

# Setting geometry variables
r = 0.15 # Tank radius
t = 0.0025 # Tank thickness
l = 4 # approximate length of first stage
F = 20e3 # Thrust Force

# Setting material variables

# Medium Carbon Steel
sig_y = 620e6 # Average yield stress
p_g = 28e5 # Gauge Pressure
rho = 7700

# Hollow Cylinder Calculations
axial_stress = -F/(2*np.pi* r * t)
hoop_stress = p_g*r/t
long_pres_stress = p_g*r/(2*t)
total_long_stress = long_pres_stress + axial_stress

# Mass calculation
V_cyl = np.pi*(r**2 - (r-t)**2)*l
V_bothcaps =4 *np.pi *t*(r**2) 
V_total = V_cyl + V_bothcaps
m = V_total*rho

# Printing the Results
print("For the hollow cylinder: \n")
print(f"The hoop stress is {hoop_stress} Pa")
print(f"The total longitudinal stress is {total_long_stress} Pa")
print(f"The mass of the structure is {m}kg")