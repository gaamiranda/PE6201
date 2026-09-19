# Section 4 Cost to Serve

## 1. Baseline Assumptions

Using the Class 5 three-layer model, our baseline is layer 1 token cost plus layer 2 expected fallback cost, multiplied by 8,000 claims per month, plus a US$500 per month fixed layer 3 deployment assumption. Retrieval and tool fees are zero because the repository records no separate provider charge. We ship the model with a 12-turn step cap, a 22-call cap, a US$0.016 per run budget ceiling, and a US$1,000 per user per month deployment assumption. Prompt caching and reasoning-token adjustments were not used or measured.

## 2. Three-Layer Cost Model

From the D5 results, under the three-layer cost model, google/gemini-2.5-flash-lite is the best model for our product. Its layer 1 cost is the second lowest rather than the lowest, but it has the highest measured success rate. After layer 1 and layer 2 are both counted, its cost per successful task is therefore the lowest, at US$1.8014.

The models ranked second and third by success rate also show the same lesson from class. mistralai/mistral-medium-3 has a layer 1 cost that is about two times higher than deepseek/deepseek-chat, but its final cost is still lower. This shows that token price alone is not the decision variable. When failure has to be handled by a human claims assessor, success rate drives the expected fallback cost.

## 3. Sensitivity Analysis and Break-Even Point

Across a plus or minus 10 percentage point range, the measured decision is clear but not fully robust. A weak Gemini point at 66.32% and US$2.5614 per successful task is more expensive than measured Mistral at US$2.3062.

The break-even point can be discussed with two models that are close in performance. For mistralai/mistral and deepseek, the sensitivity analysis shows that DeepSeek is currently 50/76 = 65.79%, while Mistral is 53/76 = 69.74%. DeepSeek would need to reach about 69.69% success to match the cost of mistralai/mistral. An improvement of 3.90 percentage points can make a change, which gives us solid business insights.

## 4. The Four Levers

Because we used scripted replay for testing, we assumed we had tuned it well and that the success rate did not decrease (remained unchanged). From this, we can see that:

Lever 1 :  Removing two rejected tool descriptors reduces input tokens by 96,288 and projected cost by US$0.009640 on the 76-trial replay. This shows that a thinner tool block lowers cost linearly because the tool manual is re-sent on each model call.

Lever 2 :  With dependency-rule grouping, tool-executing turns fall from 222 to 183, and input tokens fall from 413,519 to 353,484. This shows that parallelising tool calls works.

Lever 3 : The measured result supports the Class 5 idea that a fat observation or manual compounds through later ReAct context. A descriptor increase of about 275 tokens becomes +131,216 input tokens across the 76-trial schedule. At the same time, the shipped return shape reduces interface risk: the old shape could return a contradictory observation, while the new shape makes that contradiction unrepresentable.

Lever 4 : This is the lever that dominates the bill. Using mistralai/mistral-medium-3 as an example, reducing token cost by 5% changes total cost only slightly, while improving success rate by 5 percentage points reduces fallback cost by about US$3,040 per month, roughly one sixth of the model’s monthly total.
