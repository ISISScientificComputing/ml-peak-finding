import math
import numpy as np
import itertools
import os.path
import sys

from mantid.api import Projection
from mantid.geometry import CrystalStructure, ReflectionGenerator, OrientedLattice

params = {
    "instrument_name": "SXD",
    "wavelength_range": (.5, 10),
    "md_extents": [-17,17,-7,17,0,33],
    "mask_binning": 'SXD23767.raw',
    "mask_workspace":  "mask",
    "nbins": 300,
    "temperature": 50,
    "background_alpha": 0.3e-3,
    "output_directory": "/Users/samueljackson/simulation",
    "file_prefix": "SXD_"
}

cif_files = [
    '/Users/samueljackson/Downloads/1000041.cif',
    '/Users/samueljackson/Downloads/9011998.cif'
]

def create_mask_workspace(instrument_name, binning_file, mask_workspace, nbins):
    mask = CreateSimulationWorkspace(instrument_name, BinParams="1,1,10", UnitX="TOF")
    real_bins = LoadRaw(Filename=binning_file, OutputWorkspace='real_bins')
    mask = RebinToWorkspace(mask, real_bins)
    DeleteWorkspace(real_bins)
    
    for i in range(mask.getNumberHistograms()):
        mask.setY(i, np.ones(mask.readY(i).shape))

    mask = ConvertToDiffractionMDWorkspace(mask, Extents=params['md_extents'])
    mask_md = BinMD(InputWorkspace=mask, AxisAligned=False, BasisVector0='Q_x,A^-1,1,0,0', 
                                           BasisVector1='Q_y,A^-1,0,1,0', BasisVector2='Q_z,A^-1,0,0,1', 
                                           OutputExtents=params['md_extents'], OutputBins=[nbins, nbins, nbins], 
                                           Parallel=True, OutputWorkspace=mask_workspace)
    
    return mask_md
    
def load_cif(instrument_name, cif_file):
    print "Loading Crystal"
    inst_ws = LoadEmptyInstrument(InstrumentName=instrument_name)
    LoadCIF(Workspace=inst_ws, InputFile=cif_file)
    crystal = inst_ws.sample().getCrystalStructure()
    return crystal, inst_ws
    
def generate_hkls(crystal, wavelength_range):
    generator = ReflectionGenerator(crystal)
    # Create list of unique reflections between 0.7 and 3.0 Angstrom
    hkls = generator.getHKLs(*wavelength_range)
    hkls = filter(lambda hkl: hkl[1] > 0, hkls)
    fs = np.array(generator.getFsSquared(hkls))
    return hkls, fs

def generate_peaks(hkls, fs, extents, nbins, UB):
    n = len(hkls)
    n_samples = 0.1
    total_signal = np.zeros((nbins, nbins, nbins))
    bins = [np.linspace(lower, upper, nbins+1) for lower, upper in zip(extents[::2], extents[1::2])]
    values = np.zeros((int(np.sum(n_samples*fs)), 3))

    print "Creating reflections"

    index = 0
    for i, (hkl, factor) in enumerate(zip(hkls, fs)):
        q = np.dot(UB, hkl) * (2.0 * np.pi)
        sample_size = int(n_samples*factor)
        v = np.random.multivariate_normal(q, [[0.003, 0, 0], [0, 0.003, 0], [0, 0, 0.003]], sample_size)
        values[index:index+sample_size] = v
        index += sample_size

    total_signal, _ = np.histogramdd(values, bins = bins)
    total_signal *= 100
    return total_signal, bins

def generate_background(bins, T, alpha, nbins):
    print "Generating Background noise"
    background = np.random.normal(100, 50, size=(nbins, nbins, nbins))
    
    # weight background by Debye-Waller factor
    xv, yv, zv = np.meshgrid(bins[1][:-1], bins[2][:-1], bins[0][:-1] )
    q_sq = xv**2 + yv**2 + zv**2
    weights = np.exp(-((alpha*T *q_sq.T)/2.0))
    background *= weights
    return background
    
def create_peaks_workspace(mask_data, hkls, UB):
    qs = np.array([np.dot(UB, hkl) * (2.0 * np.pi) for hkl in hkls])
    h_idx = np.digitize(qs[:, 0], bins[0])
    k_idx = np.digitize(qs[:, 1], bins[1])
    l_idx = np.digitize(qs[:, 2], bins[2])

    peak_locations = mask_data[h_idx, k_idx, l_idx] != 0.0
    hkl_peaks = np.array(hkls)[peak_locations]

    peaks = CreatePeaksWorkspace(inst_ws, 0)
    SetUB(peaks, UB=UB)
    for hkl in hkl_peaks:
        AddPeakHKL(peaks, hkl)
    return peaks

if not os.path.exists(params['output_directory']):
    raise RuntimeError("Need an output directory to be defined")

#make a mask for the instrument, only need to do this once
mask = create_mask_workspace(params['instrument_name'], params['mask_binning'], params['mask_workspace'], params['nbins'])

for i, cif_file in enumerate(cif_files):
    crystal, inst_ws = load_cif(params['instrument_name'], cif_file)

    # Just make a default UB
    lattice = OrientedLattice(crystal.getUnitCell())
    UB = lattice.getUB()

    hkls, fs = generate_hkls(crystal, params['wavelength_range'])
    signal, bins = generate_peaks(hkls, fs, params['md_extents'], params['nbins'], UB) 
    background = generate_background(bins, params['temperature'], params['background_alpha'], params['nbins'])

    total_signal = signal + background
    mask_data = mask.getSignalArray()
    total_signal[mask_data == 0.0] = 0.0

    peaks = create_peaks_workspace(mask_data, hkls, UB)

    ws = CreateMDWorkspace(3, Extents=params['md_extents'], Names='Q_lab_x, Q_lab_y, Q_lab_z', Units='A^-1, A^-1, A^-1')
    ws = BinMD(ws, AxisAligned=False, Parallel=True, BasisVector1='Q_lab_x, A^-1, 1,0,0', BasisVector2='Q_lab_y, A^-1, 0,1,0', BasisVector3='Q_lab_z, A^-1, 0,0,1', 
                        OutputExtents=params['md_extents'], OutputBins=[params['nbins'],params['nbins'],params['nbins']])
    ws.setSignalArray(total_signal)

    file_prefix = os.path.join(params['output_directory'], params['file_prefix']+"_" + str(i))
    SaveMD(ws, file_prefix+"_MD.nxs")
    SaveNexus(peaks, file_prefix+"_peaks.nxs")
    SaveIsawUB(peaks, file_prefix + "_UB.mat")
    
    DeleteWorkspace(inst_ws)
    DeleteWorkspace(peaks)
    DeleteWorkspace(ws)
    
DeleteWorkspace(mask)
