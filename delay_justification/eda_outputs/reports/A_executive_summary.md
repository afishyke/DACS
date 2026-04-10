# A. Executive summary

- Inventory confirms 17 CSV class files, 1 MAT file, and 1 TXT metadata file.
- Classes are encoded directly in CSV filenames (exactly 17 class names).
- Each CSV has shape 1000 x 100; sample counts are balanced.
- Global amplitude range observed in waveform files: [-2.460116, 2.485719] (supports scaled/synthetic signal claim).
- With fs=5000 Hz and 100 samples/signal, each signal spans 20.000 ms (~1 cycle at 50 Hz).
- Transient-oriented features indicate strongest abrupt/localized behavior in classes containing Transient and in Notch; sag/swell classes look more sustained in-window.
