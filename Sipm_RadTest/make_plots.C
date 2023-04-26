void make_plots(){

	//Set Style
	gStyle->SetOptStat(0);
	gStyle->SetPadBorderMode(0);
	gStyle->SetFrameBorderMode(0);
	gStyle->SetFrameLineWidth(2);
	gStyle->SetLabelSize(0.035,"X");
	gStyle->SetLabelSize(0.035,"Y");
	//gStyle->SetLabelOffset(0.01,"X");
	//gStyle->SetLabelOffset(0.01,"Y");
	gStyle->SetTitleXSize(0.04);
	gStyle->SetTitleXOffset(0.9);
	gStyle->SetTitleYSize(0.04);
	gStyle->SetTitleYOffset(0.9);

	//Proton KE = 55 MeV file
	TFile *f1 = TFile::Open("Sipm_proton.edm4hep.root");
	TTree *t1 = (TTree*) f1->Get("events");
	
	TH1 *h1 = new TH1D("h1","For 55 MeV Protons",100,-0.1,6);
	h1->SetLineColor(kBlue);h1->SetLineWidth(3);
	h1->GetXaxis()->SetTitle("Energy deposited in SiPM [MeV]");h1->GetXaxis()->CenterTitle();

	TH1 *h1a = new TH1D("h1a","For 55 MeV Protons",100,-0.1,6);
	h1a->SetLineColor(kRed);h1a->SetLineWidth(3);
	h1a->GetXaxis()->SetTitle("Energy deposited in SiPM [MeV]");h1a->GetXaxis()->CenterTitle();

	TCanvas *ctemp = new TCanvas("ctemp");
	t1->Draw("SipmHits.energy*1000.>>h1","fabs(SipmHits.position.z-0.875)<0.01");
	t1->Draw("SipmHits.energy*1000.>>h1a","fabs(SipmHits.position.z-12.325)<0.01");

	TCanvas *c1 = new TCanvas("c1");
	c1->SetLogy();
	h1->Draw();h1a->Draw("same");

	TPaveText* tex1 = new TPaveText(0.65,0.65,0.85,0.85,"NDCNB");
	tex1->AddText("1^{st} SiPM");tex1->SetTextColor(kBlue);
	tex1->SetFillStyle(4000);tex1->SetTextFont(63);tex1->SetTextSize(20);
	tex1->Draw();

	TPaveText* tex1a = new TPaveText(0.65,0.6,0.85,0.8,"NDCNB");
	tex1a->AddText("2^{nd} SiPM");tex1a->SetTextColor(kRed);
	tex1a->SetFillStyle(4000);tex1a->SetTextFont(63);tex1a->SetTextSize(20);
	tex1a->Draw();

	//Neutron KE = 1 MeV file
	TFile *f2 = TFile::Open("Sipm_neutron.edm4hep.root");
	TTree *t2 = (TTree*) f2->Get("events");

	TH1 *h2 = new TH1D("h2","For 1 MeV Neutrons",100,-0.1,6);
	h2->SetLineColor(kBlue);h2->SetLineWidth(3);
	h2->GetXaxis()->SetTitle("Energy deposited in SiPM [MeV]");h2->GetXaxis()->CenterTitle();

	TCanvas *c2 = new TCanvas("c2");
	c2->SetLogy();
	t2->Draw("SipmHits.energy*1000.>>h2");

	//Print to pdf
	c1->Print("SiPM_plots.pdf[");
	c1->Print("SiPM_plots.pdf");
	c2->Print("SiPM_plots.pdf");
	c2->Print("SiPM_plots.pdf]");

}

