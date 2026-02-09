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
    # Two scale types: major pentatonic (calm) vs minor pentatonic (tense)
    baseScales = [
        [0, 2, 4, 7, 9],      # Major pentatonic
        [0, 3, 5, 7, 10]      # Minor pentatonic
    ]
    scale = baseScales[0] if row["temp_n"] < 0.5 else baseScales[1]
    
    # Root pitch: constrained to 48-72 (12 semitone span max)
    root = int(48 + row["temp_n"] * 12)  # Changed from 24 to 12 semitones
    
    # Chord size: 2-8 voices based on CO2
    chordSize = int(np.interp(row["co2_n"], [0, 1], [2, 8]))
    
    # Cluster probability: up to 60% based on CO2
    clusterProb = min(0.6, row["co2_n"] * 0.6)
    
    # Generate pitches across 3 octaves, constrained to MIDI 48-84
    pitches = []
    for octave in range(3):
        for degree in scale:
            pitch = root + degree + (octave * 12)
            if 48 <= pitch <= 84:
                pitches.append(pitch)
    
    # Build chord with potential clusters
    chord = []
    for i in range(chordSize):
        if np.random.random() < clusterProb and len(pitches) > 1:
            # Cluster: pick adjacent semitones
            base_idx = np.random.randint(0, len(pitches))
            chord.append(pitches[base_idx])
            if base_idx + 1 < len(pitches):
                chord.append(pitches[base_idx] + 1)  # Semitone cluster
        else:
            # Normal: pick from scale
            chord.append(pitches[np.random.randint(0, len(pitches))])
    
    return sorted(list(set(chord))), scale, root

def rhythm(row):
    # Base: 4/4 time signature, 4 beats per bar
    beatsPerBar = 4
    
    # Base note density: 4-12 notes per bar
    baseNoteCount = int(np.interp(row["extreme_n"], [0, 1], [4, 12]))
    
    # Extreme events create rhythmic disruptions
    hasGlitch = row["extreme_n"] > 0.7 and np.random.random() < row["extreme_n"]
    hasMetricShift = row["extreme_n"] > 0.5 and np.random.random() < (row["extreme_n"] - 0.5)
    
    if hasMetricShift:
        # Occasional metric shifts - stick to valid time signatures
        beatsPerBar = np.random.choice([3, 5, 6, 7])  # All valid numerators
    
    # Generate base rhythm
    starts = np.linspace(0, beatsPerBar, baseNoteCount, endpoint=False)
    
    # Add glitch bursts (rapid note clusters)
    if hasGlitch:
        glitchPoint = np.random.uniform(0, beatsPerBar)
        glitchNotes = np.random.randint(3, 8)
        glitchDuration = 0.5  # Half beat of glitch
        glitchStarts = np.linspace(glitchPoint, glitchPoint + glitchDuration, glitchNotes)
        starts = np.concatenate([starts, glitchStarts])
        starts = np.sort(starts)
    
    return starts, beatsPerBar, hasGlitch

def timbre(row):
    # Base velocities
    vel1 = int(np.interp(row["ice_n"], [0, 1], [50, 110]))
    vel2 = int(np.interp(row["ice_n"], [0, 1], [40, 90]))
    vel3 = int(np.interp(row["ice_n"], [0, 1], [60, 100]))
    
    # Timbral degradation parameters (for future audio synthesis)
    filterCutoff = np.interp(row["ice_n"], [0, 1], [12000, 1500])  # Hz
    noiseMix = min(0.4, row["ice_n"] * 0.4)  # Max 40%
    distortion = row["ice_n"] * 0.3  # Moderate distortion
    
    # Choose instruments - darker sounds as ice decreases (higher ice_n)
    if row["ice_n"] < 0.33:
        # Low ice_n (high ice extent) - bright
        instruments = [
            (vel1, pretty_midi.instrument_name_to_program("Pad 2 (warm)")),
            (vel2, pretty_midi.instrument_name_to_program("Choir Aahs")),
            (vel3, pretty_midi.instrument_name_to_program("Flute"))
        ]
    elif row["ice_n"] < 0.66:
        # Medium ice_n - mixed
        instruments = [
            (vel1, pretty_midi.instrument_name_to_program("String Ensemble 1")),
            (vel2, pretty_midi.instrument_name_to_program("Clarinet")),
            (vel3, pretty_midi.instrument_name_to_program("Pad 2 (warm)"))
        ]
    else:
        # High ice_n (low ice extent) - dark
        instruments = [
            (vel1, pretty_midi.instrument_name_to_program("Contrabass")),
            (vel2, pretty_midi.instrument_name_to_program("Acoustic Bass")),
            (vel3, pretty_midi.instrument_name_to_program("Synth Strings 1"))
        ]
    
    return instruments, filterCutoff, noiseMix, distortion

def subsampleData(dataFrame, targetBars=75):
    if len(dataFrame) <= targetBars:
        return dataFrame
    
    # Use uniform sampling to preserve temporal distribution
    indices = np.linspace(0, len(dataFrame) - 1, targetBars, dtype=int)
    subsampled = dataFrame.iloc[indices].copy().reset_index(drop=True)
    
    print(f"Subsampled {len(dataFrame)} years down to {len(subsampled)} bars")
    return subsampled


# Define instrument range mapping
def get_instrument_range(program):
    name = pretty_midi.program_to_instrument_name(program).lower()
    
    # Bass instruments
    if any(x in name for x in ['contrabass', 'bass', 'tuba']):
        return (28, 60)  # E1 to C4
    # Low-mid instruments
    elif any(x in name for x in ['cello', 'bassoon', 'trombone']):
        return (36, 72)  # C2 to C5
    # Mid instruments
    elif any(x in name for x in ['viola', 'horn', 'clarinet', 'pad', 'string']):
        return (48, 76)  # C3 to E5
    # High instruments
    elif any(x in name for x in ['flute', 'violin', 'piccolo', 'voice', 'oohs']):
        return (60, 84)  # C4 to C6
    # Synth (wide range)
    elif 'synth' in name:
        return (36, 84)  # C2 to C6
    # Default mid-range
    else:
        return (48, 76)

def generatePiece(dataFrame, yearsPerBar=1, tempo=120, targetDuration=300, outputFile="sonicWeather.mid"):
    # Calculate how many bars we need for target duration
    secondsPerBar = (4 * 60) / tempo  # Assuming avg 4 beats per bar
    targetBars = int(targetDuration / secondsPerBar)
    
    # Subsample if needed
    if len(dataFrame) > targetBars:
        dataFrame = subsampleData(dataFrame, targetBars)
    
    print(f"Generating {len(dataFrame)} bars at {tempo} BPM (target: {targetDuration/60:.1f} minutes)")
    
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    timeCursor = 0.0
    secondsPerBeat = 60.0 / tempo
    
    # Track current instrument programs and their corresponding pretty_midi instruments
    current_programs = [None, None, None]
    current_instruments = [None, None, None]
    
    for row_idx, row in dataFrame.iterrows():
        chord, scale, root = harmony(row)
        starts, beatsPerBar, hasGlitch = rhythm(row)
        instrument_timbres, filterCutoff, noiseMix, distortion = timbre(row)
        
        # Add time signature change - ensure valid values
        try:
            ts = pretty_midi.TimeSignature(beatsPerBar, 4, timeCursor)
            pm.time_signature_changes.append(ts)
        except:
            # Fallback to 4/4 if the time signature is invalid
            ts = pretty_midi.TimeSignature(4, 4, timeCursor)
            pm.time_signature_changes.append(ts)
            beatsPerBar = 4
        
        # Determine instrument ranges based on current programs
        instrument_ranges = []
        for idx, (velocity_base, program) in enumerate(instrument_timbres):
            instrument_ranges.append(get_instrument_range(program))
        
        # Check if we need to create new instruments due to program changes
        for idx, (velocity_base, program) in enumerate(instrument_timbres):
            if current_programs[idx] != program:
                # Create new instrument track with this program
                new_instrument = pretty_midi.Instrument(program=program)
                pm.instruments.append(new_instrument)
                current_instruments[idx] = new_instrument
                current_programs[idx] = program
        
        # Rhythmic density per instrument
        rhythm_divisions = [
            starts[::3] if len(starts) > 3 else starts[::2],  # Sparse - bass
            starts,                                             # Full - melody
            starts[::2] if len(starts) > 2 else starts         # Medium - counter
        ]
        
        melody_pitches = []
        
        for idx in range(3):
            instrument = current_instruments[idx]
            if instrument is None:
                continue
                
            min_pitch, max_pitch = instrument_ranges[idx]
            velocity_base, program = instrument_timbres[idx]
            
            # Filter chord to instrument range
            valid_pitches = [p for p in chord if min_pitch <= p <= max_pitch]
            if not valid_pitches:
                # If no valid pitches in range, transpose chord into range
                transposed_chord = []
                for p in chord:
                    # Transpose up or down by octaves to fit
                    while p < min_pitch:
                        p += 12
                    while p > max_pitch:
                        p -= 12
                    if min_pitch <= p <= max_pitch:
                        transposed_chord.append(p)
                valid_pitches = sorted(list(set(transposed_chord)))

                # Fallback: if still no valid pitches, create scale in range
                if not valid_pitches:
                    valid_pitches = list(range(min_pitch, min(max_pitch, min_pitch + 24), 2))
            
            instrument_starts = rhythm_divisions[idx]
            if len(instrument_starts) == 0:
                continue
            
            last_pitch_idx = idx % len(valid_pitches)
            
            for start_idx, start in enumerate(instrument_starts):
                # Instrument-specific pitch behavior
                if idx == 0:
                    # Bass: root and fifth emphasis
                    if start_idx % 2 == 0:
                        target = root
                    else:
                        target = root + 7
                    
                    # Transpose target into range
                    while target < min_pitch:
                        target += 12
                    while target > max_pitch:
                        target -= 12
                    
                    pitch = min(valid_pitches, key=lambda p: abs(p - target))
                    
                elif idx == 1:
                    # Melody: more freedom
                    movement = (row_idx * 3 + start_idx * 7) % len(valid_pitches)
                    pitch = valid_pitches[movement]
                    melody_pitches.append((start, pitch))
                    
                else:
                    # Counter-melody: harmonize with melody
                    if melody_pitches:
                        closest_melody = min(melody_pitches, key=lambda x: abs(x[0] - start))
                        melody_pitch = closest_melody[1]
                        # Harmonize in thirds
                        target = melody_pitch - 4  # Major third below
                        
                        # Ensure target is in range
                        while target < min_pitch:
                            target += 12
                        while target > max_pitch:
                            target -= 12
                        
                        pitch = min(valid_pitches, key=lambda p: abs(p - target))
                    else:
                        movement = (start_idx * 3) % len(valid_pitches)
                        pitch = valid_pitches[movement]

                # Final safety check - clamp to range
                pitch = max(min_pitch, min(max_pitch, pitch))
                
                # Velocity with expression
                velocity = velocity_base
                if hasGlitch and start_idx % 2 == 0:
                    velocity = min(127, int(velocity * 1.3))  # Accent glitch notes
                velocity_var = ((row_idx + start_idx) * 11) % 20 - 10
                velocity = max(30, min(127, velocity + velocity_var))
                
                # Duration calculation
                if start_idx < len(starts) - 1:
                    next_start_idx = np.where(starts > start)[0]
                    if len(next_start_idx) > 0:
                        gap = starts[next_start_idx[0]] - start
                    else:
                        gap = beatsPerBar - start
                else:
                    gap = beatsPerBar - start
                
                # Articulation per instrument
                if idx == 0:
                    note_duration = gap * 0.95  # Sustained bass
                elif idx == 1:
                    # Varied melody
                    duration_types = [0.4, 0.6, 0.8, 0.95]
                    note_duration = gap * duration_types[start_idx % 4]
                else:
                    note_duration = gap * 0.7  # Medium
                
                # Glitch notes are very short
                if hasGlitch and gap < 0.2:
                    note_duration = gap * 0.5
                
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=pitch,
                    start=timeCursor + start * secondsPerBeat,
                    end=timeCursor + (start + note_duration) * secondsPerBeat,
                )
                instrument.notes.append(note)
        
        timeCursor += beatsPerBar * yearsPerBar * secondsPerBeat
    
    pm.write(outputFile)
    actualDuration = timeCursor
    print(f"MIDI written to {outputFile}")
    print(f"Actual duration: {actualDuration / 60:.2f} minutes ({actualDuration:.1f} seconds)")
    print(f"Created {len(pm.instruments)} instrument tracks")