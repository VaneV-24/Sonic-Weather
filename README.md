Sonic Weather

---
## Overview
---
This project is an algorithmic composition system written in Python that generates a 2 minute musical work in which over half a centutry of historic weather is compressed into sound. Annual climate indicators of global temperature, atmospheric CO2 concentration, and counts of extreme weather events are mapped to pitch, harmony, and rhythmic disruption. Each bar represents 1 year, allowing long-term trends to become audible as evolving musical form.

---
## Musical Question
---
The musical question this project is attempting to answer is can long-term climate change trends generate musically coherent large-scale form when mapped to compositional parameters?

---
## Data Sources
---
The data sources used to create the composition are NOAA Climate at a Glance (annual global anomalies) for temperature anomaly, Global Monitoring Laboratory at Mauna Loa for CO2 concentration, and Our World in Data (EM-DAT derived annual disaster counts) for extreme events. All of this data are stored as CSV files in the folder called data.

---
## Time Mapping
---
I chose to do 1 year as 1 bar with a base time signature of 4/4 and a tempo of about 100 BPM because I want to convey the changes the piece goes through clearly and have enough time to build into the intensity that will appear later on.

---
## Musical Mapping
---
As the temperature anomaly changes: for higher temperatures the pitch is higher and for lower temperature the pitch is lower.

As CO2 concentration changes: the octave changes, for low CO2 the register is low (warm, calm) and for high CO2 the register is high (bright, tense).

As the number of extreme events changes: event spikes create rhythmic bursts, glitches, metric instability, and sudden modulations.

---
## Mapping Ranges
---
All climate variables are first normalized to the range [0, 1] using min–max scaling across the full historical dataset, and these values are then mapped into bounded musical parameter spaces with explicit cutoffs to preserve musical coherence. 

Normalized global temperature anomaly controls tonal center and register but is limited to a maximum span of twelve semitones and constrained to MIDI pitches 48–84, ensuring that long-term warming produces a gradual upward drift rather than uncontrolled registral extremes.

Atmospheric CO₂ concentration governs harmonic density by scaling chord sizes from two to eight voices and limiting cluster probability to a maximum of sixty percent, preventing complete saturation while still allowing increasing textural pressure.

Annual extreme-event counts regulate rhythmic disruption while preserving a 4/4 metric grid as the default, with probabilistic insertions of irregular subdivisions, brief metric shifts, and glitch-like bursts capped to avoid total metric collapse.

---
## How to Run
---
Create a virtual environment
```
python -m venv sonic_env
```
or 
```
python3 -m venv sonic_env
```
Activate virtual environment
```
source sonic_env/bin/activate (on Mac)
sonic_env\Scripts\activate (on Windows)
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

