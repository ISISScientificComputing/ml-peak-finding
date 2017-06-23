import numpy as np
import scipy.ndimage as ndimage
import os.path

import mantid.simpleapi as api
from mantid.geometry import (ReflectionGenerator, OrientedLattice)


def create_mask_workspace(instrument_name, binning_file, mask_workspace, 
                          nbins, params):
    mask = api.CreateSimulationWorkspace(instrument_name, BinParams="1,1,10", 
                                         UnitX="TOF")
    real_bins = api.LoadRaw(Filename=binning_file, OutputWorkspace='real_bins')
    mask = api.RebinToWorkspace(mask, real_bins)
    api.DeleteWorkspace(real_bins)
    
    for i in range(mask.getNumberHistograms()):
        mask.setY(i, np.ones(mask.readY(i).shape))

    mask = api.ConvertToDiffractionMDWorkspace(mask, 
                                               Extents=params['md_extents'])

    mask_md = api.BinMD(InputWorkspace=mask, AxisAligned=False, 
                        BasisVector0='Q_x,A^-1,1,0,0', 
                        BasisVector1='Q_y,A^-1,0,1,0', 
                        BasisVector2='Q_z,A^-1,0,0,1', 
                        OutputExtents=params['md_extents'], 
                        OutputBins=[nbins, nbins, nbins], 
                        Parallel=True, OutputWorkspace=mask_workspace)

    return mask_md
    

def load_cif(instrument_name, cif_file):
    print "Loading Crystal"
    inst_ws = api.LoadEmptyInstrument(InstrumentName=instrument_name)
    api.LoadCIF(Workspace=inst_ws, InputFile=cif_file)
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
    n_samples = 0.1
    total_signal = np.zeros((nbins, nbins, nbins))
    bounds = zip(extents[::2], extents[1::2])
    bins = [np.linspace(lower, upper, nbins+1) for lower, upper in bounds]
    values = np.zeros((int(np.sum(n_samples*fs)), 3))

    print "Creating reflections"

    index = 0
    for i, (hkl, factor) in enumerate(zip(hkls, fs)):
        q = np.dot(UB, hkl) * (2.0 * np.pi)
        sample_size = int(n_samples*factor)
        conv = [[0.003, 0, 0], [0, 0.003, 0], [0, 0, 0.003]]
        v = np.random.multivariate_normal(q, conv, sample_size)
        values[index:index+sample_size] = v
        index += sample_size

    total_signal, _ = np.histogramdd(values, bins=bins)
    total_signal *= 100  # arbitrary scale factor approximate neutron counts
    return total_signal, bins


def generate_background(bins, T, alpha, nbins):
    print "Generating Background noise"
    background = np.random.normal(5.0, 3., size=(nbins, nbins, nbins))
    
    # weight background by Debye-Waller factor
    xv, yv, zv = np.meshgrid(bins[1][:-1], bins[2][:-1], bins[0][:-1])
    q_sq = xv**2 + yv**2 + zv**2
    weights = np.exp(-((alpha*T * q_sq.T)/2.0))
    background *= weights
    return background
    

def create_peaks_workspace(mask_data, hkls, UB, bins, inst_ws):
    qs = np.array([np.dot(UB, hkl) * (2.0 * np.pi) for hkl in hkls])
    h_idx = np.digitize(qs[:, 0], bins[0])
    k_idx = np.digitize(qs[:, 1], bins[1])
    l_idx = np.digitize(qs[:, 2], bins[2])

    # dilate to catch all peaks
    m = ndimage.morphology.binary_dilation(mask_data).astype(mask_data.dtype)
    peak_locations = m[h_idx, k_idx, l_idx] != 0.0
    hkl_peaks = np.array(hkls)[peak_locations]

    peaks = api.CreatePeaksWorkspace(inst_ws, 0)
    api.SetUB(peaks, UB=UB)
    for hkl in hkl_peaks:
        api.AddPeakHKL(peaks, hkl)
    return peaks


def create_simulated_data(params, cif_files):
    # make a mask for the instrument, only need to do this once
    mask = create_mask_workspace(params['instrument_name'], 
                                 params['mask_binning'], 
                                 params['mask_workspace'], 
                                 params['nbins'], params)

    for i, cif_file in enumerate(cif_files):
        crystal, inst_ws = load_cif(params['instrument_name'], cif_file)

        # Just make a default UB
        lattice = OrientedLattice(crystal.getUnitCell())
        UB = lattice.getUB()

        hkls, fs = generate_hkls(crystal, params['wavelength_range'])
        signal, bins = generate_peaks(hkls, fs, params['md_extents'], 
                                      params['nbins'], UB) 
        background = generate_background(bins, 
                                         params['temperature'], 
                                         params['background_alpha'], 
                                         params['nbins'])

        total_signal = signal + background
        mask_data = mask.getSignalArray()
        total_signal[mask_data == 0.0] = 0.0

        peaks = create_peaks_workspace(mask_data, hkls, UB, bins, inst_ws)

        ws = api.CreateMDWorkspace(3, Extents=params['md_extents'], 
                                   Names='Q_lab_x, Q_lab_y, Q_lab_z', 
                                   Units='A^-1, A^-1, A^-1')

        ws = api.BinMD(ws, AxisAligned=False, Parallel=True, 
                       BasisVector1='Q_lab_x, A^-1, 1,0,0', 
                       BasisVector2='Q_lab_y, A^-1, 0,1,0', 
                       BasisVector3='Q_lab_z, A^-1, 0,0,1', 
                       OutputExtents=params['md_extents'], 
                       OutputBins=[params['nbins']]*3)
        ws.setSignalArray(total_signal)

        file_prefix = params['file_prefix']+"_" + str(i)
        file_prefix = os.path.join(params['output_directory'], file_prefix)

        api.SaveMD(ws, file_prefix+"_MD.nxs")
        api.SaveNexus(peaks, file_prefix+"_peaks.nxs")
        api.SaveIsawUB(peaks, file_prefix + "_UB.mat")
        
        api.DeleteWorkspace(inst_ws)
        api.DeleteWorkspace(peaks)
        api.DeleteWorkspace(ws)
        
    api.DeleteWorkspace(mask)
