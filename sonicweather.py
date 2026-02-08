from src.functions import loadAllData, preProcessData, normalizeData


def main():
    print("Sonic Weather — Climate Change Sonification System")

    # -----------------------------
    # Load CSV data
    # -----------------------------
    print("Loading climate data...")
    df = loadAllData(
        data_dir="data"
    )

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

if __name__ == "__main__":
    main()