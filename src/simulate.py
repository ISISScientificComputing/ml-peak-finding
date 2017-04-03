import math
import numpy as np

from mantid.api import Projection
from mantid.geometry import CrystalStructure, ReflectionGenerator, OrientedLattice

salt = CrystalStructure("5.64 5.64 5.64", "F m -3 m", "Cl 0 0 0 1.0 0.05; Na 0.5 0.5 0.5 1.0 0.05")
generator = ReflectionGenerator(salt)

# Create list of unique reflections between 0.7 and 3.0 Angstrom
hkls = generator.getHKLs(.4, 10.0)
# Calculate structure factors for those HKLs
fSquared = generator.getFsSquared(hkls)

ws = CreateMDWorkspace(Dimensions=3, Extents=[-18,10,0,30,-10,10], Names="H,K,L", Units="A-1, A-1, A-1")
hkls = filter(lambda hkl: hkl[1] > 0, hkls)

n = len(hkls)
for i, (f, hkl) in enumerate(zip(fSquared, hkls)):
    print "Creating reflection %d of %d" % (i, n)
    h, k, l = hkl
    FakeMDEventData(InputWorkspace=ws, PeakParams=[100000,h,k,l,0.1], RandomizeSignal=True)

print "Adding Background noise"
FakeMDEventData(ws, UniformParams=100000000)

print "Binning"
ws_rebinned = BinMD(InputWorkspace=ws, AxisAligned=False, BasisVector0='H,A-1,1,0,0', BasisVector1='K,A-1,0,1,0', BasisVector2='L,A-1,0,0,1', OutputExtents='-18,10,0,30,-0.05,0.05', OutputBins='300,300,1', Parallel=True, OutputWorkspace='ws_rebinned')

print "Cropping to instrument"
mask = CreateSimulationWorkspace("SXD", BinParams="500,1.375,19000", UnitX="TOF")
sxd_real = LoadRaw(Filename='SXD23767.raw', OutputWorkspace='SXD23767')
mask = RebinToWorkspace(mask, sxd_real)
for i in range(mask.getNumberHistograms()):
    mask.setY(i, np.ones(mask.readY(i).shape))

sample = mask.sample()
sample.setCrystalStructure(salt)
lattice = OrientedLattice(salt.getUnitCell())
#UB = lattice.getUB().flatten()
UB = [0.09169989, -0.00510618, 0.15055867, 0.14087206, 0.06702044, -0.08328194, -0.05553794, 0.16320122, 0.03898424]
SetUB(mask, UB=UB)
mask = ConvertToDiffractionMDWorkspace(mask, OutputDimensions="HKL", Extents=[-18,10,0,30,-10,10])

# note: L and K dimension are swapped here due to fake UB matrix.
mask_rebinned = BinMD(InputWorkspace=mask, AxisAligned=False, BasisVector0='H,A-1,1,0,0', BasisVector1='K,A-1,0,1,0', BasisVector2='L,A-1,0,0,1', OutputExtents='-18,10,0,30,-0.05,0.05', OutputBins='300,300,1', Parallel=True, OutputWorkspace='mask_rebinned')

xDim = ws_rebinned.getXDimension()
yDim = ws_rebinned.getYDimension()
for i in range(xDim.getNBins()):
    for j in range(yDim.getNBins()):
        idx = ws_rebinned.getLinearIndex(i, j, 0)
        if mask_rebinned.signalAt(idx) == 0.0:
            ws_rebinned.setSignalAt(idx, 0.0)
