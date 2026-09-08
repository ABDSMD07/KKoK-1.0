from htr_engine import HTREngine


if __name__ == "__main__":

    print("=" * 50)
    print("HTR BASELINE TEST")
    print("=" * 50)

    engine = HTREngine()

    result = engine.predict("test_image.png")

    print()
    print("=" * 50)
    print("PREDICTED TEXT")
    print("=" * 50)
    print(result)
    print("=" * 50)