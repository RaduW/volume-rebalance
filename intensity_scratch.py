import numpy as np
from transaction_adjustment_model import adjust_sample_rate_full, get_ideal_rates

counts = np.array([10, 10, 100])
rate = 0.2
intensity = 0.5
print(f"counts:{counts}, rate={rate}, intensity={intensity}")

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
counts_dict = [(f"{idx}", count) for idx,count in enumerate(counts)]

sample_rates, used = get_ideal_rates(counts_dict, rate, intensity, None)
print(f"sample_rates:{sample_rates}, used:{used}")
