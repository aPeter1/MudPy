from mudpy import mud, cmud

with mud.MudFile(r"/Users/apetersen/PycharmProjects/MudPy/006523.msr", 'r') as mf:
    print("### Getting comments/subtitle ###")
    print(mf.get_subtitle())
    print(mf.get_header_comments())
    print(mf.get_comments())
    print("\n### Getting scalars ###")
    print(mf.get_scalers())

    print("\n### Getting independent variables ###")
    print(mf.get_independent_variables())

    print("\n### Getting temp and field")
    print(mf.get_temperature())
    print(mf.get_field())

    print("\n### Getting histograms")
    histograms = mf.get_histograms()
    print(histograms['Forw'])
    print(histograms[5])





