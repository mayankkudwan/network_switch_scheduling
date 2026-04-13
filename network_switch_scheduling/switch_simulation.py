"""
Network Switch Scheduling Simulation
3x3 Crossbar Switch: Inputs I0,I1,I2 | Outputs O0,O1,O2
"""

from collections import deque
from itertools import permutations
import matplotlib

import matplotlib.pyplot as plt

# Input Trace
# ─────────────────────────────────────────────
packets = [
    ("p1",  0, 0, 0),
    ("p2",  0, 0, 1),
    ("p3",  0, 1, 0),
    ("p4",  0, 1, 2),
    ("p5",  0, 2, 0),
    ("p6",  1, 0, 2),
    ("p7",  1, 2, 1),
    ("p8",  2, 1, 1),
    ("p9",  2, 2, 2),
    ("p10", 3, 0, 1),
    ("p11", 3, 1, 0),
    ("p12", 3, 2, 1),
    ("p13", 4, 0, 0),
    ("p14", 4, 1, 2),
    ("p15", 4, 2, 2),
    ("p16", 5, 0, 2),
    ("p17", 5, 1, 1),
    ("p18", 5, 2, 0),
]

# Build arrival map: time -> list of (name, src, dst)
from collections import defaultdict
arrivals = defaultdict(list)
for name, t, src, dst in packets:
    arrivals[t].append((name, src, dst))


# PART 1: FIFO with HoL Blocking
# ─────────────────────────────────────────────
def simulate_fifo():
    print("=" * 60)
    print("PART 1: FIFO Queue with HoL Blocking")
    print("=" * 60)

    # Each input has one FIFO queue
    queues = {0: deque(), 1: deque(), 2: deque()}
    t = 0
    backlog_over_time = []

    def total_packets():
        return sum(len(q) for q in queues.values())

    while True:
        # Arrive at beginning of slot
        for name, src, dst in arrivals.get(t, []):
            queues[src].append((name, dst))

        total = total_packets()
        if total == 0 and t > 0 and not arrivals.get(t, []):
            break

        print(f"\n--- t={t} | Backlog(start)={total} ---")

        # Find which outputs are contested
        # Only HEAD of each queue is eligible
        # Tie-break: lowest input port wins
        output_served = {}   # output -> input that wins
        output_winner_pkt = {}

        # Collect heads
        heads = {}  # input -> (name, dst)
        for inp in range(3):
            if queues[inp]:
                heads[inp] = queues[inp][0]

        # Assign outputs: for each output, find lowest-numbered contending input
        for inp in sorted(heads.keys()):
            name, dst = heads[inp]
            if dst not in output_served:
                output_served[dst] = inp
                output_winner_pkt[dst] = name

        # Send winning packets
        sent = set()
        for dst, inp in output_served.items():
            name, _ = queues[inp][0]
            queues[inp].popleft()
            sent.add((inp, dst, name))
            print(f"  SEND: {name} | I{inp} -> O{dst}")

        # Record END-of-slot backlog (after sending)
        backlog_over_time.append((t, total_packets()))

        # HoL blocking detection
        for inp in range(3):
            if queues[inp]:
                name, dst = queues[inp][0]
                if dst in output_served and output_served[dst] != inp:
                    print(f"  [HoL BLOCKED] {name} at I{inp} wants O{dst} but lost to I{output_served[dst]}")
                # Check if head is blocked and output is actually idle (served by nobody)
                # Real HoL: head blocked and behind it a packet that could use idle output
                # Check all positions in queue
                served_outputs = set(output_served.keys())
                for pos, (pname, pdst) in enumerate(list(queues[inp])):
                    if pos == 0 and pdst in served_outputs:
                        # head is being served or blocked
                        pass
                    elif pos > 0 and pdst not in served_outputs:
                        # This packet behind head could use an idle output but is stuck
                        head_name, head_dst = queues[inp][0]
                        if head_dst in served_outputs and output_served[head_dst] != inp:
                            print(f"  [HoL BLOCKING] {pname} (I{inp}, wants O{pdst} [IDLE]) blocked behind {head_name}")
                        break

        t += 1
        if t > 100:
            break

    # last slot check
    for name, src, dst in arrivals.get(t, []):
        queues[src].append((name, dst))
    total = total_packets()
    service_time = t

    print(f"\n✅ FIFO Total Service Time: {t} time slots")
    backlog_over_time.append((t, 0))
    return t, backlog_over_time



# PART 2: VOQ - Optimal (Exhaustive Search)
# ─────────────────────────────────────────────
def simulate_voq_optimal():
    print("\n" + "=" * 60)
    print("PART 2: VOQ - Optimal Exhaustive Search")
    print("=" * 60)

    # VOQ: voq[src][dst] = deque of packets
    def make_voq():
        return {i: {j: deque() for j in range(3)} for i in range(3)}

    # All valid matchings (permutations of outputs assigned to inputs)
    # A matching is a dict: input -> output (bijection, so permutation)
    def get_valid_matchings(voq):
        """Return list of valid matchings. Each matching = list of (inp, dst) pairs."""
        valid = []
        # Try all permutations of outputs assigned to inputs
        for perm in permutations(range(3)):
            # perm[i] = output assigned to input i
            matching = []
            for inp, dst in enumerate(perm):
                if voq[inp][dst]:  # there's a packet to send
                    matching.append((inp, dst))
            if matching:
                valid.append(matching)
        # Also include partial matchings? No - we want maximum matchings
        # But we should consider all subsets for true optimality
        # For a 3x3 switch, enumerate all valid matchings (sets of non-conflicting pairs)
        return valid

    def all_valid_matchings(voq):
        """All valid matchings including partial ones."""
        pairs = []
        for inp in range(3):
            for dst in range(3):
                if voq[inp][dst]:
                    pairs.append((inp, dst))

        # Generate all valid subsets (no shared input, no shared output)
        result = [[]]  # include empty matching
        for pair in pairs:
            new_subsets = []
            for subset in result:
                inp_used = {p[0] for p in subset}
                dst_used = {p[1] for p in subset}
                if pair[0] not in inp_used and pair[1] not in dst_used:
                    new_subsets.append(subset + [pair])
            result.extend(new_subsets)
        return [m for m in result if m]  # exclude empty

    def count_voq(voq):
        return sum(len(voq[i][j]) for i in range(3) for j in range(3))

    def apply_matching(voq, matching):
        new_voq = {i: {j: deque(voq[i][j]) for j in range(3)} for i in range(3)}
        for inp, dst in matching:
            if new_voq[inp][dst]:
                new_voq[inp][dst].popleft()
        return new_voq

    def add_arrivals(voq, t):
        for name, src, dst in arrivals.get(t, []):
            voq[src][dst].append((name, src, dst))

    # Greedy lookahead: try to find sequence that finishes earliest
    # Use BFS/greedy: at each time step pick matching that maximizes throughput
    # For true optimal, we do a simulation with greedy-max matching each slot

    voq = make_voq()
    t = 0
    backlog_over_time = []
    all_matchings_log = []

    while True:
        add_arrivals(voq, t)
        total = count_voq(voq)

        if total == 0 and not arrivals.get(t, []):
            break


        # Find maximum matching (most packets sent)
        matchings = all_valid_matchings(voq)
        if not matchings:
            print(f"  t={t}: No packets to send")
            t += 1
            continue

        best = max(matchings, key=lambda m: len(m))
        # Among ties, pick lexicographically smallest for determinism
        all_best = [m for m in matchings if len(m) == len(best)]
        best = sorted(all_best, key=lambda m: sorted(m))[0]

        print(f"\n--- t={t} | Backlog={total} ---")
        for inp, dst in best:
            pkt = voq[inp][dst][0]
            print(f"  SEND: {pkt[0]} | I{inp} -> O{dst}")

        voq = apply_matching(voq, best)
        all_matchings_log.append((t, best))
        backlog_over_time.append((t, count_voq(voq)))
        t += 1

        if t > 100:
            break

    backlog_over_time.append((t, 0))
    print(f"\n✅ VOQ-Optimal Total Service Time: {t} time slots")
    return t, backlog_over_time


# ─────────────────────────────────────────────
# PART 3: VOQ with iSLIP (3 iterations)
# ─────────────────────────────────────────────
def simulate_islip(num_iterations=3):
    print("\n" + "=" * 60)
    print(f"PART 3: VOQ with iSLIP ({num_iterations} iterations)")
    print("=" * 60)

    def make_voq():
        return {i: {j: deque() for j in range(3)} for i in range(3)}

    def count_voq(voq):
        return sum(len(voq[i][j]) for i in range(3) for j in range(3))

    def add_arrivals(voq, t):
        for name, src, dst in arrivals.get(t, []):
            voq[src][dst].append((name, src, dst))

    voq = make_voq()
    # Round-robin pointers: grant_ptr[dst] = next input to grant from
    #                        accept_ptr[inp] = next output to accept from
    grant_ptr = [0, 0, 0]   # one per output
    accept_ptr = [0, 0, 0]  # one per input

    t = 0
    backlog_over_time = []

    while True:
        add_arrivals(voq, t)
        total = count_voq(voq)

        if total == 0 and not arrivals.get(t, []):
            break

        print(f"\n--- t={t} | Backlog(start)={total} ---")
        print(f"  grant_ptr={grant_ptr}, accept_ptr={accept_ptr}")

        final_match = {}  # inp -> dst

        for iteration in range(num_iterations):
            print(f"  [Iteration {iteration+1}]")

            # REQUEST: each unmatched input requests all outputs it has packets for
            requests = {dst: [] for dst in range(3)}
            for inp in range(3):
                if inp in final_match:
                    continue  # already matched
                for dst in range(3):
                    if voq[inp][dst]:
                        requests[dst].append(inp)

            # GRANT: each unmatched output grants to one requesting input
            # starting from grant_ptr[dst], round-robin
            # grants_received[inp] = list of outputs that granted to inp
            grants_received = {inp: [] for inp in range(3)}
            for dst in range(3):
                if dst in final_match.values():
                    continue  # already matched
                reqs = requests[dst]
                if not reqs:
                    continue
                # Round-robin from grant_ptr[dst]
                ptr = grant_ptr[dst]
                chosen = None
                for offset in range(3):
                    candidate = (ptr + offset) % 3
                    if candidate in reqs:
                        chosen = candidate
                        break
                if chosen is not None:
                    grants_received[chosen].append(dst)
                    print(f"    GRANT: O{dst} -> I{chosen}")

            # ACCEPT: each unmatched input accepts ONE grant using accept_ptr
            new_matches = {}
            for inp in range(3):
                if inp in final_match:
                    continue
                g_list = grants_received[inp]
                if not g_list:
                    continue
                # Round-robin from accept_ptr[inp]: pick first granted output >= ptr
                ptr = accept_ptr[inp]
                chosen_dst = None
                for offset in range(3):
                    candidate = (ptr + offset) % 3
                    if candidate in g_list:
                        chosen_dst = candidate
                        break
                if chosen_dst is not None:
                    new_matches[inp] = chosen_dst
                    print(f"    ACCEPT: I{inp} -> O{chosen_dst}")
                    # Update pointers only on accept
                    grant_ptr[chosen_dst] = (inp + 1) % 3
                    accept_ptr[inp] = (chosen_dst + 1) % 3

            final_match.update(new_matches)

        # Send matched packets
        if final_match:
            for inp, dst in final_match.items():
                if voq[inp][dst]:
                    pkt = voq[inp][dst][0]
                    voq[inp][dst].popleft()
                    print(f"  SEND: {pkt[0]} | I{inp} -> O{dst}")
        else:
            print(f"  No packets sent this slot")

        backlog_over_time.append((t, count_voq(voq)))
        t += 1
        if t > 100:
            break

    backlog_over_time.append((t, 0))
    print(f"\n✅ iSLIP Total Service Time: {t} time slots")
    return t, backlog_over_time


# MAIN
# ─────────────────────────────────────────────
fifo_time, fifo_backlog = simulate_fifo()
voq_time,  voq_backlog  = simulate_voq_optimal()
islip_time, islip_backlog = simulate_islip(num_iterations=3)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  FIFO Total Service Time:        {fifo_time}")
print(f"  VOQ-Optimal Total Service Time: {voq_time}")
print(f"  iSLIP Total Service Time:       {islip_time}")


# PART 4: Graphs
# ─────────────────────────────────────────────
def extend_backlog(bl, end_t):
    """Extend backlog to end_t=0 if needed."""
    d = dict(bl)
    result = []
    for t in range(end_t + 1):
        result.append((t, d.get(t, 0)))
    return result

max_t = max(fifo_time, voq_time, islip_time)

fifo_bl  = extend_backlog(fifo_backlog,  max_t)
voq_bl   = extend_backlog(voq_backlog,   max_t)
islip_bl = extend_backlog(islip_backlog, max_t)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Graph 1: Bar Chart - Total Service Time
ax1 = axes[0]
algorithms = ['FIFO', 'VOQ-Optimal', 'iSLIP']
times = [fifo_time, voq_time, islip_time]
colors = ['#e74c3c', '#2ecc71', '#3498db']
bars = ax1.bar(algorithms, times, color=colors, edgecolor='black', width=0.5)
ax1.set_title('Total Service Time Comparison', fontsize=14, fontweight='bold')
ax1.set_ylabel('Time Slots to Empty Switch', fontsize=12)
ax1.set_xlabel('Scheduling Algorithm', fontsize=12)
ax1.set_ylim(0, max(times) + 3)
for bar, val in zip(bars, times):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
             str(val), ha='center', va='bottom', fontsize=13, fontweight='bold')
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Graph 2: Backlog over Time
ax2 = axes[1]
ft = [x[0] for x in fifo_bl]
fv = [x[1] for x in fifo_bl]
vt = [x[0] for x in voq_bl]
vv = [x[1] for x in voq_bl]
it = [x[0] for x in islip_bl]
iv = [x[1] for x in islip_bl]

ax2.plot(ft, fv, 'r-o', label='FIFO',        linewidth=2, markersize=7)
ax2.plot(vt, vv, 'g-s', label='VOQ-Optimal', linewidth=2, markersize=7)
ax2.plot(it, iv, 'b-^', label='iSLIP',       linewidth=2, markersize=7)
ax2.set_title('Backlog over Time', fontsize=14, fontweight='bold')
ax2.set_xlabel('Time Slot (t)', fontsize=12)
ax2.set_ylabel('Packets Remaining in Switch', fontsize=12)
ax2.legend(fontsize=11)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.set_xticks(range(max_t + 1))
ax2.set_yticks(range(0, max(fv) + 2))

plt.tight_layout()
plt.savefig('switch_graphs.png', dpi=150, bbox_inches='tight')
print("\n📊 Graphs saved to switch_graphs.png")