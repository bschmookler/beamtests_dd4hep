const int kLayers = 10;	// 4 square layers + 6 hexagon layers
const int kCells = 4;	// 4 cells per layer
			//
void plot(const char *fname = "output.edm4hep.root", 
	  const char*out_name = "output.root",
	  int N = -1, // number of events to be processed
	  int mode = 1,
	  int level = 1)
{
    /* mode
     * 0 -- calibration mode (muon)
     * 1 -- normal mode (electron)
     *
     * level
     * 0 -- simulation
     * 1 -- reconstruction
     */
    gROOT->SetBatch(1);
    TGaxis::SetMaxDigits(3);
    gStyle->SetOptStat(111110);
    gStyle->SetOptFit(111);

    float ADC2MIP = 1/0.000465;
    float energy_cut = 0.3;
    string unit = "MIP";
    if (0 == mode)
    {
	ADC2MIP = 1;
	energy_cut = 1e-6;   
	unit = "ADC";
    }
    const char * branch = (0 == level) ? "HCALHits" : "HCALHitsReco";
    const char * prefix = (0 == level) ? "sim" : "reco";

    TFile *fin = new TFile(fname, "read");
    TTree *tin = (TTree*) fin->Get("events");
    TTreeReader tr(tin);

    TTreeReaderArray<unsigned long> hit_cellID(tr, Form("%s.cellID", branch));
    TTreeReaderArray<float> hit_energy(tr, Form("%s.energy", branch));
    TTreeReaderArray<float> hit_x(tr, Form("%s.position.x", branch));
    TTreeReaderArray<float> hit_y(tr, Form("%s.position.y", branch));
    // TTreeReaderArray<float> hit_z(tr, Form("%s.position.z", branch));

    map<string, TH1F*> h1;
    map<string, TH1F*[10]> h1_layer;
    map<string, TH2F*> h2;

    TFile *fout = new TFile(out_name, "recreate");
    h1["hit_layer_id"] = new TH1F("hit_layer_id", "layer id", 20, 0, 20);
    h1["hit_cell_id"] = new TH1F("hit_cell_id", "cell id", 45, 0, 45);
    h1["hit_x"] = new TH1F("hit_x", "hit x", 100, -50, 50);
    h1["hit_y"] = new TH1F("hit_y", "hit y", 100, -50, 50);
    h1["hit_energy"] = new TH1F("hit_energy", Form("hit energy (%s)", unit.c_str()), 100, 0, 0.004*ADC2MIP);
    h1["event_x"] = new TH1F("event_x", "energy weighted x", 100, -50, 50);
    h1["event_y"] = new TH1F("event_y", "energy weighted y", 100, -50, 50);
    h1["event_energy"] = new TH1F("event_energy", Form("event energy (%s)", unit.c_str()), 100, 0, 0.02*ADC2MIP);

    // h2["hit_x_vs_y"] = new TH2F("hit_x_vs_y", "x vs y", 100, -50, 50, 100, -50, 50);
    // h2["hit_x_vs_z"] = new TH2F("hit_x_vs_z", "x vs z", 100, -50, 50, 10, 0, 10);
    // h2["hit_y_vs_z"] = new TH2F("hit_y_vs_z", "y vs z", 100, -50, 50, 10, 0, 10);

    for (int l=0; l<kLayers; l++)
    {
	const char *name = Form("layer%d_energy", l);
	const char *title = Form("layer%d energy (%s)", l, unit.c_str());
	h1_layer["energy"][l] = new TH1F(name, title, 100, 0, 0.02*ADC2MIP);
    }


    const int ne = tin->GetEntries();
    if (-1 == N)
	N = ne;
    else if (N > ne)
    {
	cout << "WARNING:\tonly " << ne << " events in the input file" << endl ;
	N = ne;
    }
    cout << "INFO:\twill process " << N << "/" << ne << " events" << endl;

    int zero_event = 0;
    for (int ei = 0; ei<N; ei++)
    {
	tr.Next();
	float event_energy = 0;
	float event_x = 0, event_y = 0;
	float layer_energy[10] = {0};
	for (int hi=0; hi<hit_x.GetSize(); hi++)
	{
	    event_energy += hit_energy[hi];
	}

	if (event_energy*ADC2MIP > energy_cut)
	{
	    for (int hi=0; hi<hit_x.GetSize(); hi++)
	    {
		int system_id = hit_cellID[hi] & 0x00FF;
		int layer_id = (hit_cellID[hi] & 0xFF00) >> 8;
		int layer = 4*(system_id-1) + layer_id - 1;
		int cell = 4*layer + 2*(hit_y[hi] < 0) + (hit_x[hi] > 0);
		if (1 == cell || 7 == cell)
		    continue;

		float x = hit_x[hi];
		float y = hit_y[hi];
		float E = hit_energy[hi];

		layer_energy[layer] += E;

		event_x += x*E;
		event_y += y*E;

		h1["hit_layer_id"]->Fill(2*layer+1);
		h1["hit_cell_id"]->Fill(cell);
		h1["hit_energy"]->Fill(E*ADC2MIP);
		h1["hit_x"]->Fill(x);
		h1["hit_y"]->Fill(y);
		// h2["hit_x_vs_y"]->Fill(x, y);
		// h2["hit_x_vs_z"]->Fill(x, layer);
		// h2["hit_y_vs_z"]->Fill(y, layer);
	    }

	    h1["event_x"]->Fill(event_x/event_energy);
	    h1["event_y"]->Fill(event_y/event_energy);
	    h1["event_energy"]->Fill(event_energy*ADC2MIP);
	    for (int l=0; l<10; l++)
	    {
		h1_layer["energy"][l]->Fill(layer_energy[l]*ADC2MIP);
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
	cout << l << "\t" << h1_layer["energy"][l]->GetBinCenter(h1_layer["energy"][l]->GetMaximumBin()) << endl;
    }

    h1["event_energy"]->Fit("gaus");
    cout << "energy resolution: " << h1["event_energy"]->GetFunction("gaus")->GetParameter(2) << " MIPS" << endl;

    TCanvas *c = new TCanvas("c", "c", 800, 800);
    for (auto ele : h1)
    {
	ele.second->Draw();
	c->SaveAs(Form("%s_%s.png", prefix, ele.first.c_str()));
    }

    // for (auto ele : h2)
    // {
    //     ele.second->Draw();
    //     c->SaveAs(Form("%s_%s.png", prefix, ele.first.c_str()));
    // }

    TCanvas *c1 = new TCanvas("c1", "c1", 4000, 1600);
    c1->Divide(5, 2);
    for (int l=0; l<10; l++)
    {
	c1->cd(l+1);
	gPad->SetLogy();
	h1_layer["energy"][l]->Draw();
    }
    c1->SaveAs(Form("%s_layer_energy.png", prefix));

    fout->cd();
    fout->Write();
    fout->Close();
}
