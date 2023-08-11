# beamtests_dd4hep
<br/>

HCal Insert Prototype Simulation
---------------------------------

### EIC Software container
The simulation in this repository uses the DD4HEP framework in the EIC 
software container. You will need to download and enter this software 
container (Singularity and CVMFS need to be installed) to run the simulation:
```
curl --location https://get.epic-eic.org | bash
./eic-shell
```

### Compilation
The standard `ZDC_Sampling` type in the 'epic' repository doesn't support the
polyhedra shape, so we construct our `Polyhedra_ZDC_Sampling` type detector.
To use it, one needs to compile it first:
```
cmake -B build -S . -DCMAKE_INSTALL_PREFIX=install
cd build
make
```
To make the new detector type available, add the newly built library to 
LD_LIBRARY_PATH:
```
source setup.sh
```

### work flow
     (make_tree.py)
data ------------> ROOT tree
			    \
			     \
			      --> plot.py --> compare.C
			     /
			    /
sim  ------------> ROOT tree
     (make_tree.py)

* There are two make_tree.py scripts, one for simulation and the other one for 
  data processing. They will deal with different aspects of data and simulations,
  the output will be a ROOT tree with hit_cellID and hit_energy (in units of MIP).
* The plot.py script will read in the ROOT tree and produce histograms (graphs)
* The compare.C script produce comparison plots from histograms (graphs) resulted from plot.py

### Detector geometry
The detector geometry is defined in [this file](prototype.xml). Note that the 
detector is aligned parallel to the z-axis and placed 350 cm from the nominal 
particle generation point. The world volume is air. 
Also note how there are 9 readout cells per scintillator slice.

#### detector visualization
To view the prototype, one can use the `dd_web_display` toolkit:
```
dd_web_display prototype.xml
```

Another method is to convert the xml file into gdml file, and then show it with ROOT
```
geoConverter -compact2gdml -input prototype.xml -output prototype.gdml	# run this command with eic-shell
```
Root commands to show the prototype:
```
TGeoManager::Import("prototype.gdml") // root or GDML file
gGeoManager->SetVisLevel(10) // Increase it to get more detailed geometry
gGeoManager->GetTopVolume()->Draw("ogl")
```

### Running the simulation
To run the simulation, simply do:
```
./run.sh
```
This will run 100 events, with a single electron generated per event. 
The generated electron has an energy of 4 GeV, moves along the z-axis, and has 
its origin at (x,y,z) = (0,0,0). The DD4HEP output is digitized using the Juggler software.

![detector_geometry](figures/prototype_geometry.png?raw=true)

### Analysis
As an example, to draw the total digitized energy deposit in the sensitive 
area per event, do the following:
```
root -l prototype_reco_e-_2_GeV.edm4hep.root
events->Draw("Sum$(HCALHitsReco.energy)")
```

![energy_figure](figures/prototype_sum.png?raw=true)
<br/>
