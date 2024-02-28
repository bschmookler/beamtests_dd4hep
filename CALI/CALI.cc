// SPDX-License-Identifier: LGPL-3.0-or-later
// Copyright (C) 2023 Friederike Bock, Wouter Deconinck
//
//

#include <Evaluator/DD4hepUnits.h>
#include <JANA/JApplication.h>
#include <string>

#include "extensions/jana/JOmniFactoryGeneratorT.h"
#include "factories/calorimetry/CalorimeterClusterRecoCoG_factory.h"
#include "factories/calorimetry/CalorimeterHitDigi_factory.h"
#include "factories/calorimetry/CalorimeterHitReco_factory.h"
#include "factories/calorimetry/CalorimeterHitsMerger_factory.h"
#include "factories/calorimetry/CalorimeterIslandCluster_factory.h"
#include "factories/calorimetry/ImagingTopoCluster_factory.h"
#include "factories/calorimetry/CalorimeterTruthClustering_factory.h"

extern "C" {
    void InitPlugin(JApplication *app) {

	using namespace eicrecon;

	InitJANAPlugin(app);
// Make sure digi and reco use the same value
	decltype(CalorimeterHitDigiConfig::capADC)        HCAL_capADC = 4096;
	decltype(CalorimeterHitDigiConfig::dyRangeADC)    HCAL_dyRangeADC = 400 * dd4hep::MeV;
	decltype(CalorimeterHitDigiConfig::pedMeanADC)    HCAL_pedMeanADC = 60;
	decltype(CalorimeterHitDigiConfig::pedSigmaADC)   HCAL_pedSigmaADC = 3;
	decltype(CalorimeterHitDigiConfig::resolutionTDC) HCAL_resolutionTDC = 10 * dd4hep::picosecond;

	app->Add(new JOmniFactoryGeneratorT<CalorimeterHitDigi_factory>(
             "CALIRawHits", 
	    {"CALIHits"}, 
	    {"CALIRawHits"},
	    {
		.eRes = {},
		.tRes = 0.0 * dd4hep::ns,
		// .threshold = 1 * dd4hep::keV;
		.capADC = HCAL_capADC,
		// .capTime = 1000, // in ns
		.dyRangeADC = HCAL_dyRangeADC,
		.pedMeanADC = HCAL_pedMeanADC,
		.pedSigmaADC = HCAL_pedSigmaADC,
		.resolutionTDC = HCAL_resolutionTDC,
		.corrMeanScale = 1.0,
		.readout = "CALIHits",
	    },
	    app   // TODO: Remove me once fixed
	));
	app->Add(new JOmniFactoryGeneratorT<CalorimeterHitReco_factory>(
	     "CALIRecHits", 
	    {"CALIRawHits"}, 
	    {"CALIRecHits"},
	    {
		.capADC = HCAL_capADC,
		.dyRangeADC = HCAL_dyRangeADC,
		.pedMeanADC = HCAL_pedMeanADC,
		.pedSigmaADC = HCAL_pedSigmaADC,
		.resolutionTDC = HCAL_resolutionTDC,
		.thresholdFactor = 0.,
		.thresholdValue = 0, // 0.25 MeV --> 0.52 / 400 * 4096 = 2.56

		.sampFrac = 0.01,
		.readout = "CALIHits",
		.layerField = "layer",
		.sectorField = "system",
	    },
	    app   // TODO: Remove me once fixed
	));
	app->Add(new JOmniFactoryGeneratorT<CalorimeterHitsMerger_factory>(
	     "CALIMergedHits", 
	    {"CALIRecHits"},
	    {"CALIMergedHits"},
	    {
		.readout = "CALIHits",
		// .fields = {"system", "layer", "slice", "x", "y"},
		.fields = {"system", "layer"},	// merge these fields
		.refs = {1, 1},
	    },
	    app   // TODO: Remove me once fixed
	));

	app->Add(new JOmniFactoryGeneratorT<CalorimeterIslandCluster_factory>(
	     "CALIIslandProtoClusters",
	    {"CALIRecHits"},
	    {"CALIIslandProtoClusters"},
	    {
		// .sectorDist = 10 * dd4hep::cm,
		.localDistXY = {30*dd4hep::mm, 35*dd4hep::mm},
		// .dimScaledLocalDistXY = {10.0*dd4hep::mm, 10.0*dd4hep::mm},
		.splitCluster = false,
		.minClusterHitEdep = 100.0 * dd4hep::MeV,
		.minClusterCenterEdep = 1000.0 * dd4hep::MeV,
		// .transverseEnergyProfileMetric = "globalDistEtaPhi",
		// .transverseEnergyProfileScale = 1.,
	    },
	    app   // TODO: Remove me once fixed
	));
	app->Add(new JOmniFactoryGeneratorT<ImagingTopoCluster_factory>(
	     "CALIImagingTopoClusters",
	    {"CALIRecHits"},
	    {"CALIImagingTopoClusters"},
	    {
		.neighbourLayersRange = 1,
		.localDistXY = {55*dd4hep::mm, 50*dd4hep::mm},
		// .layerDistEtaPhi = {0.9, 0.5},
		// .sectorDist = 10.0 * dd4hep::cm,
		.minClusterHitEdep = 10.0 * dd4hep::MeV,
		.minClusterCenterEdep = 100.0 * dd4hep::MeV,
		.minClusterEdep = 3000.0 * dd4hep::MeV,
		.minClusterNhits = 1,
	    },
	    app   // TODO: Remove me once fixed
	));

	app->Add(new JOmniFactoryGeneratorT<CalorimeterClusterRecoCoG_factory>(
             "CALIIslandClusters",
            {"CALIIslandProtoClusters",     // edm4eic::ProtoClusterCollection
	     "CALIHits"},
            {"CALIIslandClusters",		    // edm4eic::Cluster
             "CALIIslandClusterAssociations"},    // edm4eic::MCRecoClusterParticleAssociation
	    {
		.energyWeight = "log",
		.sampFrac = 1.0,
		.logWeightBase = 6.2,
		.enableEtaBounds = false,
	    },
	    app   // TODO: Remove me once fixed
	    )
	);
	app->Add(new JOmniFactoryGeneratorT<CalorimeterClusterRecoCoG_factory>(
             "CALIImagingClusters",
            {"CALIImagingTopoClusters",     // edm4eic::ProtoClusterCollection
	     "CALIHits"},
            {"CALIImagingClusters",		    // edm4eic::Cluster
             "CALIImagingClusterAssociations"},    // edm4eic::MCRecoClusterParticleAssociation
	    {
		.energyWeight = "log",
		.sampFrac = 1.0,
		.logWeightBase = 6.2,
		.enableEtaBounds = false,
	    },
	    app   // TODO: Remove me once fixed
	    )
	);
    }
}
