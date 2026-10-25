
from functools import lru_cache
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

# All times are measured relative to 5:00 PM.
START_TIME = 0
HOUSES_OPEN = 90       # 7:00 PM relative to 5:30 PM
DEADLINE = 420         # 12:30 AM
PARK_CLOSE = 450       # 1:00 AM
BUFFER = 15
INTERVAL = 30
NUM_INTERVALS = 15

RIDES = [
    "Iron Gwazi",
    "Cheetah Hunt",
    "Sheikra",
    "Montu",
    "Cobras Curse",
]

HOUSES = [
    "Anaconda",
    "Stranglewood Estate",
    "Circus of Fear",
    "Raven's Mill",
    "M.A.R.S.",
    "Shadows of Wonderland",
]

# ============================================================
# INPUT DATA
# Populate each array with exactly 19 integer wait times.
#
# Index 0 = 5:00 PM
# Index 1 = 5:30 PM
# Index 2 = 6:00 PM
# ...
# Index 18 = 2:00 AM
#
# Use -1 for houses while they are closed.
# ============================================================

RIDE_WAITS = {
    "Iron Gwazi": [45,45,45,45,40,35,35,30,30,30,20,20,20,20,20],
    "Cheetah Hunt": [35,40,35,35,30,30,30,30,35,35,25,25,25,25,25],
    "Sheikra": [10,15,15,15,15,15,15,15,15,15,10,10,10,10,10],
    "Montu": [10,15,15,15,15,15,15,15,15,15,10,10,10,10,10],
    "Cobras Curse": [25,30,30,30,30,30,30,30,30,30,20,20,20,20,20],
}

HOUSE_WAITS = {
    "Anaconda": [-1,-1,-1,25,25,30,30,25,25,20,20,20,20,20,20],
    "Stranglewood Estate": [-1,-1,-1,30,30,30,30,25,25,25,25,20,25,30,30],
    "Circus of Fear": [-1,-1,-1,25,25,35,35,30,30,25,25,20,20,20,20],
    "Raven's Mill": [-1,-1,-1,15,15,20,20,25,20,20,20,20,20,20,20],
    "M.A.R.S.": [-1,-1,-1,10,10,15,25,35,40,40,40,35,35,40,40],
    "Shadows of Wonderland": [-1,-1,-1,15,15,15,25,30,35,40,45,40,40,65,65],
}

HOUSE_QUICK_QUEUE_WAITS = {
    "Anaconda": [-1,-1,-1,5,5,5,5,5,5,5,5,5,5,5,5],
    "Stranglewood Estate": [-1,-1,-1,5,5,5,5,5,5,5,5,5,5,5,5],
    "Circus of Fear": [-1,-1,-1,5,5,5,5,5,5,5,5,5,5,5,5],
    "Raven's Mill": [-1,-1,-1,5,5,5,5,5,5,5,5,5,5,5,5],
    "M.A.R.S.": [-1,-1,-1,5,5,5,5,5,5,5,5,5,5,5,5],
    "Shadows of Wonderland": [-1,-1,-1,5,5,5,5,5,5,5,5,5,5,5,5],
}


# ============================================================
# VALIDATE INPUT
# ============================================================

def validate_data():
    all_series = {
        **RIDE_WAITS,
        **HOUSE_WAITS,
        **{
            f"Quick Queue: {name}": values
            for name, values in HOUSE_QUICK_QUEUE_WAITS.items()
        },
    }

    errors = []

    for name, values in all_series.items():
        if len(values) != NUM_INTERVALS:
            errors.append(
                f"{name}: expected {NUM_INTERVALS} values, "
                f"received {len(values)}"
            )
            continue

        for i, value in enumerate(values):
            if not isinstance(value, int):
                errors.append(
                    f"{name}: index {i} must be an integer"
                )
            elif value < 0 and value != -1:
                errors.append(
                    f"{name}: invalid wait time {value} at index {i}"
                )

    if errors:
        raise ValueError(
            "Please populate/fix the wait-time arrays:\n- "
            + "\n- ".join(errors)
        )


# ============================================================
# TIME UTILITIES
# ============================================================

def format_time(minutes):
    """Convert minutes since 5:30 PM into a readable clock time."""
    base = datetime(2000, 1, 1, 17, 30)
    result = base + timedelta(minutes=minutes)
    return result.strftime("%I:%M %p").lstrip("0")


def get_wait(attraction, time, use_quick_queue=False):
    """
    Get the expected wait at the 30-minute interval containing
    the attraction's START time.

    A wait longer than 30 minutes advances the clock naturally.
    The next attraction uses the interval corresponding to its
    newly calculated start time.
    """
    if time < 0:
        return None

    index = time // INTERVAL

    if index >= NUM_INTERVALS:
        return None

    if attraction in RIDES:
        if use_quick_queue:
            return None
        wait = RIDE_WAITS[attraction][index]

    elif attraction in HOUSES:
        if time < HOUSES_OPEN:
            return None

        if use_quick_queue:
            wait = HOUSE_QUICK_QUEUE_WAITS[attraction][index]
        else:
            wait = HOUSE_WAITS[attraction][index]

    else:
        return None

    # -1 means unavailable, not zero waiting.
    return wait if wait >= 0 else None


# ============================================================
# OPTIMIZER
#
# Phase 0: Rides before houses open
# Phase 1: All houses
# Phase 2: Remaining rides
#
# Each attraction is visited exactly once.
# Quick Queue can be used at most once.
# ============================================================

PRE_HOUSES = 0
HOUSES_PHASE = 1
POST_HOUSES = 2

FULL_RIDE_MASK = (1 << len(RIDES)) - 1
FULL_HOUSE_MASK = (1 << len(HOUSES)) - 1

RIDE_INDEX = {name: i for i, name in enumerate(RIDES)}
HOUSE_INDEX = {name: i for i, name in enumerate(HOUSES)}


def optimize(force_iron_gwazi_first=False):

    @lru_cache(maxsize=None)
    def best(phase, ride_mask, house_mask, time, pass_used):
        """
        Return:
            (total_wait, itinerary)
        or:
            None if no feasible completion exists.

        Each itinerary entry is:
            (attraction, start_time, queue_wait, used_quick_queue)
        """

        # ----------------------------------------------------
        # PHASE 0: Rides before houses open
        # ----------------------------------------------------
        if phase == PRE_HOUSES:

            # Option: stop riding and move to the houses.
            # If houses are not open yet, wait until 7:00 PM.
            house_start = max(time, HOUSES_OPEN)

            result = best(
                HOUSES_PHASE,
                ride_mask,
                house_mask,
                house_start,
                pass_used,
            )

            candidates = []

            if result is not None:
                candidates.append(result)

            # Rides may only START before houses open.
            if time < HOUSES_OPEN:
                for ride in RIDES:
                    bit = 1 << RIDE_INDEX[ride]

                    if ride_mask & bit:
                        continue

                    wait = get_wait(ride, time)

                    if wait is None:
                        continue

                    next_time = time + wait + BUFFER

                    if next_time > DEADLINE:
                        continue

                    result = best(
                        PRE_HOUSES,
                        ride_mask | bit,
                        house_mask,
                        next_time,
                        pass_used,
                    )

                    if result is not None:
                        total, itinerary = result

                        candidates.append((
                            wait + total,
                            ((ride, time, wait, False),) + itinerary,
                        ))

            return min(candidates, key=lambda x: x[0]) \
                if candidates else None

        # ----------------------------------------------------
        # PHASE 1: Complete all houses before remaining rides
        # ----------------------------------------------------
        if phase == HOUSES_PHASE:

            # All houses are complete: proceed to remaining rides.
            if house_mask == FULL_HOUSE_MASK:
                return best(
                    POST_HOUSES,
                    ride_mask,
                    house_mask,
                    time,
                    pass_used,
                )

            candidates = []

            for house in HOUSES:
                bit = 1 << HOUSE_INDEX[house]

                if house_mask & bit:
                    continue

                # Option 1: regular queue
                options = [(False, pass_used)]

                # Option 2: use Quick Queue on this house
                if not pass_used:
                    options.append((True, True))

                for use_pass, next_pass_used in options:
                    wait = get_wait(
                        house,
                        time,
                        use_quick_queue=use_pass,
                    )

                    if wait is None:
                        continue

                    next_time = time + wait + BUFFER

                    if next_time > DEADLINE:
                        continue

                    result = best(
                        HOUSES_PHASE,
                        ride_mask,
                        house_mask | bit,
                        next_time,
                        next_pass_used,
                    )

                    if result is not None:
                        total, itinerary = result

                        candidates.append((
                            wait + total,
                            ((house, time, wait, use_pass),)
                            + itinerary,
                        ))

            return min(candidates, key=lambda x: x[0]) \
                if candidates else None

        # ----------------------------------------------------
        # PHASE 2: Remaining rides, after all houses
        # ----------------------------------------------------
        if phase == POST_HOUSES:

            if ride_mask == FULL_RIDE_MASK:
                return (0, ())

            candidates = []

            for ride in RIDES:
                bit = 1 << RIDE_INDEX[ride]

                if ride_mask & bit:
                    continue

                wait = get_wait(ride, time)

                if wait is None:
                    continue

                next_time = time + wait + BUFFER

                if next_time > DEADLINE:
                    continue

                result = best(
                    POST_HOUSES,
                    ride_mask | bit,
                    house_mask,
                    next_time,
                    pass_used,
                )

                if result is not None:
                    total, itinerary = result

                    candidates.append((
                        wait + total,
                        ((ride, time, wait, False),) + itinerary,
                    ))

            return min(candidates, key=lambda x: x[0]) \
                if candidates else None

        return None

    # --------------------------------------------------------
    # GLOBAL OPTIMUM
    # --------------------------------------------------------
    if not force_iron_gwazi_first:
        return best(
            PRE_HOUSES,
            0,
            0,
            START_TIME,
            False,
        )

    # --------------------------------------------------------
    # IRON GWAZI FIRST: forced start at 5:30 PM
    # --------------------------------------------------------
    iron_wait = get_wait("Iron Gwazi", START_TIME)

    if iron_wait is None:
        return None

    next_time = START_TIME + iron_wait + BUFFER

    if next_time > DEADLINE:
        return None

    iron_bit = 1 << RIDE_INDEX["Iron Gwazi"]

    result = best(
        PRE_HOUSES,
        iron_bit,
        0,
        next_time,
        False,
    )

    if result is None:
        return None

    total, itinerary = result

    return (
        iron_wait + total,
        (("Iron Gwazi", START_TIME, iron_wait, False),)
        + itinerary,
    )


# ============================================================
# REPORTING
# ============================================================

def print_itinerary(title, result):
    print(f"\n{'=' * 60}")
    print(title)
    print("=" * 60)

    if result is None:
        print("No feasible itinerary satisfies all constraints.")
        return

    total_wait, itinerary = result

    for i, (name, start, wait, used_pass) in enumerate(
        itinerary, start=1
    ):
        suffix = " [QUICK QUEUE]" if used_pass else ""

        print(
            f"Attraction {i}: {format_time(start)} - {name} "
            f"(wait: {wait} min){suffix}"
        )

    if itinerary:
        last_name, last_start, last_wait, _ = itinerary[-1]
        finish_time = last_start + last_wait + BUFFER
    else:
        finish_time = START_TIME

    print(f"\nTotal queue waiting: {total_wait} minutes")
    print(f"Final completion time: {format_time(finish_time)}")
    print(f"Attractions completed: {len(itinerary)} / 11")


def main():
    validate_data()

    global_optimum = optimize(force_iron_gwazi_first=False)
    iron_first = optimize(force_iron_gwazi_first=True)

    print_itinerary("GLOBAL OPTIMUM", global_optimum)
    print_itinerary("IRON G WAZI FIRST", iron_first)

    print(f"\n{'=' * 60}")
    print("IRON G WAZI FIRST PENALTY")
    print("=" * 60)

    if global_optimum is None or iron_first is None:
        print("Penalty unavailable: at least one itinerary is infeasible.")
    else:
        penalty = iron_first[0] - global_optimum[0]

        print(f"Global optimum wait: {global_optimum[0]} minutes")
        print(f"Iron Gwazi first wait: {iron_first[0]} minutes")
        print(f"Additional queue waiting: {penalty} minutes")

        if penalty > 0:
            print(
                f"Starting with Iron Gwazi costs {penalty} "
                "additional minutes of queue waiting."
            )
        elif penalty < 0:
            print(
                "ERROR: The constrained result beats the global "
                "optimum; check the implementation."
            )
        else:
            print(
                "Starting with Iron Gwazi has no queue-wait penalty."
            )


if __name__ == "__main__":
    main()
