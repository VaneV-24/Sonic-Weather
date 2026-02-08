Sonic Weather

---
## Overview
---
This project is an algorithmic composition system written in Python that generates a 5 minute musical work in which over a centutry of historic weather is compressed into sound. Annual climate indicators of global temperature, atmospheric CO2 concentration, Artic sea-ice extent, and counts of extreme weather events are mapped to pitch, harmony, timbre and rhythmic disruption. Each bar represents 1 year, allowing long-term trends to become audible as evolving musical form.

---
## Musical Question
---
The musical question this project is attempting to answer is can long-term climate change trends generate musically coherent large-scale form when mapped to compositional parameters?

---
## Data Sources
---
The data sources used to create the composition are NOAA Climate at a Glance (annual global anomalies) for temperature anomaly, Global Monitoring Laboratory at Mauna Loa for CO2 concentration, NSIDC Sea Ice Index for sea ice extent and Our World in Data (EM-DAT derived annual disaster counts) for extreme events. All of this data are stored as CSV files in the folder called data.

---
## Time Mapping
---
I chose to do 1 year as 1 bar with a base time signature of 4/4 and a tempo of about 60 BPM because I want to convey the changes the piece goes through clearly and have enough time to build into the intensity that will appear later on. Additionally, to make the contrast of the changing meter or subdivision based on extreme events be more apparent.

---
## Musical Mapping
---
As the temparature anomaly rises: the key center shifts upward, register increases over time and bright orchestration can be heard in later years.

As CO2 concentration increases: chord tones increase, cluster probability increases and more voices are added.

As sea ice extent decreases: spectra becomes darker, more noise added, lower fliter cutoff and distortion.

As the number of extreme events changes, event spikes create rhythmic bursts, glitches, metric instability, and sudden modulations.

---
## Mapping Ranges
---
All climate variables are first normalized to the range [0, 1] using min–max scaling across the full historical dataset, and these values are then mapped into bounded musical parameter spaces with explicit cutoffs to preserve musical coherence. 

Normalized global temperature anomaly controls tonal center and register but is limited to a maximum span of twelve semitones and constrained to MIDI pitches 48–84, ensuring that long-term warming produces a gradual upward drift rather than uncontrolled registral extremes.

Atmospheric CO₂ concentration governs harmonic density by scaling chord sizes from two to eight voices and limiting cluster probability to a maximum of sixty percent, preventing complete saturation while still allowing increasing textural pressure.

Arctic sea-ice extent is inverted and mapped to timbral degradation through a low-pass filter cutoff bounded between approximately 12 kHz and 1.5 kHz, a noise-mix ceiling of forty percent, and moderate distortion thresholds so that spectral erosion remains audible but not overwhelming.

Annual extreme-event counts regulate rhythmic disruption while preserving a 4/4 metric grid as the default, with probabilistic insertions of irregular subdivisions, brief metric shifts, and glitch-like bursts capped to avoid total metric collapse.

---
## How to Run
---
### Make sure you are in python version 3.11 for pretty-midi and setuptools version 68.2.2 or else the code wont't compile.
### To do this:
```
python3.11 -m venv venv
source venv/bin/activate
```
or
```
python3.11 -m venv venv
venv\Scripts\activate
```
```
pip uninstall -y setuptools
pip install setuptools==68.2.2
```

Create a virtual environment
```
python -m venv venv 
```
or 
```
python3 -m venv venv
```
Activate virtual environment
```
source venv/bin/activate (on Mac)
venv\Scripts\activate (on Windows)
```

Install required packages
```
pip install -r requirements.txt
```

Run Program
```
python sonicweather.py 
```
or 
```
python3 sonicweather.py
```
---
## Limitations
---
The datasets all start in different years so I had to figure out how to deal with the variations in start years.

