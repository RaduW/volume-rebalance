import numpy as np
from transaction_adjustment_model import adjust_sample_rate_full, adjust_sample_rate_full_v2, adjust_sample_rate_v2

counts = np.array([2, 10, 10, 20, 50, 50, 100])

rate = 0.2
intensity = 1.0
print(f"counts:{counts}, rate={rate}, intensity={intensity}")

total = counts.sum()
num_classes = len(counts)

sampled = counts * rate
print(f"sampled original: {sampled}")

ideal = counts.mean() * rate
print(f"ideal:{ideal}")

correction = (ideal - counts * rate) * intensity
print(f"correction:{correction}")

corrected_sample = sampled + correction
print(f"corrected sample:{corrected_sample}")

corrected_rates = corrected_sample / counts
print(f"corrected rates: {corrected_rates}")

final_counts = corrected_rates * counts
# check that we get the corrected sample in practice
print(f"final counts: {final_counts}")

# algorithm calculation
algo_rates = (1 - intensity) * rate + ideal * intensity / counts
print(f"algo_rates: {algo_rates}")

# adjusted counts
adjusted_counts = counts * algo_rates
print(f"final adjusted counts:{adjusted_counts}")

total_sampled = adjusted_counts.sum()
print(f"total adjusted sample: {total_sampled} expected_sampled:{counts.sum() * rate}")

# now check the algorithm
counts_dict = [(f"{idx}-{count}", count) for idx, count in enumerate(counts)]

sample_rates, used = adjust_sample_rate_full_v2(counts_dict, rate, intensity, None)
print(f"sample_rates:{sample_rates}, used:{used}")

# check pushing from the top
top = counts[-2:].tolist()
bottom = counts[:2].tolist()
both = bottom + top
# both = counts
explicit = [(f"{idx}-{count}", count) for idx, count in enumerate(both)]
explicit, implicit = adjust_sample_rate_v2(explicit, rate, total_num_classes=num_classes, total=total,
                                           intensity=intensity)

print(f"implicit={implicit}\n explicit={explicit}")

# implicit=0.22857142857142856
# explicit={'3': 0.08, '2': 0.16, '1': 0.8, '0': 0.8}
