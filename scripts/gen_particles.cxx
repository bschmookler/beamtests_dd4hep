#include "HepMC3/GenEvent.h"
#include "HepMC3/ReaderAscii.h"
#include "HepMC3/WriterAscii.h"
#include "HepMC3/Print.h"

#include "TRandom3.h"
#include "TVector3.h"

#include <iostream>
#include <random>
#include <cmath>
#include <math.h>
#include <TMath.h>
#include <TDatabasePDG.h>
#include <TParticlePDG.h>

using namespace HepMC3;

// Generate single electron as input to the Insert simulation.
// --
// We generate events with a constant polar angle with respect to
// the proton direction and then rotate so that the events are given
// in normal lab coordinate system
// --
void gen_particles(
                    int n_events = 1000, 
                    TString out_fname = "", 
		    // double yshift = 225, // in mm
		    double yshift = 212.4, // in mm
                    double th_min = 0.040*TMath::RadToDeg(), // Minimum polar angle, in degrees
		    double th_max = 0.044*TMath::RadToDeg(), // Maximum polar angle, in degrees
		    double phi_min = -110, // Minimum azimuthal angle, in degrees
                    double phi_max = -70, // Maximum azimuthal angle, in degrees
                    TString particle_name = "e+",
                    double p = 4.3,  // Momentum in GeV/c
		    int dist = 0  //Momentum distribution: 0=fixed, 1=uniform, 2=Gaussian
                  )
{ 
  
  if (out_fname.IsNull())
      out_fname = Form("gen_%s_%.1f.hepmc", particle_name.Data(), p);
  WriterAscii hepmc_output(out_fname.Data());
  int events_parsed = 0;
  GenEvent evt(Units::GEV, Units::MM);

  // Random number generator
  TRandom3 *r1 = new TRandom3(0); //Use time as random seed
  
  // Getting generated particle information
  TDatabasePDG *pdg = new TDatabasePDG();
  TParticlePDG *particle = pdg->GetParticle(particle_name);
  const double mass = particle->Mass();
  const int pdgID = particle->PdgCode();

  double dp = p*0.2;
  double pi = TMath::Pi();

  for (events_parsed = 0; events_parsed < n_events; events_parsed++) {

    //Set the event number
    evt.set_event_number(events_parsed);

    // Define momentum with respect to proton direction
    double th    = r1->Uniform(th_min, th_max)*TMath::DegToRad();
    double phi   = r1->Uniform(phi_min, phi_max)*TMath::DegToRad();
    // double p1 = p;
    double x = (500 - 30)*tan(th)*cos(phi);
    double p1 = p + dp * x/4.74;

    //Total momentum distribution
    double pevent = 4;
    if(dist==0){ //fixed
      pevent = p1;
    }
    else if(dist==1){ //Uniform: +-50% variation
      pevent = p1*(1. + r1->Uniform(-0.5,0.5) );
    }
    else if(dist==2){  //Gaussian: Sigma = 0.1*mean
      while(pevent<0) //Avoid negative values
	pevent = r1->Gaus(p1, 0.1*p1);
    }

    double px = pevent * std::cos(phi) * std::sin(th);
    double py = pevent * std::sin(phi) * std::sin(th);
    double pz = pevent * std::cos(th);

    // FourVector(px,py,pz,e,pdgid,status)
    // type 4 is beam
    // type 1 is final state
    // pdgid 11 - electron 0.510 MeV/c^2
    GenParticlePtr pin1 =
        std::make_shared<GenParticle>(FourVector(0.0, 0.0, 10.0, 10.0), 11, 4);
    GenParticlePtr pin2 = std::make_shared<GenParticle>(
        FourVector(0.0, 0.0, 0.0, 0.938), 2212, 4);
    GenParticlePtr pout = std::make_shared<GenParticle>(
        FourVector(px, py, pz, sqrt(pevent*pevent + (mass * mass))),
        pdgID, 1);

    //If wanted, set non-zero vertex
    double vx = 0;
    double vy = yshift;
    double vz = 300.;
    // double vz = 0.;
    double vt = 0.;

    GenVertexPtr v1 = std::make_shared<GenVertex>();
    evt.shift_position_by(FourVector(vx, vy, vz, vt));

    v1->add_particle_in(pin1);
    v1->add_particle_in(pin2);

    v1->add_particle_out(pout);
    evt.add_vertex(v1);

    if (events_parsed == 0) {
      std::cout << "First event: " << std::endl;
      Print::listing(evt);
    }

    hepmc_output.write_event(evt);
    if (events_parsed % 1000 == 0) {
      std::cout << "Event: " << events_parsed << std::endl;
    }
    evt.clear();
  }
  hepmc_output.close();
  std::cout << "Events parsed and written: " << events_parsed << std::endl;
}
