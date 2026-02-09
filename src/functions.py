import pandas as pd
import numpy as np
import pretty_midi
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"

def standardizeColums(file, yearCol, valCol, newValName):
    file = file[[yearCol, valCol]].copy()
    file.columns = ["year", newValName]
    return file

def loadAllData(dataDir):
    temp = pd.read_csv(dataDir + "/" + "temperature.csv")
    co2 = pd.read_csv(dataDir + "/" + "co2.csv")
    ice = pd.read_csv(dataDir + "/" + "nh_sea_ice_extent_annual.csv")
    extreme = pd.read_csv(dataDir + "/" + "extreme_events.csv")

    tempStand = standardizeColums(temp, "Year", "Anomaly", "temp_anomaly")
    co2Stand = standardizeColums(co2, "Year", "CO2_Mean", "co2_ppm")
    iceStand = standardizeColums(ice, "Year", "Ice_Extent", "ice_extent")
    extremeStand = standardizeColums(extreme, "Year", "Extremes_Index", "extreme_count")

    dataFrame = tempStand.merge(co2Stand, on="year", how="outer")
    dataFrame = dataFrame.merge(iceStand, on="year", how="outer")
    dataFrame = dataFrame.merge(extremeStand, on="year", how="outer")

    return dataFrame.sort_values("year").reset_index(drop=True)

def preProcessData(dataFrame, smoothingWindow=5, clipQuantiles=(0.01, 0.99)):
    dataFrame = dataFrame.copy()
    dataFrame = dataFrame.sort_values("year").reset_index(drop=True)

    numericCols = [
        "temp_anomaly",
        "co2_ppm",
        "ice_extent",
        "extreme_count",
    ]

    dataFrame[numericCols] = dataFrame[numericCols].interpolate(
        method="linear",
        limit_direction="both")

    if smoothingWindow and smoothingWindow > 1:
        dataFrame[numericCols] = (
            dataFrame[numericCols]
            .rolling(window=smoothingWindow, center=True)
            .mean())

        dataFrame[numericCols] = dataFrame[numericCols].bfill().ffill()

    if clipQuantiles:
        lo, hi = clipQuantiles

        for col in numericCols:
            lowVal = dataFrame[col].quantile(lo)
            highVal = dataFrame[col].quantile(hi)

            dataFrame[col] = dataFrame[col].clip(lowVal, highVal)

    dataFrame[numericCols] = dataFrame[numericCols].bfill().ffill()

    return dataFrame.reset_index(drop=True)

def normalizeData(dataFrame, cutoffQuantiles=(0.005, 0.995)):
    dataFrame = dataFrame.copy()

    climateCols = {
        "temp_anomaly": "temp_n",
        "co2_ppm": "co2_n",
        "ice_extent": "ice_n",
        "extreme_count": "extreme_n",
    }

    for rawCol, normCol in climateCols.items():

        lo = dataFrame[rawCol].quantile(cutoffQuantiles[0])
        hi = dataFrame[rawCol].quantile(cutoffQuantiles[1])

        clipped = dataFrame[rawCol].clip(lo, hi)

        # min–max scale
        norm = (clipped - lo) / (hi - lo)

        dataFrame[normCol] = norm

    # Invert ice so *less* ice = higher tension
    dataFrame["ice_n"] = 1.0 - dataFrame["ice_n"]

    return dataFrame

def harmony(row):
    baseScales = [[0, 2, 4, 7, 9],
                  [0, 3, 5, 7, 10]]
    scale = baseScales[0] if row["temp_n"] < 0.5 else baseScales[1]

    # register mapping: MIDI 48-72
    root = int(48 + row["temp_n"] * 24)

    # chord size: 2–5 notes
    chordSize = int(np.interp(row["co2_n"], [0, 1], [2, 5]))

    pitches = [(root + scale[i % len(scale)]) for i in range(chordSize)] 

    return pitches

def rhythm(row, minBeats=3, maxBeats=7):
    noteCount = int(np.interp(row["extreme_n"], [0, 1], [1, 8]))
    beatsPerBar = np.interp(row["extreme_n"], [0, 1], [minBeats, maxBeats])
    return np.linspace(0, beatsPerBar, noteCount, endpoint=False), beatsPerBar

def timbre(row):
    
    instruments = []

    # Map ice_n to velocities
    vel1 = int(np.interp(1 - row["ice_n"], [0, 1], [50, 110]))
    vel2 = int(np.interp(1 - row["ice_n"], [0, 1], [40, 90]))
    vel3 = int(np.interp(1 - row["ice_n"], [0, 1], [60, 100]))

    # Choose instruments based on ice_n
    if row["ice_n"] > 0.66:
        instruments.append((vel1, pretty_midi.instrument_name_to_program("Pad 2 (warm)")))
        instruments.append((vel2, pretty_midi.instrument_name_to_program("Synth Strings 1")))
    elif row["ice_n"] > 0.33:
        instruments.append((vel1, pretty_midi.instrument_name_to_program("Synth Strings 1")))
        instruments.append((vel3, pretty_midi.instrument_name_to_program("Clarinet")))
    else:
        instruments.append((vel1, pretty_midi.instrument_name_to_program("Clarinet")))
        instruments.append((vel2, pretty_midi.instrument_name_to_program("Pad 2 (warm)")))

    return instruments

def generatePiece(dataFrame, yearsPerBar=1, outputFile="sonicWeather.mid"):
    pm = pretty_midi.PrettyMIDI()
    
    timeCursor = 0.0

    for _, row in dataFrame.iterrows():
        pitches = harmony(row)
        starts, beatsPerBar = rhythm(row)
        for velocity, program in timbre(row):
            instrument = pretty_midi.Instrument(program=program)
            pm.instruments.append(instrument)

            duration = 0.8 #beats

            for start in starts:
                for pitch in pitches:
                    note = pretty_midi.Note(
                        velocity=velocity,
                        pitch=pitch,
                        start=timeCursor + start,
                        end=timeCursor + start + duration,
                    )
                    instrument.notes.append(note)

                timeCursor += beatsPerBar * yearsPerBar

    pm.write(outputFile)

    print(f"MIDI written to {outputFile}")