# beamtests_dd4hep
<br/>

HCal Insert Prototype Simulation
---------------------------------

### EIC Software container
The simulation in this repository uses the DD4HEP framework in the EIC software container. You will need to download and enter this software container (Singularity and CVMFS need to be installed) to run the simulation:
```
curl --location https://get.epic-eic.org | bash
./eic-shell
```

### Detector geometry
The detector geometry is defined in [this file](prototype.xml). Note that the detector is aligned parallel to the z-axis and placed 350 cm from the nominal particle generation point. The world volume is air. Also note how there are 9 readout cells per scintillator slice.

### Running the simulation
To run the simulation, simply do:
```
./run_sim_proto.sh
```
This will run 100 events, with a single electron generated per event. The generated electron has an energy of 2 GeV, moves along the z-axis, and has its origin at (x,y,z) = (0,0,0). The DD4HEP output is digitized using the Juggler software.

![detector_geometry](figures/prototype_geometry.png?raw=true)

### Analysis
As an example, to draw the total digitized energy deposit in the sensitive area per event, do the following:

```
root -l prototype_reco_e-_2_GeV.edm4hep.root
events->Draw("Sum$(HCALHitsReco.energy)")
```

![energy_figure](figures/prototype_sum.png?raw=true)
<br/>
