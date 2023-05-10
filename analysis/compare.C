void compare(const char *sim_file, const char*data_file = "beam_test/data.root")
{
    gROOT->SetBatch(1);

    map<string, TFile*> fin;
    fin["sim"]  = new TFile(sim_file, "read");
    fin["data"] = new TFile(data_file, "read");

    map<string, TH1F*> hist;

    TCanvas c("c", "c", 3000, 1200);
    c.Divide(5, 2);
    for (int i=0; i<10; i++)
    {
	const char *var = Form("layer%d_energy", i);
	hist["sim"] = (TH1F *) fin["sim"]->Get(var);
	hist["data"] = (TH1F *) fin["data"]->Get(var);
	hist["sim"]->Scale(hist["data"]->Integral()/hist["sim"]->Integral());

	c.cd(i+1);
	gPad->SetLogy(1);
	hist["sim"]->SetLineColor(kRed);
	hist["sim"]->SetName("sim");
	hist["data"]->SetLineColor(kBlue);
	hist["data"]->SetName("data");
	hist["data"]->Draw();
	gPad->Update();
	TPaveStats *st_data = (TPaveStats *) hist["data"]->FindObject("stats");
	st_data->SetTextColor(kBlue);
	hist["sim"]->Draw("sames");
	gPad->Update();
	TPaveStats *st_sim = (TPaveStats *) hist["sim"]->FindObject("stats");
	st_sim->SetTextColor(kRed);
	st_sim->SetY1NDC(0.57);
	st_sim->SetY2NDC(0.77);
    }
    c.SaveAs("compare_layer_energy.png");
}
