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
make install
```
To make the new detector type available, add the newly built library to 
LD_LIBRARY_PATH:
```
source setup.sh
```

### Running the simulation
To run the simulation, simply do:
```
./run.sh
```
This will run 1000 events, with a single electron generated per event. 
The generated electron has an energy of 10 GeV, moves along the z-axis, and has 
its origin at (x,y,z) = (0,0,0). The default geometry is 'prototype.xml', to
produce hits, one should make sure that the prototype is along the z-axis.
The DD4HEP output is digitized using the Juggler software.

The simulation will produce a '.edm4hep.root' file, which contains all simulation 
information. What is interesting to us is only hit related information, specifically:
cellID, energy and position. They are extracted by the [make_tree.py](analysis/sim/make_tree.py)
script.

To run a more complicated simulation, one needs to provide their own steeringFile
and compactFile. The steeringFile defines the beam profile and the compactFile
defines the prototype geometry and position. Try
```
./run.sh -h
```
for more available options.

#### CALI plugin
We are now using the [JANA](https://jeffersonlab.github.io/JANA2/index.html) based 
[eicrecon](https://github.com/eic/EICrecon) for reconstruction. To do that, one
needs to compile the [CALI](CALI) plugin, which is not a standard eicrecon plugin 
yet. To compile it:
* compile and install eicrecon, and make it the default executable
```
    cmake -S CALI -B CALI/build -DCMAKE_INSTALL_PREFIX=plugins
    cd CALI/build
    make install
```
* now, we can use the CALI plugin
```
    eicrecon -Pplugins=CALI -Ppodio:output_include_collection=CALIRawHits,CALIRecHits input.edm4hep.root
```

### Analysis
As an example, to draw the total digitized energy deposit in the sensitive 
area per event, do the following:
```
root -l prototype_reco_e-_2_GeV.edm4hep.root
events->Draw("Sum$(HCALHitsReco.energy)")
```

### Detector geometry
The detector geometry is defined in [this file](prototype.xml). The prototype
consists of 7 layers of hexagal cells and 13 layers of square cells. Each cell
is surrounded by 3D-printed plastic frame. There are 4 blocks per layer, and 7 
hexagal (4 square) cells per block.

The world volume is air. The prototype position is adjustable, by changing
the x0/y0/z0 values.

#### detector visualization
To view the prototype, one can use the `dd_web_display` toolkit:
```
dd_web_display prototype.xml
```
![detector_geometry](figures/prototype_geometry.png?raw=true)

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
<br/>
