'''
    An example option file to digitize/reconstruct/clustering calorimeter hits
'''
from Gaudi.Configuration import *
import json
import os
import ROOT

from Configurables import ApplicationMgr, EICDataSvc, PodioInput, PodioOutput, GeoSvc
from GaudiKernel.SystemOfUnits import MeV, GeV, mm, cm, mrad

detector_name = str(os.environ.get("DETECTOR", "prototype.xml"))
# detector_config = str(os.environ.get("DETECTOR_CONFIG", detector_name))
# detector_version = str(os.environ.get("DETECTOR_VERSION", "main"))

detector_path = str(os.environ.get("DETECTOR_PATH", "."))
compact_path = os.path.join(detector_path, detector_name)

ci_hcal_insert_sf = "1."

# input and output
input_sims = [f.strip() for f in str.split(os.environ["JUGGLER_SIM_FILE"], ",") if f.strip()]
output_rec = str(os.environ["JUGGLER_REC_FILE"])
n_events = int(os.environ["JUGGLER_N_EVENTS"])

# geometry service
geo_service = GeoSvc("GeoSvc", detectors=[compact_path], OutputLevel=INFO)
# data service
podioevent = EICDataSvc("EventDataSvc", inputs=input_sims)

# juggler components
from Configurables import Jug__Digi__CalorimeterHitDigi as CalHitDigi
from Configurables import Jug__Reco__CalorimeterHitReco as CalHitReco
from Configurables import Jug__Reco__CalorimeterHitsMerger as CalHitsMerger
from Configurables import Jug__Reco__CalorimeterIslandCluster as IslandCluster
# from Configurables import Jug__Reco__ImagingPixelReco as ImCalPixelReco
# from Configurables import Jug__Reco__ImagingTopoCluster as ImagingCluster
# from Configurables import Jug__Reco__ClusterRecoCoG as RecoCoG
# from Configurables import Jug__Reco__ImagingClusterReco as ImagingClusterReco

# branches needed from simulation root file
sim_coll = [
    "MCParticles",
    "HCALHits",
    "HCALHitsContributions",
]

# input and output
podin = PodioInput("PodioReader", collections=sim_coll)
podout = PodioOutput("out", filename=output_rec)

# Hcal Hadron Endcap Insert
ci_hcal_insert_daq = dict(
         dynamicRangeADC=400.*MeV,
         capacityADC=4096,
         pedestalMean=60,
         pedestalSigma=3.16)
ci_hcal_insert_digi = CalHitDigi("ci_hcal_insert_digi",
         inputHitCollection="HCALHits",
         outputHitCollection="HCALHitsDigi",
         **ci_hcal_insert_daq)

ci_hcal_insert_reco = CalHitReco("ci_hcal_insert_reco",
        inputHitCollection=ci_hcal_insert_digi.outputHitCollection,
        outputHitCollection="HCALHitsReco",
        thresholdFactor=0.0,
        samplingFraction=ci_hcal_insert_sf,
        **ci_hcal_insert_daq)

ci_hcal_insert_merger = CalHitsMerger("ci_hcal_insert_merger",
        inputHitCollection=ci_hcal_insert_reco.outputHitCollection,
        outputHitCollection="HCALHitsRecoXY",
        readoutClass="HCALHits",
        fields=["layer", "slice"],
        fieldRefNumbers=[1, 0])

ci_hcal_insert_cl = IslandCluster("ci_hcal_insert_cl",
	# OutputLevel=DEBUG,
	inputHitCollection=ci_hcal_insert_reco.outputHitCollection,
	outputProtoClusterCollection="HCALClusters",
	splitCluster=False,
	minClusterHitEdep=1.0*MeV,  # discard low energy hits
	minClusterCenterEdep=30*MeV,
	sectorDist=5.0*cm,
	dimScaledLocalDistXY=[1.8, 1.8])          # dimension scaled dist is good for hybrid sectors with different module size
								

# Output
podout.outputCommands = ['drop *',
        'keep MCParticles',
        'keep *Digi',
        'keep *Reco*',
        'keep *Clusters*']

ApplicationMgr(
    TopAlg = [podin,
            ci_hcal_insert_digi, ci_hcal_insert_reco, ci_hcal_insert_merger, ci_hcal_insert_cl,
	    podout],
    EvtSel = 'NONE',
    EvtMax = n_events,
    ExtSvc = [podioevent],
    OutputLevel=DEBUG
)
