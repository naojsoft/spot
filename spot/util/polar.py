import math


def subaru_normalize_az(az_deg):
    az_deg = az_deg + 180.0
    #az_deg = az_deg % 360.0
    if math.fabs(az_deg) >= 360.0:
        az_deg = math.fmod(az_deg, 360.0)
    if az_deg < 0.0:
        az_deg += 360.0

    return az_deg
