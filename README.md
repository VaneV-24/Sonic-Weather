Sonic Weather

---
# Overview:
---
This project is an algorithmic composition system written in Python that generates a 5 minute musical work in which over a centutry of historic weather is compressed into sound. Annual climate indicators of global temperature, atmospheric CO2 concentration, Artic sea-ice extent, and counts of extreme weather events are mapped to pitch, harmony, timbre and rhythmic disruption. Each bar represents 1 year, allowing long-term trends to become audible as evolving musical form.
---
# Musical Question:
---
The musical question this project is attempting to answer is can long-term climate change trends generate musically coherent large-scale form when mapped to compositional parameters?

---
# Data Sources:
---
The data sources used to create the composition are NOAA Climate at a Glance (annual global anomalies) for temperature anomaly, Global Monitoring Laboratory at Mauna Loa for CO2 concentration, NSIDC Sea Ice Index for sea ice extent and Our World in Data (EM-DAT derived annual disaster counts) for extreme events. All of this data are stored as CSV files in the folder called data.

---
# Time Mapping:
---
I chose to do 1 year as 1 bar with a base time signature of 4/4 and a tempo of about 60 BPM because I want to convey the changes the piece goes through clearly and have enough time to build into the intensity that will appear later on. Additionally, to make the contrast of the changing meter or subdivision based on extreme events be more apparent.

---
# Musical Mapping:
---
As the temparature anomaly rises: the key center shifts upward, register increases over time and bright orchestration can be heard in later years.

As CO2 concentration increases: chord tones increase, cluster probability increases and more voices are added.

As sea ice extent decreases: spectra becomes darker, more noise added, lower fliter cutoff and distortion.

As the number of extreme events changes, event spikes create rhythmic bursts, glitches, metric instability, and sudden modulations.

---
# Control Distribution:
---

---
# How to Run:
---
Create a virtual environment
python -m venv venv or python3 -m venv venv

Activate virtual environment
source venv/bin/activate (on Mac)
venv\Scripts\activate (on Windows)

Install required packages
pip install -r requirements.txt

Run Program
python sonicweather.py or python3 sonicweather.py

---
# Limitations:
---
The datasets all start in different years so I had to figure out how to deal with the variations in start years.

