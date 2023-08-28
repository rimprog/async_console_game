TRASH_YEAR = 1969
PLASMA_GUN_YEAR = 2020


PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}


max_phrase_length = max([len(phrase) for phrase in PHRASES.values()])


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < TRASH_YEAR:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < PLASMA_GUN_YEAR:
        return 6
    else:
        return 2
