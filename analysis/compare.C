const int kColors[] = {kRed, kBlue};
const int kLayer = 10;
const int kCell = 4;

void compare(const char *file0,		 const char *file1 = "beam_test/data_hist.root",
	     const char *title0 = "sim", const char *title1 = "data")
{
    gROOT->SetBatch(1);
    gStyle->SetOptStat(101111);                                                 
    gStyle->SetOptFit(111);

    TFile* fin[2];
    fin[0] = new TFile(file0, "read");
    fin[1] = new TFile(file1, "read");

    TH1F* hist[2];
    TGraphErrors* g[2];

    TCanvas c("c", "c", 500*kLayer, 500*kCell);
    c.Divide(kLayer, kCell);
    // cells
    for (int i=0; i<kLayer*kCell; i++)
    {
	const char *var = Form("cell%d_energy", i);
	hist[0] = (TH1F *) fin[0]->Get(var);
	hist[0]->SetLineColor(kColors[0]);
	hist[0]->SetName(title0);
	hist[0]->SetTitle(Form("Cell%d Energy (#color[%d]{sim} vs #color[%d]{data});MIP;", i, kColors[0], kColors[1]));
	hist[1] = (TH1F *) fin[1]->Get(var);
	hist[1]->SetLineColor(kColors[1]);
	hist[1]->SetName(title1);
	hist[0]->Scale(hist[1]->Integral()/hist[0]->Integral());
	double min = hist[0]->GetMinimum();
	if (min > hist[1]->GetMinimum())
	    min = hist[1]->GetMinimum();
	if (0 == min)
	    min = 1;
	double max = hist[0]->GetMaximum();
	if (max < hist[1]->GetMaximum())
	    max = hist[1]->GetMaximum();
	if (0 == max)
	    max = 10;
	hist[0]->SetMaximum(max*1.2);
	hist[0]->SetMinimum(min*0.9);

	c.cd(kLayer*(i%kCell)+i/kCell+1);
	gPad->Clear();
	gPad->SetLeftMargin(0.05);
	gPad->SetRightMargin(0.05);
	gPad->SetLogy(1);
	const double st_height = 0.22;

	hist[0]->Draw("HIST");
	gPad->Update();
	TPaveStats *st0 = (TPaveStats *) hist[0]->FindObject("stats");
	st0->SetTextColor(kColors[0]);
	st0->SetY2NDC(0.9);
	st0->SetY1NDC(0.9-st_height);

	hist[1]->Draw("HIST sames");
	gPad->Update();
	TPaveStats *st1 = (TPaveStats *) hist[1]->FindObject("stats");
	st1->SetTextColor(kColors[1]);
	st1->SetY2NDC(0.9-st_height);
	st1->SetY1NDC(0.9-st_height*2);
    }
    c.SaveAs("compare_cell_energy.png");

    TCanvas c1("c1", "c1", 3000, 1200);
    c1.Divide(5, 2);

    TCanvas c2("c2", "c2", 800, 600);

    for (const char *var : {"x", "y", "energy"})
    {
	auto unit = strcmp(var, "energy") == 0 ? "MIP" : "mm";
	double st_height = 0.22;
	// layer level
	for (int i=0; i<10; i++)
	{
	    const char *vname = Form("layer%d_%s", i, var);
	    hist[0] = (TH1F *) fin[0]->Get(vname);
	    hist[0]->SetLineColor(kColors[0]);
	    hist[0]->SetName(title0);
	    hist[0]->SetTitle(Form("Layer%d %s (#color[%d]{sim} vs #color[%d]{data});%s;", i, var, kColors[0], kColors[1], unit));
	    hist[1] = (TH1F *) fin[1]->Get(vname);
	    hist[1]->SetLineColor(kColors[1]);
	    hist[1]->SetName(title1);
	    hist[0]->Scale(hist[1]->Integral()/hist[0]->Integral());
	    double min = hist[0]->GetMinimum();
	    if (min > hist[1]->GetMinimum())
		min = hist[1]->GetMinimum();
	    double max = hist[0]->GetMaximum();
	    if (max < hist[1]->GetMaximum())
		max = hist[1]->GetMaximum();

	    c1.cd(i+1);
	    if (strcmp(var, "energy") == 0)
	    {
		gPad->SetLogy(1);
		if (0 == min)
		    min = 1;
	    }

	    hist[0]->SetMaximum(max*1.1);
	    hist[0]->SetMinimum(min);
	    hist[0]->Draw("HIST");
	    gPad->Update();
	    TPaveStats *st0 = (TPaveStats *) hist[0]->FindObject("stats");
	    st0->SetTextColor(kColors[0]);
	    st0->SetY2NDC(0.9);
	    st0->SetY1NDC(0.9-st_height);

	    hist[1]->Draw("HIST sames");
	    gPad->Update();
	    TPaveStats *st1 = (TPaveStats *) hist[1]->FindObject("stats");
	    st1->SetTextColor(kColors[1]);
	    st1->SetY2NDC(0.9-st_height);
	    st1->SetY1NDC(0.9-st_height*2);
	}
	c1.SaveAs(Form("compare_layer_%s.png", var));

	// event level
	const char *vname = Form("event_%s", var);
	if (strcmp(var, "energy") == 0)
	{
	    st_height = 0.35;
	}

	hist[0] = (TH1F *) fin[0]->Get(vname);
	hist[0]->SetLineColor(kColors[0]);
	hist[0]->SetName(title0);
	hist[0]->SetTitle(Form("Event %s (#color[%d]{sim} vs #color[%d]{data}); %s;", var, kColors[0], kColors[1], unit));
	hist[1] = (TH1F *) fin[1]->Get(vname);
	hist[1]->SetLineColor(kColors[1]);
	hist[1]->SetName(title1);
	hist[0]->Scale(hist[1]->Integral()/hist[0]->Integral());

	double min = hist[0]->GetMinimum();
	if (min > hist[1]->GetMinimum())
	    min = hist[1]->GetMinimum();
	double max = hist[0]->GetMaximum();
	if (max < hist[1]->GetMaximum())
	    max = hist[1]->GetMaximum();
	hist[0]->SetMaximum(max*1.1);
	hist[0]->SetMinimum(min*0.9);
	c2.cd();
	// gPad->SetLogy(1);

	hist[0]->Draw("HIST");
	gPad->Update();
	TPaveStats *st0 = (TPaveStats *) hist[0]->FindObject("stats");
	st0->SetTextColor(kColors[0]);
	st0->SetY2NDC(0.9);
	st0->SetY1NDC(0.9-st_height);

	hist[1]->Draw("HIST sames");
	gPad->Update();
	TPaveStats *st1 = (TPaveStats *) hist[1]->FindObject("stats");
	st1->SetTextColor(kColors[1]);
	st1->SetY2NDC(0.9-st_height);
	st1->SetY1NDC(0.9-st_height*2);
	c2.SaveAs(Form("compare_event_%s.png", var));
    }

    for (const char *var : {"x", "y",})
    {
	const char *vname = Form("layer_%s_avg", var);
	g[0] = (TGraphErrors *) fin[0]->Get(vname);
	g[1] = (TGraphErrors *) fin[1]->Get(vname);

	g[0]->SetMarkerColor(kColors[0]);
	g[0]->SetName(title0);
	g[0]->SetTitle(Form("Layer %s mean (#color[%d]{sim} vs #color[%d]{data});layer;mm", var, kColors[0], kColors[1]));
	g[1]->SetMarkerColor(kColors[1]);
	g[1]->SetName(title1);
	double min = g[0]->GetHistogram()->GetMinimum();
	if (min > g[1]->GetHistogram()->GetMinimum())
	    min = g[1]->GetHistogram()->GetMinimum();
	if (min > 0)
	    min *= 0.9;
	else
	    min *= 1.1;
	double max = g[0]->GetHistogram()->GetMaximum();
	if (max < g[1]->GetHistogram()->GetMaximum())
	    max = g[1]->GetHistogram()->GetMaximum();
	if (max > 0)
	    max *= 1.1;
	else
	    max *= 0.9;
	g[0]->GetHistogram()->SetMaximum(max);
	g[0]->GetHistogram()->SetMinimum(min);

	c2.cd();
	g[0]->Draw("AP");
	// gPad->Update();
	// TPaveStats *st0 = (TPaveStats *) g[0]->FindObject("stats");
	// st0->SetTextColor(kBlue);
	g[1]->Draw("P");
	// gPad->Update();
	// TPaveStats *st1 = (TPaveStats *) g[0]->FindObject("stats");
	// st1->SetTextColor(kRed);
	// st1->SetY1NDC(0.1);
	// st1->SetY2NDC(0.5);
	c2.SaveAs(Form("compare_layer_%s_avg.png", var));
    }
}
