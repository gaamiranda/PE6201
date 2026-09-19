# D6 Supplement · DeepSeek vs Mistral Sensitivity

**Purpose:** compare `deepseek/deepseek-chat` against `mistralai/mistral-medium-3` using the same D6 three-layer cost model.

Machine-readable output: [`../results/d6_deepseek_mistral_sensitivity.json`](../results/d6_deepseek_mistral_sensitivity.json).

## Inputs

| Quantity | DeepSeek | Mistral |
|---|---:|---:|
| Model | `deepseek/deepseek-chat` | `mistralai/mistral-medium-3` |
| Measured pass rate | 50/76 = 65.79% | 53/76 = 69.74% |
| Layer 1 variable cost/run | US$0.0028 | US$0.0062 |
| Layer 2 fallback/run | US$2.6000 | US$2.3000 |
| Cost per successful claim | US$2.6028 | US$2.3062 |
| Monthly total, 8,000 claims + US$500 layer 3 | US$21,322.69 | US$18,949.50 |

Shared assumptions: volume is 8,000 claims/month, failure cost is US$7.60, fixed monthly layer 3 is US$500, and retrieval/tool fees are US$0.

## Sensitivity Table

| Model | Success point | Cost per successful claim | Monthly total |
|---|---:|---:|---:|
| DeepSeek, P - 10pp | 55.79% | US$3.3628 | US$27,402.69 |
| DeepSeek, measured P | 65.79% | US$2.6028 | US$21,322.69 |
| DeepSeek, P + 10pp | 75.79% | US$1.8428 | US$15,242.69 |
| Mistral, P - 10pp | 59.74% | US$3.0662 | US$25,029.50 |
| Mistral, measured P | 69.74% | US$2.3062 | US$18,949.50 |
| Mistral, P + 10pp | 79.74% | US$1.5462 | US$12,869.50 |

## Break-even

Use Mistral's cost per successful claim as the target:

```text
p_deepseek = 1 - (mistral_cost_per_successful_claim - deepseek_layer_1_variable_cost) / failure_cost
           = 1 - (2.3061880632 - 0.0028363442) / 7.60
           = 69.69%
```

DeepSeek measures **65.79%**, so it is **3.90 percentage points below** break-even. On a 76-trial schedule, the exact threshold is **52.966/76**, so DeepSeek would need **53/76 passes**. Since it currently has **50/76**, it needs **3 more successful trials** on the same schedule to clear the break-even point.

## Conclusion

At the measured rates, DeepSeek is not cheaper than Mistral despite its lower token cost. Its lower success rate creates more expected fallback cost than the token price saves. The model would need about **69.69% success**, effectively **53/76**, for its cost to match Mistral.
