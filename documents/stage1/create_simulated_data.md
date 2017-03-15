Create simulated data suitable for machine learning
---------------------------------------------------

One initial pseudo-code suggestion for how to do this:

* Loop over a set of crystal structures (cif files):
  * Convolute predicted peak positions with resolution from sample to get first Q-space file
  * Convolute with instrument resolution function
  * Make data noisy (take into account counting statistics)
  * Restrict Q-space view to that of the instrument
  * Loop over the different sample environments supported by WISH:
    * Add artefact for each sample container environment
    
A question is how close to real data does the simulated data needs to be? I practice we 
should be able to get very close, but say ~80% may be close enough. 
