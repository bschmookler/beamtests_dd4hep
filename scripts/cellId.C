#include <bitset>

void cellId(const char *fname = "output.edm4hep.root", int nevent = -1)
{
    gROOT->SetBatch(1);
    TGaxis::SetMaxDigits(3);
    gStyle->SetOptStat(111110);
    gStyle->SetOptFit(111);

    TFile *fin = new TFile(fname, "read");
    TTree *tin = (TTree*) fin->Get("events");
    TTreeReader tr(tin);

    TTreeReaderArray<unsigned long> hit_cellID(tr, "HCALHits.cellID");
    // TTreeReaderArray<float> hit_energy(tr, "HCALHits.energy");
    TTreeReaderArray<float> hit_x(tr, "HCALHits.position.x");
    TTreeReaderArray<float> hit_y(tr, "HCALHits.position.y");
    // TTreeReaderArray<float> hit_z(tr, "HCALHits.position.z");

    const int n = tin->GetEntries();
    cout << "INFO -- number of events: " << n << endl;
    if (nevents > n || -1 == nevent)
	nevents = n;
    for (int i=0; i<nevents; i++)
    {
	tr.Next();
	for (int hi=0; hi<hit_cellID.GetSize(); hi++)
	{
	    int system_id = hit_cellID[hi] & 0x0000FF;
	    int layer_id = (hit_cellID[hi] & 0x00FF00) >> 8;
	    int cell_id = (hit_cellID[hi]  & 0xFF0000) >> 16;
	    int layer = 7*(system_id-1) + (layer_id - 1);
	    int cell = cell_id - 1;
	    if (layer < 7)
		cell += 7*layer;
	    else
		cell += 7*7 + 4*(layer-7);
	    cout << layer << "\t" << cell << "\t" 
		 << hit_cellID[hi] << "\t" 
		 << bitset<8>((hit_cellID[hi] >> 32) & 0xFF) << "\t"
		 << bitset<8>((hit_cellID[hi] >> 24) & 0xFF) << "\t"
		 << bitset<8>((hit_cellID[hi] >> 16) & 0xFF) << "\t"
		 << bitset<8>((hit_cellID[hi] >> 8) & 0xFF) << "\t"
		 << bitset<8>(hit_cellID[hi] & 0xFF) << "\t"
		 << endl;
	}
    }
}
