from collections import deque
import csv
import html

# PRACTICAL WORK 5: CPU SCHEDULING
# Lower priority number means higher priority.

SET1 = [
    {"pid": "P1", "arrival": 0, "burst": 8, "priority": 2},
    {"pid": "P2", "arrival": 1, "burst": 4, "priority": 1},
    {"pid": "P3", "arrival": 2, "burst": 9, "priority": 3},
    {"pid": "P4", "arrival": 3, "burst": 5, "priority": 2},
]

SET2 = [
    {"pid": "P1", "arrival": 0, "burst": 8, "priority": 3},
    {"pid": "P2", "arrival": 1, "burst": 4, "priority": 1},
    {"pid": "P3", "arrival": 2, "burst": 9, "priority": 4},
    {"pid": "P4", "arrival": 3, "burst": 5, "priority": 2},
]


def simulate(processes, algorithm, **params):
    """Return CPU intervals: (start, end, PID). Idle CPU is marked IDLE."""
    ps = [dict(p) for p in processes]
    if not ps:
        return []

    for p in ps:
        if p["arrival"] < 0 or p["burst"] <= 0:
            raise ValueError("Arrival must be >= 0 and burst must be > 0")
        p["remaining"] = p["burst"]
        p["first"] = None
        p["finish"] = None
        p["used"] = 0

    alg = algorithm.upper()
    if alg not in {"FCFS", "SJF", "SRTF", "PRIORITY", "RR"}:
        raise ValueError("Unknown algorithm")

    quantum = int(params.get("quantum", 2))
    aging = int(params.get("aging", 3))
    if alg == "RR" and quantum <= 0:
        raise ValueError("Quantum must be positive")
    if aging <= 0:
        raise ValueError("Aging interval must be positive")

    by_pid = {p["pid"]: p for p in ps}
    ready = []
    queued = set()
    completed = 0
    time = 0
    current = None
    slice_used = 0
    intervals = []
    sequence = 0

    def add_interval(t, pid):
        if intervals and intervals[-1][2] == pid and intervals[-1][1] == t:
            a, _, old = intervals[-1]
            intervals[-1] = (a, t + 1, old)
        else:
            intervals.append((t, t + 1, pid))

    while completed < len(ps):
        # Add new arrivals before choosing a process.
        for p in sorted(ps, key=lambda x: (x["arrival"], x["pid"])):
            if p["arrival"] == time and p["pid"] not in queued:
                ready.append((sequence, p["pid"], time))
                sequence += 1
                queued.add(p["pid"])

        # Remove processes that have already finished.
        ready = [item for item in ready
                 if by_pid[item[1]]["remaining"] > 0]

        if alg == "FCFS":
            if current is None and ready:
                ready.sort(key=lambda x: (by_pid[x[1]]["arrival"], x[0]))
                _, pid, _ = ready.pop(0)
                queued.discard(pid)
                current = pid

        elif alg == "SJF":
            if current is None and ready:
                ready.sort(key=lambda x: (
                    by_pid[x[1]]["burst"],
                    by_pid[x[1]]["arrival"], x[0]))
                _, pid, _ = ready.pop(0)
                queued.discard(pid)
                current = pid

        elif alg == "SRTF":
            candidates = ready[:]
            if current is not None:
                candidates.append((-1, current, time))
            if candidates:
                candidates.sort(key=lambda x: (
                    by_pid[x[1]]["remaining"],
                    by_pid[x[1]]["arrival"], x[0]))
                chosen = candidates[0][1]
                if chosen != current:
                    if current is not None:
                        ready.append((-1, current, time))
                        queued.add(current)
                    if chosen in queued:
                        ready = [x for x in ready if x[1] != chosen]
                        queued.discard(chosen)
                    current = chosen

        elif alg == "PRIORITY":
            candidates = ready[:]
            if current is not None:
                candidates.append((-1, current, time))
            if candidates:
                def priority_key(item):
                    p = by_pid[item[1]]
                    waited = time - p["arrival"] - p["used"]
                    effective = p["priority"] - max(0, waited) // aging
                    return (effective, p["arrival"], item[0])
                candidates.sort(key=priority_key)
                chosen = candidates[0][1]
                if chosen != current:
                    if current is not None:
                        ready.append((-1, current, time))
                        queued.add(current)
                    if chosen in queued:
                        ready = [x for x in ready if x[1] != chosen]
                        queued.discard(chosen)
                    current = chosen

        elif alg == "RR":
            if current is None and ready:
                ready.sort(key=lambda x: (x[2], x[0]))
                _, current, _ = ready.pop(0)
                queued.discard(current)
                slice_used = 0

        if current is None:
            add_interval(time, "IDLE")
            time += 1
            continue

        p = by_pid[current]
        if p["first"] is None:
            p["first"] = time

        add_interval(time, current)
        p["remaining"] -= 1
        p["used"] += 1
        time += 1

        if p["remaining"] == 0:
            p["finish"] = time
            completed += 1
            current = None
            slice_used = 0
        elif alg == "RR":
            slice_used += 1
            if slice_used >= quantum:
                # Arrivals at this instant enter the queue before requeueing.
                for newp in sorted(ps, key=lambda x: (x["arrival"], x["pid"])):
                    if newp["arrival"] == time and newp["remaining"] > 0 \
                            and newp["pid"] not in queued \
                            and newp["pid"] != current:
                        ready.append((sequence, newp["pid"], time))
                        sequence += 1
                        queued.add(newp["pid"])
                ready.append((sequence, current, time))
                sequence += 1
                queued.add(current)
                current = None
                slice_used = 0

    return intervals


def metrics(processes, intervals):
    results = []
    for p in processes:
        runs = [x for x in intervals if x[2] == p["pid"]]
        finish = max(x[1] for x in runs)
        first = min(x[0] for x in runs)
        turnaround = finish - p["arrival"]
        waiting = turnaround - p["burst"]
        response = first - p["arrival"]
        results.append({
            "PID": p["pid"],
            "Waiting": waiting,
            "Turnaround": turnaround,
            "Response": response,
        })

    makespan = max(x[1] for x in intervals) - min(x[0] for x in intervals)
    busy = sum(x[1] - x[0] for x in intervals if x[2] != "IDLE")
    switches = sum(
        1 for i in range(1, len(intervals))
        if intervals[i][2] != intervals[i - 1][2]
    )
    avg = {
        key: sum(r[key] for r in results) / len(results)
        for key in ("Waiting", "Turnaround", "Response")
    }
    avg["CPU utilization"] = 100 * busy / makespan if makespan else 0
    avg["Switches"] = switches
    return results, avg


def print_gantt(intervals):
    print("Gantt chart:")
    print(" | ".join(f"{pid}[{start}-{end}]"
                     for start, end, pid in intervals))


def run_table(processes, label):
    print("\n" + "=" * 65)
    print(label)
    print("=" * 65)
    rows = []
    for alg in ("FCFS", "SJF", "SRTF", "PRIORITY", "RR"):
        kw = {"quantum": 3} if alg == "RR" else {}
        intervals = simulate(processes, alg, **kw)
        _, m = metrics(processes, intervals)
        rows.append((alg, m))
        print(f"{alg:10} | Wait {m['Waiting']:.2f} | "
              f"Turnaround {m['Turnaround']:.2f} | "
              f"Response {m['Response']:.2f} | "
              f"CPU {m['CPU utilization']:.1f}% | "
              f"Switches {m['Switches']}")
        print_gantt(intervals)
    return rows


def rr_graph(processes):
    points = []
    print("\nRR: quantum 1..10")
    print("Quantum | Average waiting | Context switches")
    for q in range(1, 11):
        ints = simulate(processes, "RR", quantum=q)
        _, m = metrics(processes, ints)
        points.append((q, m["Waiting"], m["Switches"]))
        print(f"{q:7} | {m['Waiting']:16.2f} | {m['Switches']:16}")
    # Make a graph file using Python's standard library (no matplotlib needed).
    w, h = 760, 400
    left, right, top, bottom = 70, 720, 45, 340
    max_wait = max(x[1] for x in points) or 1
    max_sw = max(x[2] for x in points) or 1
    def px(q):
        return left + (q - 1) * (right - left) / 9
    def py(v, vmax):
        return bottom - v * (bottom - top) / vmax
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="380" y="24" text-anchor="middle" font-size="18">RR: Quantum vs Waiting and Switches</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="black"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="black"/>',
        f'<text x="380" y="385" text-anchor="middle">Quantum (1-10)</text>',
        f'<text x="15" y="190" transform="rotate(-90 15 190)" text-anchor="middle">Scaled value</text>',
    ]
    for q, wait, sw in points:
        svg.append(f'<text x="{px(q)}" y="{bottom+18}" text-anchor="middle" font-size="11">{q}</text>')
    for vals, vmax, color in [(1, max_wait, "blue"), (2, max_sw, "red")]:
        coords = []
        for q, wait, sw in points:
            v = wait if vals == 1 else sw
            coords.append(f"{px(q):.1f},{py(v, vmax):.1f}")
        svg.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for q, wait, sw in points:
            v = wait if vals == 1 else sw
            svg.append(f'<circle cx="{px(q):.1f}" cy="{py(v, vmax):.1f}" r="3" fill="{color}"/>')
    svg += [
        '<text x="530" y="55" fill="blue">Blue: average waiting</text>',
        '<text x="530" y="73" fill="red">Red: context switches</text>',
        '</svg>',
    ]
    with open("rr_graph.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print("Graph saved as rr_graph.svg")


def aging_demo():
    # A low-priority job waits while higher-priority jobs arrive.
    processes = [
        {"pid": "LOW", "arrival": 0, "burst": 5, "priority": 8},
        {"pid": "H1", "arrival": 0, "burst": 3, "priority": 0},
        {"pid": "H2", "arrival": 1, "burst": 3, "priority": 0},
        {"pid": "H3", "arrival": 2, "burst": 3, "priority": 0},
        {"pid": "H4", "arrival": 3, "burst": 3, "priority": 0},
        {"pid": "H5", "arrival": 4, "burst": 3, "priority": 0},
    ]
    print("\nPriority scheduling WITHOUT aging:")
    # Base priority, preemptive, no aging (very large aging interval).
    a = simulate(processes, "PRIORITY", aging=100000)
    print_gantt(a)
    print("\nPriority scheduling WITH aging (interval=2):")
    b = simulate(processes, "PRIORITY", aging=2)
    print_gantt(b)
    print("Aging gradually improves the waiting process's effective priority.")


def main():
    run_table(SET1, "SET1: algorithm comparison (example data)")
    run_table(SET2, "SET2: algorithm comparison (example data)")
    rr_graph(SET2)
    aging_demo()

    print("\nSRTF and RR(q=3) comparison on SET1:")
    for alg, kw in [("SRTF", {}), ("RR", {"quantum": 3})]:
        ints = simulate(SET1, alg, **kw)
        print(alg, end=": ")
        print_gantt(ints)

    print("\nIMPORTANT:")
    print("SET1 and SET2 currently use example data because the official")
    print("sets/reference output were not supplied. Replace SET1/SET2 with")
    print("the exact assignment data before submitting.")

    with open("set1_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Algorithm", "Start", "End", "PID"])
        for alg in ("FCFS", "SJF", "SRTF", "PRIORITY", "RR"):
            kw = {"quantum": 3} if alg == "RR" else {}
            for start, end, pid in simulate(SET1, alg, **kw):
                writer.writerow([alg, start, end, pid])
    print("\nSaved: set1_results.csv and rr_graph.svg")


if __name__ == "__main__":
    main()
