import pandas as pd
import numpy as np
from music21 import stream, note, scale, tempo, instrument, meter
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
    extreme = pd.read_csv(dataDir + "/" + "extreme_events.csv")

    tempStand = standardizeColums(temp, "Year", "Anomaly", "tempAnomaly")
    co2Stand = standardizeColums(co2, "Year", "CO2_Mean", "co2ppm")
    extremeStand = standardizeColums(extreme, "Year", "Extremes_Index", "extremeCount")

    dataFrame = tempStand.merge(co2Stand, on="year", how="inner")
    dataFrame = dataFrame.merge(extremeStand, on="year", how="inner")

    return dataFrame.sort_values("year").reset_index(drop=True)

def preProcessData(dataFrame, smoothingWindow=3, clipQuantiles=(0.01, 0.99)):
    dataFrame = dataFrame.copy()
    dataFrame = dataFrame.sort_values("year").reset_index(drop=True)

    numericCols = [
        "tempAnomaly",
        "co2ppm",
        "extremeCount",
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
    df = dataFrame.copy()

    climateCols = {
        "tempAnomaly": "tempN",
        "co2ppm": "co2N",
        "extremeCount": "extremeN",
    }

    for rawCol, normCol in climateCols.items():

        lo = df[rawCol].quantile(cutoffQuantiles[0])
        hi = df[rawCol].quantile(cutoffQuantiles[1])

        # Clip first
        clipped = df[rawCol].clip(lo, hi)

        denom = (hi - lo)

        # Prevent division-by-zero
        if denom == 0:
            norm = 0.5  # neutral midpoint
        else:
            norm = (clipped - lo) / denom

        # Hard clamp to [0, 1]
        norm = norm.clip(0.0, 1.0)

        # Replace any possible NaN safely
        df[normCol] = norm.fillna(0.5)

    return df

def generatePiece(df, basePitch=60, melodicRange=3, tempoBPM=100):
    """
    df: preprocessed + normalized DataFrame with columns:
        - tempN (0..1)
        - co2N (0..1)
        - extremeN (0..1)
    basePitch: MIDI pitch for the lowest note
    melodicRange: how many semitones melody spans
    """
    # Clarinet playable range
    CLARINET_MIN = 50
    CLARINET_MAX = 96

    score = stream.Score()
    clarinetPart = stream.Part()
    clarinetPart.id = "Clarinet"
    clarinetPart.append(instrument.Clarinet())
    score.append(tempo.MetronomeMark(number=tempoBPM))

    prevPitch = None
    invertNextMotif = False

    # Phrase engine state (Movement 1 only)
    phraseLength = 4
    phraseCounter = 0
    phraseDirection = 1
    phraseTarget = None

    # Define 3 movements
    movements = [
        (1959, 1978, [1.0]),             # quarter notes only
        (1979, 1999, [1.0, 0.5]),        # quarter & eighth
        (2000, 2024, [0.5, 0.25])        # eighth, sixteenth
    ]

    scaleLow = scale.MajorScale('C')
    scaleHigh = scale.MajorScale('G')
    tempThreshold = 0.6  # to choose high/low scale

    for idx, row in df.iterrows():
        year = row["year"]
        temp = row["tempN"]
        co2 = row["co2N"]
        extreme = row["extremeN"]

        # Determine movement for rhythm options
        for startY, endY, rhythmOptions in movements:
            if startY <= year <= endY:
                break

        # --- Step 1: choose scale based on temperature ---
        currentScale = scaleHigh if temp > tempThreshold else scaleLow

        # Step 2: get scale pitches and shift into clarinet range
        scalePitches = [p.midi for p in currentScale.getPitches()]
        scalePitches = [p for p in scalePitches if CLARINET_MIN <= p <= CLARINET_MAX]

        # If too low, shift up in octaves
        while scalePitches and min(scalePitches) < CLARINET_MIN:
            scalePitches = [p + 12 for p in scalePitches if p + 12 <= CLARINET_MAX]
        # If too high, shift down
        while scalePitches and max(scalePitches) > CLARINET_MAX:
            scalePitches = [p - 12 for p in scalePitches if p - 12 >= CLARINET_MIN]

        if not scalePitches:
            scalePitches = [basePitch]  # fallback

        # Step 3: pick base note safely
        pitchNote = np.random.choice(scalePitches)

        # Apply small temperature influence as relative step
        tempStep = int(temp * melodicRange)  # ±3 semitones
        pitchNote += np.clip(tempStep, -melodicRange, melodicRange)

        # --- CO2 REGISTER DRIFT ---
        registerShift = int(co2 * 6)
        pitchNote += registerShift

        # Step 4: motif evolution (interval limitation)
        if prevPitch is not None:
            diff = pitchNote - prevPitch
            maxUp = 5
            maxDown = -3
            if diff > maxUp:
                pitchNote = prevPitch + maxUp
            elif diff < maxDown:
                pitchNote = prevPitch + maxDown

            # optional motif inversion
            if invertNextMotif:
                pitchNote = prevPitch - (pitchNote - prevPitch)

        # Step 5: extreme events influence on rhythm and velocity
        baseVelocity = 50
        velocity = int(np.clip(baseVelocity + extreme * 60, 0, 127))

        # Ensure pitch within clarinet range
        pitchNote = int(np.clip(pitchNote, CLARINET_MIN, CLARINET_MAX))

        # Step 6: create bar for this year
        bar = stream.Measure(number=year)
        bar.timeSignature = meter.TimeSignature('4/4')
        remainingLength = 4.0  # 1 bar = 4 quarter notes

        # Starting pitch for this bar
        currentPitch = pitchNote

         # Determine movement index
        if 1959 <= year <= 1975:
            movement = 1
        elif 1976 <= year <= 1995:
            movement = 2
        else:
            movement = 3

        # --- HYBRID PHRASE ENGINE (Movement 1 only) ---
        if movement == 1:
            if phraseCounter == 0:
                phraseDirection = np.random.choice([-1, 1])
                phraseTarget = currentPitch + phraseDirection * 5
            phraseCounter += 1
            if phraseCounter >= phraseLength:
                phraseCounter = 0

        while remainingLength > 0:
            # Choose a rhythm that fits remaining space
            possibleRhythms = [r for r in rhythmOptions if r <= remainingLength]
            qLen = remainingLength if not possibleRhythms else np.random.choice(possibleRhythms)

            # Limit melodic motion for coherence
            if movement == 1:
                maxStep = 2
                accidentalChance = 0.0
            elif movement == 2:
                maxStep = 5
                accidentalChance = 0.2
            else:
                if year < 2010:
                    rhythmOptions = [0.5]  # just eighths
                else:
                    rhythmOptions = [0.5, 0.25]  # intensify near climax
                maxStep = 3
                accidentalChance = 0.15  # chaotic but controlled
                if (np.random.rand() < accidentalChance and 
                    abs(nextPitch - currentPitch) <= 2):

                    chromaticShift = 1 if nextPitch > currentPitch else -1
                    candidate = currentPitch + chromaticShift

                    if CLARINET_MIN <= candidate <= CLARINET_MAX:
                        nextPitch = candidate

            # Stepwise movement within scale
            stepOptions = [p for p in scalePitches 
               if abs(p - currentPitch) <= maxStep 
               and p != currentPitch]

            if movement == 1 and phraseTarget is not None:
                stepOptions = [p for p in stepOptions
                               if (phraseTarget - currentPitch) * (p - currentPitch) >= 0]

                # Bar 4 gentle relaxation toward tonic
                if phraseCounter == 0:
                    stepOptions = sorted(scalePitches,
                                         key=lambda x: abs(x - basePitch))[:3]

            # If removing repetition leaves nothing, allow motion in one direction
            if not stepOptions:
                stepOptions = [p for p in scalePitches if p != currentPitch]

            # Absolute fallback
            if not stepOptions:
                stepOptions = scalePitches

            nextPitch = int(np.random.choice(stepOptions))

            # --- Add controlled chromaticism ---
            if np.random.rand() < accidentalChance:
                # Only allow neighbor tones (±1 semitone)
                chromaticShift = np.random.choice([-1, 1])
                candidate = nextPitch + chromaticShift

                # Keep inside clarinet range
                if CLARINET_MIN <= candidate <= CLARINET_MAX:
                    nextPitch = candidate

            # Final safety clip
            nextPitch = int(np.clip(nextPitch, CLARINET_MIN, CLARINET_MAX))

            # Create note
            n = note.Note(midi=nextPitch)
            n.quarterLength = qLen
            n.volume.velocity = velocity

            bar.append(n)

            # Update for next note
            currentPitch = nextPitch
            remainingLength -= qLen

        clarinetPart.append(bar)
        prevPitch = pitchNote

        # Motif inversion every 5 bars
        if (idx + 1) % 5 == 0:
            invertNextMotif = np.random.rand() < 0.5

    score.append(clarinetPart)
    return score