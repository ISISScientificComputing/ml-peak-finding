import numpy as np
import os.path

import mantid.simpleapi as api


def create_mask_workspace(binning_file, output_file, nbins, extents):
    real_bins = api.LoadRaw(Filename=binning_file, OutputWorkspace='real_bins')
    instrument_name = real_bins.getInstrument().getName()
    mask = api.CreateSimulationWorkspace(instrument_name, BinParams="1,1,10", 
                                         UnitX="TOF")
    mask = api.RebinToWorkspace(mask, real_bins)
    api.DeleteWorkspace(real_bins)
    
    for i in range(mask.getNumberHistograms()):
        mask.setY(i, np.ones(mask.readY(i).shape))

    mask = api.ConvertToDiffractionMDWorkspace(mask, Extents=extents)

    mask_md = api.BinMD(InputWorkspace=mask, AxisAligned=False, 
                        BasisVector0='Q_x,A^-1,1,0,0', 
                        BasisVector1='Q_y,A^-1,0,1,0', 
                        BasisVector2='Q_z,A^-1,0,0,1', 
                        OutputExtents=extents, 
                        OutputBins=[nbins, nbins, nbins], 
                        Parallel=True, OutputWorkspace="mask")

    data = np.array(mask_md.getSignalArray())
    np.save(output_file, data.flatten())


def create_simulated_data(builder, cif_files, mask, file_prefix, 
                          output_directory):

    for i, cif_file in enumerate(cif_files):
        ws, peaks = builder.build(cif_file, mask)

        file_prefix = "{0}_{1}".format(file_prefix, i)
        file_prefix = os.path.join(output_directory, file_prefix)

        api.SaveMD(ws, file_prefix+"_MD.nxs")
        api.SaveNexus(peaks, file_prefix+"_peaks.nxs")
        api.SaveIsawUB(peaks, file_prefix + "_UB.mat")
        
        api.DeleteWorkspace(peaks)
        api.DeleteWorkspace(ws)
        
