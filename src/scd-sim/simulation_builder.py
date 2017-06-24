import numpy as np
import scipy.ndimage.morphology as morph

import mantid.simpleapi as api
from mantid.geometry import (ReflectionGenerator, OrientedLattice)


class SimulationBuilder(object):

    def __init__(self):
        self._instrument_name = None
        self._mask_file = None
        self._wavelength_range = (.5, 10.)
        self._n_bins = 300
        self._temperature = 50
        self._background_alpha = 0.3e-3

    def build(self, cif_file, mask):
        crystal, inst_ws = self.load_cif(cif_file)

        # Just make a default UB
        lattice = OrientedLattice(crystal.getUnitCell())
        UB = lattice.getUB()

        hkls, fs = self.generate_hkls(crystal)
        signal, bins = self.generate_peaks(hkls, fs, UB) 
        background = self.generate_background(bins)

        total_signal = signal + background
        total_signal[mask == 0.0] = 0.0

        peaks = self.create_peaks_workspace(mask, hkls, UB, bins, inst_ws)

        ws = api.CreateMDWorkspace(3, Extents=self.extents, 
                                   Names='Q_lab_x, Q_lab_y, Q_lab_z', 
                                   Units='A^-1, A^-1, A^-1')

        ws = api.BinMD(ws, AxisAligned=False, Parallel=True, 
                       BasisVector1='Q_lab_x, A^-1, 1,0,0', 
                       BasisVector2='Q_lab_y, A^-1, 0,1,0', 
                       BasisVector3='Q_lab_z, A^-1, 0,0,1', 
                       OutputExtents=self.extents, 
                       OutputBins=[self.nbins]*3)
        ws.setSignalArray(total_signal)

        api.DeleteWorkspace(inst_ws)

        return ws, peaks

    def load_cif(self, cif_file):
        print "Loading Crystal"
        inst_ws = api.LoadEmptyInstrument(InstrumentName=self.instrument_name)
        api.LoadCIF(Workspace=inst_ws, InputFile=cif_file)
        crystal = inst_ws.sample().getCrystalStructure()
        return crystal, inst_ws
        
    def generate_hkls(self, crystal):
        generator = ReflectionGenerator(crystal)
        # Create list of unique reflections between 0.7 and 3.0 Angstrom
        hkls = generator.getHKLs(*self.wavelength_range)
        hkls = filter(lambda hkl: hkl[1] > 0, hkls)
        fs = np.array(generator.getFsSquared(hkls))
        return hkls, fs

    def generate_peaks(self, hkls, fs, UB):
        n_samples = 0.1
        total_signal = np.zeros((self.nbins, self.nbins, self.nbins))
        bounds = zip(self.extents[::2], self.extents[1::2])
        bins = [np.linspace(lower, upper, self.nbins+1) for lower, upper in bounds]
        values = np.zeros((int(np.sum(n_samples*fs)), 3))

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

    def generate_background(self, bins):
        print "Generating Background noise"
        size = (self.nbins, self.nbins, self.nbins)
        background = np.random.normal(5.0, 3., size=size)
        
        # weight background by Debye-Waller factor
        xv, yv, zv = np.meshgrid(bins[1][:-1], bins[2][:-1], bins[0][:-1])
        q_sq = xv**2 + yv**2 + zv**2
        weights = np.exp(-((self.background_alpha*self.temperature * q_sq.T)/2.0))
        background *= weights
        return background

    def create_peaks_workspace(self, mask_data, hkls, UB, bins, inst_ws):
        qs = np.array([np.dot(UB, hkl) * (2.0 * np.pi) for hkl in hkls])
        h_idx = np.digitize(qs[:, 0], bins[0])
        k_idx = np.digitize(qs[:, 1], bins[1])
        l_idx = np.digitize(qs[:, 2], bins[2])

        # dilate to catch all peaks
        m = morph.binary_dilation(mask_data).astype(mask_data.dtype)
        peak_locations = m[h_idx, k_idx, l_idx] != 0.0
        hkl_peaks = np.array(hkls)[peak_locations]

        peaks = api.CreatePeaksWorkspace(inst_ws, 0)
        api.SetUB(peaks, UB=UB)
        for hkl in hkl_peaks:
            api.AddPeakHKL(peaks, hkl)
        return peaks

    @property
    def extents(self):
        return self._extents

    @extents.setter
    def extents(self, extents):
        if isinstance(extents, list) and len(extents) == 6:
            self._extents = extents
        else:
            raise RuntimeError("Extents could not be set")

    @property
    def instrument_name(self):
        return self._instrument_name

    @instrument_name.setter
    def instrument_name(self, name):
        self._instrument_name = name
    
    @property
    def wavelength_range(self):
        return self._wavelength_range

    @wavelength_range.setter
    def wavelength_range(self, wavelength_range):
        if isinstance(wavelength_range, tuple) and len(wavelength_range) == 2:
            self._wavelength_range = wavelength_range
        else:
            raise RuntimeError("Cannot set wavelength_range")

    @property
    def nbins(self):
        return self._n_bins

    @nbins.setter
    def nbins(self, nbins):
        if isinstance(nbins, int):
            self._n_bins = nbins
        else:
            raise RuntimeError("Cannot set number of bins")

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, temp):
        if isinstance(temp, float):
            self._temperature = temp
        else:
            raise RuntimeError("Cannot set temperature")

    @property
    def background_alpha(self):
        return self._background_alpha

    @background_alpha.setter
    def background_alpha(self, alpha):
        if isinstance(alpha, float):
            self._background_alpha = alpha
        else:
            raise RuntimeError("Cannot set alpha")



