import logging
import math
import jax.numpy as jnp
jnp.arange(5)

import src.globals as g

from src.iginData import iginData
from src.meshes.igmeshR import igmeshR

# -------------------------------------------------
# DEBUGGING PARAMETERS
# -------------------------------------------------

# Airfoil Mesh Plot: mplot mesh plot 0 (no) 1 (yes) 2 (Compare equal arc and equal abscissa mesh points)
g.mplot = 1
# Airfoil normal velocity plot: vplot 0 (no) 1 (yes)
g.vplot = 0
# Wake Vortex plot: 0 (no) 1 (yes)
g.wplot = 1
# Velocity plot by avoid source and observation points coincidence.
# Zavoid 0 (no, faster) 1 (yes, slower)
g.zavoid = 0
# Velocity field plot: 0 (no) 1 (yes)

# -------------------------------------------------

logging.basicConfig(filename=g.log_file, filemode = "w", force = True, level = logging.INFO, format="%(message)s")
logging.info("-------------------------------------------")
logging.info("igVortex")
logging.info("-------------------------------------------")

# -------------------------------------------------
# INPUT VARIABLES
# -------------------------------------------------

## Wing Geometry
l0_ = 5.0 # Wing Span (cm)
l_ = 0.5 * l0_ # Reduce the wing span by half to be used for 2D Modeling

# c_ = chord length (cm)
#   calculated while specifying the airfoil shape
#   # of data points that define the airfoil shape
n = 101
# Read airfoil shape data to determine the chord length
# Here use a formula to specify the airfoil shape
atmp_ = 0.8
x_ = jnp.linspace(-atmp_, atmp_ + 1e-10, n)
# Camber options are not elaborated yet.
camber = 0.0
y_ = camber * ( atmp_ ** 2 - x_ ** 2 )
c_ = x_[n] - x_[0]

m = 5 # # of vortex points on the airfoil

## Wing Motion Parameters

# Stroke angles (degrees)
phiT_ = 45
phiB_ = -45

a_ = 0 # rotation axis offset (cm)
beta_ = -30 # stroke plane angle (degrees)
f_ = 30 # flapping frequency (1/sec)
gMax_ = 30 # max rotation (degrees)
p = 5 # Rotation Speed Parameter [p >= 4]

rtOff = 0.0 # rotation timing offset (nondimentional)
# rtOff < 0 (advanced), rtoff = 0 (symmetric), rtOff > 0 (delayed)
# -0.5 < rtOff < 0.5

g.tau = 0.0 # phase shift for the time [0 <= tau < 2]
# 0 (start from TOP), 0 < tau < 1 (in between, start with DOWN stroke)
# 1 (BOTTOM), 1 < tau < 2 (in between, start with UP stroke), 2 (TOP)

g.mpath = 0 # Motion path parameter
# 0 (no tail), 1 (DUTail 2 periods), 2 (UDTail 2 periods)
# 3 (DUDUTail 4 periods), 4 (UDUDTail 4 periods)
logging.info(f"mpath = {g.mpath}")
## Fluid Parameters

rho_ = 0.001225 # g/cm^3 (air density)
# Ambient velocity (cm/sec, assume constant)
# can be interpreted as the flight velocity when the wind is calm
U_ = 100.0
V_ = 0.0

itinc = 1 # Time increment and # of time steps option
# 0 (manually specified) 1 (automatic)
# Specify nperiod ( # of periods ) below

g.eps = 0.5e-6 # Distance between the source and the observation point to be judged as zero

g.ibios = 1 # Vortex core model (Modified Biot-Savart equation)
# 0 (no) 1 (yes)
logging.info(f"ibios = {g.ibios}")

# velocity contour plots in space-fixed system
# used as the 4th argument of countour to control the range of velocity.

# space-fixed velocity plot: svInc (increment) svMax (max velocity)
svInc = 0.025
svMax = 2.5
g.svCont = jnp.arange(0.0, svMax + 1e-10, svInc) # Add a tiny number to include endpoint.

# wing-fixed velocity plot: wvInc (increment), wvMax (max velocity)
wvInc = 0.1
wvMax = 7.0
g.wvCont = jnp.arange(0.0, svMax + 1e-10, wvInc)

g.ivCont = 0 # Use of svCont and wvCont 0 (no) 1 (yes)
# The velocity range varies widely depending on the input parameters
# It is recommended to respecify this when input parameters are changed.
g.vpFreq = 1 # Frequency of velocity plots

# -------------------------------------------------
# Print Input Data
# -------------------------------------------------

logging.info(f"l_ = {l_}, phiT_ = {phiT_}, phiB = {phiB_}, a = {a_}, beta = {beta_}, f_ = {f_}")
logging.info(f"gMax_ = {gMax_}, p = {p}, rtOff = {rtOff}, tau = {g.tau}")
logging.info(f"U_ = {U_}, V_ = {V_}, m = {m}, n = {n}")

# -------------------------------------------------

# Nondimentionalize the input variables.
v_, t_, d_, e, c, x, y, a, beta, gMax, U, V = iginData(l_, phiT_, phiB_, c_, x_, y_, a_, beta_, f_, gMax_, U_, V_)

# Threshold radius for modified Biot-Savart equation
g.delta = 0.5 * c / (m - 1)
q = 1.0 # Multiplier 0 < q <= 1
g.delta *= q

if itinc == 0: # Manual
    dt = 0.025
    nstep = 81
else: # Automatic
    nperiod = 1
    dt = min( c / (m - 1), 0.1 * (4 / p) ) # 4 / p = duration of pitch
    nstep = nperiod * math.ceil(2 / dt)

logging.info(f"nstep = {nstep}, dt = {dt}")

# Comparison of flapping, pitching and air speeds.

air = math.sqrt(U_ ** 2 + V_ ** 2)
logging.info(f"air speed = {air}")
if air > 1e-03:
    fk = 2 * f_ * d_ / air # Flapping/Air Speed Ratio
    logging.info(f"flapping/air: speed ratio = {fk}")
    r = 0.25 * (c_ / d_) * (p / t_) * (gMax / f_)
    logging.info(f"pitching/flapping: speed ratio = {r}") # Pitch/Flapping Speed Ratio
    k = fk * r # Pitch/Air Speed Ratio
    logging.info(f"pitch/air: speed ratio = {k}") 
else:
    r = 0.25 * (c_ / d_) * (p / t_) * (gMax / f_)
    logging.info(f"pitch/flapping: speed ratio = {r}")

# Generate the vortex and collocation points on the airfoil.
xv, yv, xc, yc, dfc, m = igmeshR(c, x, y, n, m)