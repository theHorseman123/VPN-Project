import pydivert
with pydivert.WinDivert() as w:
    for packet in w:
        print(packet)
        w.send(packet)