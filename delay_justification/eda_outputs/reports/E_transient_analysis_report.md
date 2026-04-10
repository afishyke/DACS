# E. Transient-analysis report

## Candidate transient-like classes
- Notch
- Oscillatory_Transient
- Sag_with_Oscillatory_Transient
- Swell_with_Oscillatory_Transient
- Transient

## Candidate sag/swell-like sustained classes
- Flicker_with_Sag
- Flicker_with_Swell
- Harmonics_with_Sag
- Harmonics_with_Swell
- Sag
- Sag_with_Harmonics
- Swell
- Swell_with_Harmonics

## Feature-based separability (grouped)
               feature  transient_group_mean  sag_swell_group_mean  cohens_d
     local_peak_change              0.359292              0.336589  0.110454
transient_energy_proxy              0.025455              0.031132 -0.550652
     derivative_energy              0.015377              0.004293  0.811737
    spectral_spread_hz            102.451516             62.523117  0.617368
high_freq_energy_ratio              0.030386              0.004168  0.648911

## Class transient score ranking
                      class_name  local_peak_change  transient_energy_proxy  derivative_energy  spectral_spread_hz  high_freq_energy_ratio  transient_score
  Sag_with_Oscillatory_Transient           1.091035                0.439084           2.074398            2.084987                3.211207         8.900711
                    Interruption           2.247962                2.953057          -0.126858            1.938157                0.994346         8.006664
Swell_with_Oscillatory_Transient           1.116546               -0.170568           2.271033            0.761354                0.666775         4.645140
           Oscillatory_Transient           0.509471               -0.706668           2.002400            1.020103                1.389127         4.214432
              Harmonics_with_Sag           0.240490                1.240241          -0.531376            0.377598               -0.251243         1.075710
              Sag_with_Harmonics           0.242347                0.881885          -0.567691            0.315872               -0.264913         0.607501
                Flicker_with_Sag           0.289594                0.759643          -0.558422            0.218323               -0.293703         0.415434
                             Sag           0.208748                0.337169          -0.591905            0.036956               -0.329895        -0.338927
                           Notch          -0.092911               -0.838051          -0.081688            0.197054               -0.311334        -1.126931
            Harmonics_with_Swell           0.097735               -0.099114          -0.166540           -0.464317               -0.565051        -1.197286
              Flicker_with_Swell           0.009790               -0.326051          -0.312627           -0.593457               -0.565265        -1.787610
            Swell_with_Harmonics          -0.036418               -0.313701          -0.346999           -0.603318               -0.567430        -1.867866
                           Swell          -0.000391               -0.572368          -0.360622           -0.785889               -0.592729        -2.311999
                       Harmonics          -1.309672               -0.709261          -0.510114           -0.695130               -0.634918        -3.859095
                       Transient          -1.198039               -0.895967          -0.714541           -1.045842               -0.615990        -4.470379
                         Flicker          -1.693689               -0.844112          -0.723895           -1.336857               -0.634066        -5.232619
                 Pure_Sinusoidal          -1.722596               -1.135219          -0.754553           -1.425594               -0.634918        -5.672879

## One-cycle limitation
- Each signal is one 50 Hz cycle (20 ms), so only within-cycle abruptness can be assessed robustly.
- Multi-cycle persistence, event duration beyond 20 ms, and recovery dynamics cannot be claimed from this dataset alone.
- Suitable hardware-delay features should emphasize local energy bursts and derivative peaks inside short windows, not long-horizon persistence.
