void plot(const char *fname = "output.edm4hep.root", const char*out_name = "output.root")
{
    gROOT->SetBatch(1);
    TGaxis::SetMaxDigits(3);
    gStyle->SetOptStat(111110);
    gStyle->SetOptFit(111);

    // const float ADC2MIP = 1;
    // const float energy_cut = 1e-6;
    const float ADC2MIP = 1/0.000465;
    const float energy_cut = 0.3;   // MIPs

    TFile *fin = new TFile(fname, "read");
    TTree *tin = (TTree*) fin->Get("events");
    TTreeReader tr(tin);

    /*
    TTreeReaderArray<int> mc_pdg(tr, "MCParticles.PDG");
    TTreeReaderArray<int> mc_generator_status(tr, "MCParticles.generatorStatus");
    TTreeReaderArray<int> mc_simulator_status(tr, "MCParticles.simulatorStatus");
    TTreeReaderArray<float> mc_charge(tr, "MCParticles.charge");
    TTreeReaderArray<double> mc_mass(tr, "MCParticles.mass");
    TTreeReaderArray<double> mc_vx(tr, "MCParticles.vertex.x");
    TTreeReaderArray<double> mc_vy(tr, "MCParticles.vertex.y");
    TTreeReaderArray<double> mc_vz(tr, "MCParticles.vertex.z");
    TTreeReaderArray<double> mc_endpoint_x(tr, "MCParticles.endpoint.x");
    TTreeReaderArray<double> mc_endpoint_y(tr, "MCParticles.endpoint.y");
    TTreeReaderArray<double> mc_endpoint_z(tr, "MCParticles.endpoint.z");
    TTreeReaderArray<float> mc_px(tr, "MCParticles.momentum.x");
    TTreeReaderArray<float> mc_py(tr, "MCParticles.momentum.y");
    TTreeReaderArray<float> mc_pz(tr, "MCParticles.momentum.z");
    TTreeReaderArray<float> mc_endpoint_px(tr, "MCParticles.momentumAtEndpoint.x");
    TTreeReaderArray<float> mc_endpoint_py(tr, "MCParticles.momentumAtEndpoint.y");
    TTreeReaderArray<float> mc_endpoint_pz(tr, "MCParticles.momentumAtEndpoint.z");
    */

    TTreeReaderArray<unsigned long> hit_layer_id(tr, "HCALHits.cellID");
    TTreeReaderArray<float> hit_energy(tr, "HCALHits.energy");
    TTreeReaderArray<float> hit_x(tr, "HCALHits.position.x");
    TTreeReaderArray<float> hit_y(tr, "HCALHits.position.y");
    TTreeReaderArray<float> hit_z(tr, "HCALHits.position.z");

    map<string, TH1F*> h1;
    map<string, TH2F*> h2;
    map<string, vector<TH1F*>> h1_array;

    TFile *fout = new TFile(out_name, "recreate");
    /*
    h1["mc_vx"] = new TH1F("mc_vx", "MC Vertex x", 100, -500, 500);
    h1["mc_vx"]->GetXaxis()->SetTitle("X/mm");
    h1["mc_vy"] = new TH1F("mc_vy", "MC Vertex y", 100, -500, 500);
    h1["mc_vy"]->GetXaxis()->SetTitle("Y/mm");
    h1["mc_vz"] = new TH1F("mc_vz", "MC Vertex z", 100, 4000, 6000);
    h1["mc_vz"]->GetXaxis()->SetTitle("Z/mm");
    h1["mc_pz"] = new TH1F("mc_pz", "MC Pz", 100, 0, 0.5);
    h1["mc_pz"]->GetXaxis()->SetTitle("Pz/GeV");
    h1["mc_pt"] = new TH1F("mc_pt", "MC Pt", 100, 0, 0.5);
    h1["mc_pt"]->GetXaxis()->SetTitle("Pt/GeV");
    h1["mc_p"] = new TH1F("mc_p", "MC P", 100, 0, 0.5);
    h1["mc_p"]->GetXaxis()->SetTitle("P/GeV");
    */
    h1["hit_layer_id"] = new TH1F("hit_layer_id", "layer id", 20, 0, 20);
    h1["hit_cell_id"] = new TH1F("hit_cell_id", "cell id", 45, 0, 45);
    h1["hit_x"] = new TH1F("hit_x", "x", 100, -50, 50);
    h1["hit_y"] = new TH1F("hit_y", "y", 100, -50, 50);
    h1["hit_z"] = new TH1F("hit_z", "z", 60, 5000, 5300);
    h1["hit_energy"] = new TH1F("hit_energy", "ADC count", 100, 0, 0.003*ADC2MIP);
    h1["hit_total_energy"] = new TH1F("hit_total_energy", "total energy (MIP)", 100, 0, /* 0.02*ADC2MIP */ 300);

    // h2["mc_vx_vs_vy"] = new TH2F("mc_vx_vs_vy", "MC Vertex X vs Y", 100, -500, 500, 100, -500, 500);
    h2["hit_x_vs_y"] = new TH2F("hit_x_vs_y", "x vs y", 100, -50, 50, 100, -50, 50);
    h2["hit_x_vs_z"] = new TH2F("hit_x_vs_z", "x vs z", 100, -50, 50, 100, 5000, 5300);
    h2["hit_y_vs_z"] = new TH2F("hit_y_vs_z", "y vs z", 100, -50, 50, 100, 5000, 5300);

    for (int l=0; l<10; l++)
    {
	const char *name = Form("layer%d_hit_energy", l);
	h1_array["hit_layer_energy"].push_back(new TH1F(name, Form("layer%d ADC count", l), 100, 0, /* 0.003*ADC2MIP */ 80));
    }


    double layer_id[] = {2097409, 2097665, 2097921, 2098177, 2098433, 2098689, 2098945, 2099201, 2099457, 2099713};
    cout << "INFO -- number of events: " << tin->GetEntries() << endl;
    int zero_event = 0;
    int ei = 0;
    while (tr.Next())
    {
	/*
	for (int pi=0; pi<mc_pdg.GetSize(); pi++)
	{
	    if (1 != mc_generator_status[pi])	// output particle
	    {
		float px = mc_px[pi];
		float py = mc_py[pi];
		float pz = mc_pz[pi];
		float pt = sqrt(px*px + py*py);
		float p = sqrt(px*px + py*py + pz*pz);
		h2["mc_vx_vs_vy"]->Fill(mc_vx[pi], mc_vy[pi]);
		h1["mc_vz"]->Fill(mc_vz[pi]);
		h1["mc_pz"]->Fill(pz);
		h1["mc_pt"]->Fill(pt);
		h1["mc_p"]->Fill(p);
	    }
	}
	*/

	float total_energy = 0;
	float layer_energy[10] = {0};
	for (int hi=0; hi<hit_x.GetSize(); hi++)
	{
	    total_energy += hit_energy[hi];
	}

	if (total_energy*ADC2MIP > energy_cut)
	{
	    for (int hi=0; hi<hit_x.GetSize(); hi++)
	    {
		unsigned long layer = (hit_z[hi]-5021.5)/28.2;
		int cell = 4*layer + 2*(hit_y[hi] < 0) + (hit_x[hi] > 0);
		if (1 == cell || 7 == cell)
		    continue;

		layer_energy[layer] += hit_energy[hi];

		h1["hit_layer_id"]->Fill(2*layer+1);
		h1["hit_cell_id"]->Fill(cell);
		h1["hit_energy"]->Fill(hit_energy[hi]*ADC2MIP);
		h1["hit_x"]->Fill(hit_x[hi]);
		h1["hit_y"]->Fill(hit_y[hi]);
		h1["hit_z"]->Fill(hit_z[hi]);
		h2["hit_x_vs_y"]->Fill(hit_x[hi], hit_y[hi]);
		h2["hit_x_vs_z"]->Fill(hit_x[hi], hit_z[hi]);
		h2["hit_y_vs_z"]->Fill(hit_y[hi], hit_z[hi]);
	    }

	    h1["hit_total_energy"]->Fill(total_energy*ADC2MIP);
	    for (int l=0; l<10; l++)
	    {
		h1_array["hit_layer_energy"][l]->Fill(layer_energy[l]*ADC2MIP);
	    }
	}
	else
	    zero_event++;

	ei++;
    }
    cout << "zero energy event: " << zero_event << endl;

    cout << h1["hit_energy"]->GetBinCenter(h1["hit_energy"]->GetMaximumBin()) << endl;
    for (int l=0; l<10; l++)
    {
	cout << l << "\t" << h1_array["hit_layer_energy"][l]->GetBinCenter(h1_array["hit_layer_energy"][l]->GetMaximumBin()) << endl;
    }

    h1["hit_total_energy"]->Fit("gaus");
    cout << "energy resolution: " << h1["hit_total_energy"]->GetFunction("gaus")->GetParameter(2) << " MIPS" << endl;

    TCanvas c("c", "c", 800, 800);
    for (auto ele : h1)
    {
	ele.second->Draw();
	c.SaveAs(Form("%s.png", ele.first.c_str()));

	fout->cd();
	ele.second->Write();
    }

    for (auto ele : h2)
    {
	ele.second->Draw();
	c.SaveAs(Form("%s.png", ele.first.c_str()));

	fout->cd();
	ele.second->Write();
    }

    TCanvas c1("c1", "c1", 4000, 1600);
    c1.Divide(5, 2);
    for (int l=0; l<10; l++)
    {
	c1.cd(l+1);
	gPad->SetLogy();
	h1_array["hit_layer_energy"][l]->Draw();

	fout->cd();
	h1_array["hit_layer_energy"][l]->Write();
    }
    c1.SaveAs("hit_layer_energy.png");

    fout->Write();
    fout->Close();
}
