# B. Dataset structure report

## Tree
```text
XPQRS/
├── eda_outputs
│   ├── plots
│   ├── reports
│   └── tables
├── 5Kfs_1Cycle_50f_1000Sam_1A.mat
├── Details.txt
├── Flicker.csv
├── Flicker_with_Sag.csv
├── Flicker_with_Swell.csv
├── Harmonics.csv
├── Harmonics_with_Sag.csv
├── Harmonics_with_Swell.csv
├── Interruption.csv
├── Notch.csv
├── Oscillatory_Transient.csv
├── Pure_Sinusoidal.csv
├── Sag.csv
├── Sag_with_Harmonics.csv
├── Sag_with_Oscillatory_Transient.csv
├── seed_pqd_eda.py
├── Swell.csv
├── Swell_with_Harmonics.csv
├── Swell_with_Oscillatory_Transient.csv
└── Transient.csv
```

## Manifest (from extracted root)
                                name                        relative_path file_type  size_bytes size_human                                likely_purpose
                         Flicker.csv                          Flicker.csv       csv     1828064    1.74 MB Per-class waveform matrix (signals x samples)
                Flicker_with_Sag.csv                 Flicker_with_Sag.csv       csv     1845224    1.76 MB Per-class waveform matrix (signals x samples)
              Flicker_with_Swell.csv               Flicker_with_Swell.csv       csv     1808478    1.72 MB Per-class waveform matrix (signals x samples)
                       Harmonics.csv                        Harmonics.csv       csv     1833542    1.75 MB Per-class waveform matrix (signals x samples)
              Harmonics_with_Sag.csv               Harmonics_with_Sag.csv       csv     1848883    1.76 MB Per-class waveform matrix (signals x samples)
            Harmonics_with_Swell.csv             Harmonics_with_Swell.csv       csv     1812584    1.73 MB Per-class waveform matrix (signals x samples)
                    Interruption.csv                     Interruption.csv       csv     1889934    1.80 MB Per-class waveform matrix (signals x samples)
                           Notch.csv                            Notch.csv       csv     1847524    1.76 MB Per-class waveform matrix (signals x samples)
           Oscillatory_Transient.csv            Oscillatory_Transient.csv       csv     1839624    1.75 MB Per-class waveform matrix (signals x samples)
                 Pure_Sinusoidal.csv                  Pure_Sinusoidal.csv       csv     1802000    1.72 MB Per-class waveform matrix (signals x samples)
                             Sag.csv                              Sag.csv       csv     1826423    1.74 MB Per-class waveform matrix (signals x samples)
              Sag_with_Harmonics.csv               Sag_with_Harmonics.csv       csv     1855000    1.77 MB Per-class waveform matrix (signals x samples)
  Sag_with_Oscillatory_Transient.csv   Sag_with_Oscillatory_Transient.csv       csv     1851764    1.77 MB Per-class waveform matrix (signals x samples)
                           Swell.csv                            Swell.csv       csv     1789009    1.71 MB Per-class waveform matrix (signals x samples)
            Swell_with_Harmonics.csv             Swell_with_Harmonics.csv       csv     1817852    1.73 MB Per-class waveform matrix (signals x samples)
Swell_with_Oscillatory_Transient.csv Swell_with_Oscillatory_Transient.csv       csv     1818603    1.73 MB Per-class waveform matrix (signals x samples)
                       Transient.csv                        Transient.csv       csv     1846158    1.76 MB Per-class waveform matrix (signals x samples)
      5Kfs_1Cycle_50f_1000Sam_1A.mat       5Kfs_1Cycle_50f_1000Sam_1A.mat       mat    11362502   10.84 MB           Consolidated tensor for all classes
                     seed_pqd_eda.py                      seed_pqd_eda.py        py       35082   34.26 KB                                       Unknown
                         Details.txt                          Details.txt       txt         891   891.00 B                  Dataset metadata/description

## Label encoding detection
- folder names: False
- filenames: True
- metadata table (Details.txt): True
- separate label file: False

## File schema and cleanliness
                                file                        relative_path           shape  column_count  dtype_summary  missing_values  duplicate_rows  empty_file  malformed_rows  non_numeric_cells         notes
      5Kfs_1Cycle_50f_1000Sam_1A.mat       5Kfs_1Cycle_50f_1000Sam_1A.mat 1000 x 100 x 17           100        float64               0            1000           0               0                  0 variable: Out
                         Flicker.csv                          Flicker.csv      1000 x 100           100        float64               0               0           0               0                  0              
                Flicker_with_Sag.csv                 Flicker_with_Sag.csv      1000 x 100           100        float64               0               0           0               0                  0              
              Flicker_with_Swell.csv               Flicker_with_Swell.csv      1000 x 100           100        float64               0               0           0               0                  0              
                       Harmonics.csv                        Harmonics.csv      1000 x 100           100        float64               0               0           0               0                  0              
              Harmonics_with_Sag.csv               Harmonics_with_Sag.csv      1000 x 100           100        float64               0               0           0               0                  0              
            Harmonics_with_Swell.csv             Harmonics_with_Swell.csv      1000 x 100           100        float64               0               0           0               0                  0              
                    Interruption.csv                     Interruption.csv      1000 x 100           100 float64, int64               0               0           0               0                  0              
                           Notch.csv                            Notch.csv      1000 x 100           100        float64               0               0           0               0                  0              
           Oscillatory_Transient.csv            Oscillatory_Transient.csv      1000 x 100           100        float64               0               0           0               0                  0              
                 Pure_Sinusoidal.csv                  Pure_Sinusoidal.csv      1000 x 100           100 float64, int64               0             999           0               0                  0              
                             Sag.csv                              Sag.csv      1000 x 100           100 float64, int64               0               0           0               0                  0              
              Sag_with_Harmonics.csv               Sag_with_Harmonics.csv      1000 x 100           100        float64               0               0           0               0                  0              
  Sag_with_Oscillatory_Transient.csv   Sag_with_Oscillatory_Transient.csv      1000 x 100           100        float64               0               0           0               0                  0              
                           Swell.csv                            Swell.csv      1000 x 100           100 float64, int64               0               0           0               0                  0              
            Swell_with_Harmonics.csv             Swell_with_Harmonics.csv      1000 x 100           100        float64               0               0           0               0                  0              
Swell_with_Oscillatory_Transient.csv Swell_with_Oscillatory_Transient.csv      1000 x 100           100        float64               0               0           0               0                  0              
                       Transient.csv                        Transient.csv      1000 x 100           100        float64               0               0           0               0                  0              

Detailed samples saved: `eda_outputs/tables/csv_sample_rows_first12.csv` and `eda_outputs/tables/mat_sample_signals_first12.csv`.
