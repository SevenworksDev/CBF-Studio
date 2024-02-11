import os, time

while True:
    if os.name == "nt":
        os.system("del build/*.zip")
    else:
        os.system("rm -rf build/*.zip")
    time.sleep(300)
