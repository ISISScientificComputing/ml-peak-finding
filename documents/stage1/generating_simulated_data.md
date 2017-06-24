Generating SCD Data
===================

We need to be able to create data that looks as close as possible to real single
crystal diffraction data. Ideally we want to be able to generate data from a
variety of different samples and in a variety of different orientations.

A tool, `scd-sim`, has been created that allows the user to generate diffraction
data from a CIF using the Mantid framework.

Overview of Methodology
=======================

The high level process of generating simulated diffraction data is as follows:
- First a 3D binary mask is generated from an example instrument file with the
same binning in time of flight as the simulated output should have.

- Using a CIF file the positions in Q space and structure factors for peaks
falling within a given wavelength range are generated. Peaks are currenlty
approximated using a uniform Gaussian distribution.

- A background is then added to the data. The number of counts at a particular
position in the background is approximated as a Gaussian variable where the
mean is the average background value. A Debye-Waller term governing temperature
is also added. The temperature and alpha terms are simualtion parameters.

- Now the binary mask is used to remove all generated data which does not fall
in view of the instrument. This is simply done by zeroing out everything
outside the mask.

- Predicted peaks which fall outside of the mask are removed from the list as
these are not visible in the generated data.


Running the Tool
================

The general syntax for running the `scd-sim` module can be is as follows:

```bash
python scd-sim <command> <options>
```

There are currently two sub-commands for running the tool: `create` and `mask`.
Both commands require a configuration file. The `create` command requires a mask
generated from the `mask` command.

### Creating a Configuration
A configuration file is a JSON file that specifies the properties to be used
when creating a simulation. An example configuration is provided in the repo.
What the properties do are documented below:

| Property           | Description                                                        |
|--------------------|--------------------------------------------------------------------|
| `instrument_name`  | The name of the instrument to simulate data for e.g. "SXD", "WISH" |
| `wavelength_range` | List of size 2 for the upper and lower limits of the range to use. Using a very small lower bound will generate many, many peaks. |
| `extents` | List of size 6 with the extents of each of the upper and lower limits of the x,y, and z dimensions. The format is `[x1, x2, y1, y2, x1, z2]` where `1` is the lower bound and `2` is the upper bound |
| `nbins` | Number of bins to use when rebinning data. This applies to each axis, so for a value of `300` this would yield a volume of size` 300*300*300` |
| `temperature` | Temperature in `K` to use when computing the Debye-Waller factor for the background. |
| `alpha` | Alpha parameter to use when computing the Debye-Waller factor for the background. |


### Creating a Mask

Before creating a simulated data you will need to create a mask file. This
should only need to be done once per instrument and can be reused providing the
desired Q space binning is the same.

To create a mask you need to run the `mask` command and supply an example data
file from the instrument.  You will also need to supply a name for the
generated mask file. Finally you need to supply a config file.

```bash
python scd-sim mask -i SXD23767.raw -o sxdmask -c config.json
```

### Creating Simulated Data

Now simulated data can be created by running the `create` command. The `-i`
command can take 1 or more `.cif` files. A simulated workspace for each file
will be created.  The `-o` flag specifies an output directory to store the
resulting files in. The `-m` flag takes the program which mask file to use (see 
the previous step). The `-c` flag tells the program which config file to use.

```bash
python scd-sim create -i nacl.cif -o ~/simulation -m sxdmask.npy -c config.json
```

This command will output 3 files for every input CIF.
 - `_MD.nxs` files contain the MD workspace for simulated Q space data. This
 can be loaded into Mantid using `LoadMD`.
 - `_peaks.nxs` files contain data about the peaks in the generated data. This
 can be loaded into Mantid using `Load`
 - `_UB.mat` files contain the UB matrix used. This can be loaded onto a
 workspace in Mantid using `LoadIsawUB`.

