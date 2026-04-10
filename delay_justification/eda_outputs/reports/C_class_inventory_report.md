# C. Class inventory report

## Exact class list (from filenames)
- Flicker
- Flicker_with_Sag
- Flicker_with_Swell
- Harmonics
- Harmonics_with_Sag
- Harmonics_with_Swell
- Interruption
- Notch
- Oscillatory_Transient
- Pure_Sinusoidal
- Sag
- Sag_with_Harmonics
- Sag_with_Oscillatory_Transient
- Swell
- Swell_with_Harmonics
- Swell_with_Oscillatory_Transient
- Transient

## Counts and class type
                      class_name  sample_count  samples_per_signal class_type  mentions_transient  mentions_sag  mentions_swell  mentions_harmonics  mentions_flicker  mentions_notch_spike
                         Flicker          1000                 100       pure                   0             0               0                   0                 1                     0
                Flicker_with_Sag          1000                 100   compound                   0             1               0                   0                 1                     0
              Flicker_with_Swell          1000                 100   compound                   0             0               1                   0                 1                     0
                       Harmonics          1000                 100       pure                   0             0               0                   1                 0                     0
              Harmonics_with_Sag          1000                 100   compound                   0             1               0                   1                 0                     0
            Harmonics_with_Swell          1000                 100   compound                   0             0               1                   1                 0                     0
                    Interruption          1000                 100       pure                   0             0               0                   0                 0                     0
                           Notch          1000                 100       pure                   1             0               0                   0                 0                     1
           Oscillatory_Transient          1000                 100       pure                   1             0               0                   0                 0                     0
                 Pure_Sinusoidal          1000                 100       pure                   0             0               0                   0                 0                     0
                             Sag          1000                 100       pure                   0             1               0                   0                 0                     0
              Sag_with_Harmonics          1000                 100   compound                   0             1               0                   1                 0                     0
  Sag_with_Oscillatory_Transient          1000                 100   compound                   1             1               0                   0                 0                     0
                           Swell          1000                 100       pure                   0             0               1                   0                 0                     0
            Swell_with_Harmonics          1000                 100   compound                   0             0               1                   1                 0                     0
Swell_with_Oscillatory_Transient          1000                 100   compound                   1             0               1                   0                 0                     0
                       Transient          1000                 100       pure                   1             0               0                   0                 0                     0

- Balanced dataset by class counts: True
- Pure class count: 9
- Compound class count: 8

## Cautious name-based disturbance relevance (inference from names only)
- transient behavior: classes containing `Transient` plus `Notch`
- sustained undervoltage/sag: classes containing `Sag`
- sustained overvoltage/swell: classes containing `Swell`
- harmonic distortion: classes containing `Harmonics`
- flicker: classes containing `Flicker`
- notch/spike behavior: class `Notch`
