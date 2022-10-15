from mudpy import mud, cmud

with mud.MudFile(r"/Users/apetersen/PycharmProjects/MudPy/007572.msr", 'r') as mf:
    print("### Getting comments/subtitle ###")
    print(mf.get_subtitle())
    print(mf.get_header_comments())
    print(mf.get_comments())
