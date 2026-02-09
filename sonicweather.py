from src.functions import loadAllData, preProcessData, normalizeData, generatePiece


def main():
    print("Sonic Weather — Climate Change Sonification System")

    # -----------------------------
    # Load CSV data
    # -----------------------------
    print("Loading climate data...")
    df = loadAllData(dataDir="data")

    # -----------------------------
    # Preprocess (smoothing, filling)
    # -----------------------------
    print("Preprocessing data...")
    df = preProcessData(df)

    # -----------------------------
    # Normalize to [0,1]
    # -----------------------------
    print("Normalizing climate variables...")
    df = normalizeData(df)

    # -----------------------------
    # Generate music
    # -----------------------------
    print("Generating musical score...")
    score = generatePiece(df)

if __name__ == "__main__":
    main()